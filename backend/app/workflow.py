from time import perf_counter
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .models import now
from .schemas import AgentRequest
from .tools import ToolRegistry


class AgentState(TypedDict, total=False):
    request: dict
    related_stars: list[dict]
    star_details: list[dict]
    preferences: dict
    draft: dict
    proposals: list[dict]
    questions: list[str]
    validation: list[dict]
    result: dict


class Workflow:
    def __init__(self, session, adapter, run, approved=False):
        self.session, self.run = session, run
        self.tools = ToolRegistry(session, adapter, run, approved)

    def node(self, name, handler, checkpoint=True):
        def wrapped(state):
            start = perf_counter()
            event = {"kind": "node", "name": name, "status": "running"}
            try:
                update = handler(state)
                event["status"] = "succeeded"
                self.run.state = {**self.run.state, **state, **update}
                return update
            except Exception:
                event["status"] = "failed"
                raise
            finally:
                event["elapsed_ms"] = round((perf_counter() - start) * 1000)
                self.run.events = [*self.run.events, event]
                if checkpoint:
                    self.session.commit()

        return wrapped

    def execute(self, request: AgentRequest):
        graph = StateGraph(AgentState)
        graph.add_node(
            "understand_request",
            self.node(
                "understand_request",
                lambda s: {"request": AgentRequest.model_validate(s["request"]).model_dump(mode="json")},
            ),
        )
        graph.add_node(
            "extract_star_draft",
            self.node(
                "extract_star_draft", lambda s: {"draft": self.tools.call("create_star_draft", s["request"])}
            ),
        )
        graph.add_node("retrieve_related_stars", self.node("retrieve_related_stars", self.retrieve))
        graph.add_node(
            "load_preferences",
            self.node(
                "load_preferences", lambda s: {"preferences": self.tools.call("get_user_preferences", {})}
            ),
        )
        graph.add_node("generate_suggestions", self.node("generate_suggestions", self.generate))
        graph.add_node("validate_suggestions", self.node("validate_suggestions", self.validate))
        graph.add_node("await_user_decision", self.node("await_user_decision", lambda s: {}))
        graph.add_edge(START, "understand_request")
        graph.add_conditional_edges(
            "understand_request",
            lambda s: (
                "extract_star_draft"
                if s["request"]["request_type"] == "collect"
                else "retrieve_related_stars"
            ),
        )
        graph.add_edge("extract_star_draft", "await_user_decision")
        graph.add_edge("retrieve_related_stars", "load_preferences")
        graph.add_edge("load_preferences", "generate_suggestions")
        graph.add_edge("generate_suggestions", "validate_suggestions")
        graph.add_edge("validate_suggestions", "await_user_decision")
        graph.add_edge("await_user_decision", END)
        result = graph.compile().invoke({"request": request.model_dump(mode="json")})
        self.run.status = "awaiting_decision"
        self.run.summary = (
            "结构化草稿待确认"
            if request.request_type == "collect"
            else f"{len(result.get('proposals', []))} 个已验证候选"
        )
        return result

    def retrieve(self, state):
        stars = self.tools.call("search_stars", {"query": state["request"]["text"]})
        details = [self.tools.call("get_star_details", {"star_id": star["star_id"]}) for star in stars[:3]]
        return {"related_stars": stars, "star_details": details}

    def validate(self, state):
        valid, checks = [], []
        for proposal in state["proposals"]:
            check = self.tools.call(
                "validate_quest_proposal",
                {
                    "proposal": proposal,
                    "request": state["request"],
                    "preferences": state["preferences"],
                    "allowed_ids": [s["star_id"] for s in state["related_stars"]],
                },
            )
            checks.append(check)
            if check["valid"]:
                valid.append(proposal)
        questions = state.get("questions", [])
        if not valid and state["proposals"]:
            questions = [*questions, "候选未通过约束验证，请调整约束或重试。"]
        return {"proposals": valid, "validation": checks, "questions": questions}

    def generate(self, state):
        categories = state["preferences"]["categories"]
        ranked = sorted(state["related_stars"], key=lambda s: (s["category"] not in categories, -s["score"]))
        return self.tools.call(
            "generate_quest_proposal",
            {"request": state["request"], "stars": ranked, "preferences": state["preferences"]},
        )

    def approved_operation(self, node_name: str, operation):
        # 审批写入不在节点中 commit；与审批记录在调用方同一事务提交。
        graph = StateGraph(AgentState)
        graph.add_node(node_name, self.node(node_name, lambda _: {"result": operation()}, checkpoint=False))
        graph.add_edge(START, node_name)
        graph.add_edge(node_name, END)
        return graph.compile().invoke({})["result"]


def finish_run(run, start):
    run.ended_at = now()
    run.elapsed_ms = round((perf_counter() - start) * 1000)
