"""显式提供 TEST_POSTGRES_URL 才运行；在独立临时 schema 中验证外键。"""

import os
from uuid import uuid4
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db import Base, make_engine
from app.models import Quest, QuestStar, Star


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="没有配置 PostgreSQL 集成测试连接")
def test_postgres_json_and_foreign_key():
    engine = make_engine(os.environ["TEST_POSTGRES_URL"])
    schema = "test_" + uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated = engine.execution_options(schema_translate_map={None: schema})
    try:
        Base.metadata.create_all(isolated)
        with Session(isolated) as session:
            star = Star(
                title="海洋",
                original_text="海洋",
                description="",
                category="自然",
                tags=["海洋"],
                source_type="manual",
                status="collected",
            )
            quest = Quest(
                proposal_key="test",
                title="记录问题",
                description="写作",
                estimated_minutes=5,
                estimated_budget=0,
                energy_level="low",
                steps=["写问题"],
                rationale="来自海洋",
                status="accepted",
            )
            session.add_all([star, quest])
            session.flush()
            session.add(QuestStar(quest_id=quest.id, star_id=star.id))
            session.commit()
            assert session.get(Star, star.id).tags == ["海洋"]
            session.delete(star)
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()
