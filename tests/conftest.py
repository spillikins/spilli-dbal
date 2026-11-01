from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
from spilli_dbal import ModelMixin
from spilli_dbal.dbal import AsyncSqlaDBAL
from spilli_dbal.dbal import SqlaDBAL
from spilli_dbal.statement_maker import StatementMaker
from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy import ForeignKey
from sqlalchemy import Select
from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

from tests.contrib.schemas import ParentPaginationSchema

UNIQUE_STRING = (f'name_{number}' for number in range(1_000))


@pytest.fixture(scope='session')
def fx_base():
    return declarative_base()


@pytest.fixture(scope='session')
def fx_db_engine() -> Engine:
    engine = create_engine('sqlite://', echo=True, future=True)
    return engine


@pytest.fixture(scope='session')
def fx_session(fx_db_engine, fx_base, fx_table_models) -> Session:
    session = Session(fx_db_engine)

    session.execute(text('PRAGMA foreign_keys=ON'))

    fx_base.metadata.create_all(fx_db_engine)

    return session


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
def fx_parent_dbal(fx_table_models):
    parents_model, _, _ = fx_table_models

    class ParentsDBAL(SqlaDBAL[parents_model]):
        """DBAL for Parents."""

    return ParentsDBAL


@pytest.fixture
def fx_parent__paginate(fx_parent_dbal):
    def _f(session: Session, data: dict[str, Any]):
        params = {k: v for k, v in data.items() if k not in ['fields']}

        result = fx_parent_dbal(session).paginate(**params)

        only = data.get('fields')
        serialized_result = ParentPaginationSchema(only=only).dump(result)

        return serialized_result

    return _f


@pytest.fixture
def fx_parent__create(fx_parent_dbal):
    def _f(session: Session, data: dict[str, Any]):
        return fx_parent_dbal(session).create(**data)

    return _f


@pytest.fixture
def fx_parent__update(fx_parent_dbal):
    def _f(session: Session, data: dict[str, Any]):
        return fx_parent_dbal(session).update(**data)

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


@pytest.fixture
def fx_parents__bulk(fx_session, fx_parent__create):  # noqa: F811
    def _f(count: int) -> list[Any]:
        return [fx_parent__create(fx_session, {'first': next(UNIQUE_STRING)}) for _ in range(count)]

    return _f


@pytest.fixture
def fx_parents__non_deletion(
    fx_session,  # noqa: F811
    fx_parent__create,
    fx_child__create,
    fx_father__create,
):
    def _create_item() -> Result:
        new_father = fx_father__create(fx_session, {'first': next(UNIQUE_STRING)})

        parent_data = {
            'first': next(UNIQUE_STRING),
            'second': f'full {next(UNIQUE_STRING)}',
            'father_id': new_father.id,
        }
        new_parent = fx_parent__create(fx_session, parent_data)
        fx_child__create(fx_session, {'first': next(UNIQUE_STRING), 'parent_id': new_parent.id})
        return new_parent

    return _create_item


@pytest.fixture
def fx_make_stmt(fx_parents__non_deletion):
    def _create_item(
        model,
        where: dict[str, list[Any]] = None,
        order_by: list[dict[str, list[Any]]] = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select:

        params = {}

        if limit is not None:
            params['limit'] = limit

        if offset is not None:
            params['offset'] = offset

        if where:
            params['where'] = where

        if order_by:
            params['order_by'] = order_by

        statement_maker = StatementMaker(model, **params)
        stmt = statement_maker.make_stmt()

        return stmt

    return _create_item


# --- Async Infrastructure ---


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


@pytest.fixture
def fx_async_parent_dbal(fx_table_models):
    parents_model, _, _ = fx_table_models

    class AsyncParentsDBAL(AsyncSqlaDBAL[parents_model]):
        """DBAL for Parents."""

    return AsyncParentsDBAL


@pytest.fixture
def fx_unified_parent_dbal():
    """Фабрика для выполнения CRUD-методов."""

    async def _factory(session, table_dbal, method_name: str, *args, **kwargs):
        dbal = table_dbal(session)
        method = getattr(dbal, method_name)

        if isinstance(session, Session):
            return method(*args, **kwargs)
        elif isinstance(session, AsyncSession):
            return await method(*args, **kwargs)
        else:
            raise TypeError(f'Unsupported session type: {type(session)}')

    return _factory


@pytest.fixture(
    params=[('fx_session', 'fx_parent_dbal'), ('fx_async_session', 'fx_async_parent_dbal')],
    ids=['sync', 'async'],
)
def fx_env(request):
    """Resolve a matching session/DBAL pair before the async test enters its event loop.

    Async fixtures cannot be requested lazily via ``request.getfixturevalue`` from inside
    an async test: fixture setup would need a new event loop while the test's loop is
    already running.
    """

    session = request.getfixturevalue(request.param[0])
    dbal_class = request.getfixturevalue(request.param[1])

    return session, dbal_class
