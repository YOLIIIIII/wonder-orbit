from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer, model_validator
from urllib.parse import urlparse

Energy = Literal["low", "medium", "high"]
Tag = Annotated[str, Field(min_length=1, max_length=80)]
Step = Annotated[str, Field(min_length=1, max_length=1000)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StarInput(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    original_text: str = Field(min_length=1, max_length=12000)
    description: str = Field(default="", max_length=12000)
    category: str = Field(default="未分类", min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    interest_reason: str | None = Field(default=None, max_length=2000)
    source_type: Literal["manual", "paste", "link"] = "manual"
    source_reference: str | None = Field(default=None, max_length=2000)
    estimated_minutes: int | None = Field(default=None, ge=1, le=1440)
    estimated_budget: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    energy_level: Energy | None = None
    status: Literal["collected", "exploring", "archived"] = "collected"

    @field_validator("source_reference")
    @classmethod
    def valid_url(cls, value):
        if value and (urlparse(value).scheme not in {"http", "https"} or not urlparse(value).netloc):
            raise ValueError("参考链接必须是 http/https 地址")
        return value

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value):
        if any(not tag.strip() or len(tag) > 80 for tag in value):
            raise ValueError("标签不能为空或超过 80 字")
        return list(dict.fromkeys(tag.strip() for tag in value))


class DraftResult(StrictModel):
    draft: StarInput
    missing_fields: list[str]
    questions: list[str]


ExplorationDirection = Literal["knowledge", "hands_on", "creative"]


class LearningSource(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    text: str = Field(min_length=1, max_length=5000)
    label: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=2000)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("材料不能为空白")
        return value

    @field_validator("url")
    @classmethod
    def valid_url(cls, value):
        return StarInput.valid_url(value)


class LearningCard(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    evidence_quote: str = Field(min_length=1, max_length=1000)
    quote_start: int = Field(ge=0, strict=True)
    quote_end: int = Field(ge=1, strict=True)
    takeaway: str = Field(min_length=1, max_length=1000)
    interest_relevance: str = Field(min_length=1, max_length=500)
    follow_up_question: str = Field(min_length=1, max_length=500)
    uncertainties: list[Step] = Field(min_length=1, max_length=10)
    source_kind: Literal["user_supplied_unverified"] = "user_supplied_unverified"
    source_label: str | None = Field(default=None, max_length=200)
    source_url: str | None = Field(default=None, max_length=2000)


class AgentRequest(StrictModel):
    learning_source: LearningSource | None = None
    exploration_direction: ExplorationDirection | None = None
    request_type: Literal["collect", "explore"]
    text: str = Field(min_length=1, max_length=12000)
    available_minutes: int | None = Field(default=None, ge=1, le=1440)
    budget: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    energy_level: Energy | None = None
    source_type: Literal["manual", "paste", "link"] = "paste"
    source_reference: str | None = None

    @model_validator(mode="after")
    def explore_only(self):
        if self.request_type != "explore" and self.exploration_direction is not None:
            raise ValueError("探索方向仅适用于 Explore")
        if self.learning_source is not None and (
            self.request_type != "explore" or self.exploration_direction != "knowledge"
        ):
            raise ValueError("学习材料仅适用于 knowledge Explore")
        return self

    @model_serializer(mode="wrap")
    def compatible_payload(self, handler):
        # 仅省略新增的空方向，保留旧字段默认值、历史 payload 与幂等哈希语义。
        data = handler(self)
        if self.learning_source is None:
            data.pop("learning_source", None)
        if self.exploration_direction is None:
            data.pop("exploration_direction", None)
        return data

    @field_validator("source_reference")
    @classmethod
    def valid_url(cls, value):
        return StarInput.valid_url(value)


class Proposal(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=4000)
    estimated_minutes: int = Field(ge=1, le=1440)
    estimated_budget: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    energy_level: Energy
    steps: list[Step] = Field(min_length=1, max_length=10)
    based_on_star_ids: list[str] = Field(min_length=1, max_length=10)
    rationale: str = Field(min_length=1, max_length=4000)
    uncertainties: list[str] = Field(default_factory=list, max_length=20)


class ProposalResult(StrictModel):
    learning_card: LearningCard | None = None
    proposals: list[Proposal] = Field(max_length=3)
    questions: list[str] = Field(default_factory=list)


class Decision(StrictModel):
    approved: bool
    index: int = Field(default=0, ge=0, le=2)
    edited_star: StarInput | None = None
    edited_proposal: Proposal | None = None


class ReflectionInput(StrictModel):
    outcome: Literal["completed", "skipped"]
    user_feedback: str = Field(default="", max_length=8000)
    liked_aspects: list[Tag] = Field(default_factory=list, max_length=20)
    disliked_aspects: list[Tag] = Field(default_factory=list, max_length=20)


class Preferences(StrictModel):
    categories: list[Tag] = Field(default_factory=list, max_length=30)
    min_minutes: int = Field(default=1, ge=1, le=1440)
    max_minutes: int = Field(default=30, ge=1, le=1440)
    max_budget: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    energy_level: Energy | None = None
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("max_minutes")
    @classmethod
    def valid_range(cls, value, info):
        if value < info.data.get("min_minutes", 1):
            raise ValueError("最长时间不能小于最短时间")
        return value


class SearchArgs(StrictModel):
    query: str = Field(max_length=12000)
    category: str | None = None
    include_archived: bool = False


class DetailArgs(StrictModel):
    star_id: str


class EmptyArgs(StrictModel):
    pass


class ProposalArgs(StrictModel):
    request: AgentRequest
    stars: list[dict]
    preferences: Preferences


class ValidateArgs(StrictModel):
    proposal: Proposal
    request: AgentRequest
    preferences: Preferences
    allowed_ids: list[str]


class PersistArgs(StrictModel):
    proposal: Proposal
    proposal_key: str


class ReflectionArgs(StrictModel):
    quest_id: str
    reflection: ReflectionInput
