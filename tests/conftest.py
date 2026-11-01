from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
from spilli_dbal import ModelMixin
from spilli_dbal.dbal import AsyncSqlaDBAL
from spilli_dbal.dbal import SqlaDBAL
from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy import ForeignKey
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session


@pytest.fixture(scope='session')
def fx_base():
    return declarative_base()


@pytest.fixture(scope='session')
def fx_table_models(fx_base):
    class Parents(fx_base, ModelMixin):
        __tablename__ = 'parents'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()
        father_id: Mapped[UUID | None] = mapped_column(ForeignKey('fathers.id'))

        father = relationship(
            'Fathers', backref='parents', cascade='all, delete-orphan', single_parent=True
        )

        @hybrid_property
        def child_count(self) -> int:
            return len(self.children)

    class Children(fx_base, ModelMixin):
        __tablename__ = 'children'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()
        parent_id: Mapped[UUID | None] = mapped_column(ForeignKey('parents.id'))

        parent = relationship(
            'Parents', backref='children', cascade='all, delete-orphan', single_parent=True
        )

    class Fathers(fx_base, ModelMixin):
        __tablename__ = 'fathers'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()

    return Parents, Children, Fathers


@pytest.fixture(scope='session')
def fx_db_engine() -> Engine:
    engine = create_engine('sqlite://', echo=False, future=True)
    return engine


@pytest.fixture(scope='session')
def fx_session(fx_db_engine, fx_base, fx_table_models):
    session = Session(fx_db_engine)

    session.execute(text('PRAGMA foreign_keys=ON'))

    fx_base.metadata.create_all(fx_db_engine)

    yield session

    session.close()


@pytest_asyncio.fixture
async def fx_async_db_engine():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def fx_async_session(
    fx_async_db_engine, fx_base, fx_table_models
) -> AsyncGenerator[AsyncSession, Any]:
    async with fx_async_db_engine.begin() as conn:
        await conn.execute(text('PRAGMA foreign_keys=ON'))
        await conn.run_sync(fx_base.metadata.create_all)
    session = AsyncSession(fx_async_db_engine, expire_on_commit=False)

    yield session

    await session.close()


@pytest.fixture(scope='session')
def fx_parent_dbal(fx_table_models):
    parents_model, _, _ = fx_table_models

    class ParentsDBAL(SqlaDBAL[parents_model]):
        """DBAL for Parents."""

    return ParentsDBAL


@pytest.fixture(scope='session')
def fx_async_parent_dbal(fx_table_models):
    parents_model, _, _ = fx_table_models

    class AsyncParentsDBAL(AsyncSqlaDBAL[parents_model]):
        """DBAL for Parents."""

    return AsyncParentsDBAL


@pytest.fixture
def fx_parent__create(fx_parent_dbal):
    def _f(session: Session, data: dict[str, Any]):
        return fx_parent_dbal(session).create(**data)

    return _f


@pytest.fixture
def fx_child__create(fx_table_models):
    _, child_model, _ = fx_table_models

    class ChildDBAL(SqlaDBAL[child_model]):
        """DBAL for Children."""

    def _f(session: Session, data: dict[str, Any]):
        return ChildDBAL(session).create(**data)

    return _f


@pytest.fixture
def fx_father__create(fx_table_models):
    _, _, father_model = fx_table_models

    class FathersDBAL(SqlaDBAL[father_model]):
        """DBAL for Fathers."""

    def _f(session: Session, data: dict[str, Any]):
        return FathersDBAL(session).create(**data)

    return _f
