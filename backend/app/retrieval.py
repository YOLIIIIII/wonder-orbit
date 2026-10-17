"""可解释关键词检索；Embedding 接口单独放在 semantic.py。"""

import re
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Star


def tokens(text: str) -> set[str]:
    chunks = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text.lower())
    result = set()
    for chunk in chunks:
        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
            result.update(chunk[i : i + 2] for i in range(len(chunk) - 1))
            if len(chunk) == 1:
                result.add(chunk)
        else:
            result.add(chunk)
    return result


def record_dict(record) -> dict:
    data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
    # SQLite 会丢弃 DateTime 时区；数据库内所有时间统一按 UTC 写入。
    return {
        key: value.replace(tzinfo=timezone.utc)
        if isinstance(value, datetime) and value.tzinfo is None
        else value
        for key, value in data.items()
    }


def star_dict(star: Star) -> dict:
    return record_dict(star)


def search(
    session: Session, query: str, category: str | None = None, include_archived: bool = True
) -> list[dict]:
    statement = select(Star)
    if category:
        statement = statement.where(Star.category == category)
    if not include_archived:
        statement = statement.where(Star.status != "archived")
    query_tokens = tokens(query)
    matches = []
    for star in session.scalars(statement):
        searchable = " ".join([star.title, star.description, star.original_text, star.category, *star.tags])
        shared = sorted(query_tokens & tokens(searchable))
        if query_tokens and not shared:
            continue
        matches.append(
            {
                "star_id": star.id,
                "title": star.title,
                "text": star.description or star.original_text,
                "tags": star.tags,
                "category": star.category,
                "score": len(shared),
                "match_basis": shared if query_tokens else ["全部档案"],
            }
        )
    return sorted(matches, key=lambda item: (-item["score"], item["star_id"]))[:20]


def relations(session: Session) -> list[dict]:
    stars = list(session.scalars(select(Star)))
    edges = []
    for i, left in enumerate(stars):
        for right in stars[i + 1 :]:
            tags = sorted(set(left.tags) & set(right.tags))
            reasons = [f"共同标签：{tag}" for tag in tags]
            if left.category == right.category and left.category != "未分类":
                reasons.append(f"共同类别：{left.category}")
            if reasons:
                edges.append(
                    {
                        "from_id": left.id,
                        "to_id": right.id,
                        "from_title": left.title,
                        "to_title": right.title,
                        "reasons": reasons,
                    }
                )
    return edges
