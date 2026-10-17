from app.config import Settings
from app.model_adapter import ModelAdapter
from app.rules import TEXT_STEPS
from app.schemas import AgentRequest, Preferences, ProposalResult


def test_live_model_receives_exact_supported_constraint_template(monkeypatch):
    seen = {}

    def fake_request(self, name, schema, payload):
        seen.update(payload)
        return ProposalResult(proposals=[], questions=["测试"])

    monkeypatch.setattr(ModelAdapter, "request", fake_request)
    model = ModelAdapter(Settings(mock_mode=False, model_api_key="test-placeholder"))
    model.proposals(
        AgentRequest(request_type="explore", text="海洋", available_minutes=5, budget=0),
        [{"star_id": "real", "title": "海洋", "match_basis": ["海洋"]}],
        Preferences(constraints=["不购买"]),
    )
    assert seen["constraint_template"]["steps"] == TEXT_STEPS
    assert seen["constraint_template"]["estimated_budget"] == 0
