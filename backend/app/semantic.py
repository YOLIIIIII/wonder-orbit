"""第二阶段扩展接口。MVP 不调用 Embedding，也不声称语义理解。"""

from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SemanticRetriever(Protocol):
    def search(self, query: str, limit: int = 10) -> list[dict]: ...
