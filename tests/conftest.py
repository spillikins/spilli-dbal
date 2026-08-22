from typing import Any
from uuid import UUID

import pytest
from spilli_dbal import ModelMixin
from spilli_dbal.dbal import SqlaDBAL
from spilli_dbal.statement_maker import StatementMaker
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Select
from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

from tests.contrib.schemas import ParentPaginationSchema

UNIQUE_STRING = (f'name_{number}' for number in range(1_000))


@pytest.fixture(scope='session')
def fx_db_connection():
    engine = create_engine('sqlite://', echo=True, future=True)
    session = Session(engine)
    Base = declarative_base()

    session.execute(text('PRAGMA foreign_keys=ON'))

    return Base, engine, session


@pytest.fixture(scope='session')
def fx_db(fx_db_connection):
    Base, engine, session = fx_db_connection

    class Parents(Base, ModelMixin):
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

    class Children(Base, ModelMixin):
        __tablename__ = 'children'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()
        parent_id: Mapped[UUID | None] = mapped_column(ForeignKey('parents.id'))

        parent = relationship(
            'Parents', backref='children', cascade='all, delete-orphan', single_parent=True
        )

    class Fathers(Base, ModelMixin):
        __tablename__ = 'fathers'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()

    Base.metadata.create_all(engine)

    return session, Parents, Children, Fathers


@pytest.fixture(scope='session')
def fx_parent_dbal(fx_db):
    session_db, parents_model, _, _ = fx_db

    class ParentsDBAL(SqlaDBAL[parents_model]):
        """DBAL for Parents."""

    return ParentsDBAL


@pytest.fixture(scope='session')
def fx_parent__paginate(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    def _f(data: dict[str, Any]):
        params = {k: v for k, v in data.items() if k not in ['fields']}

        result = fx_parent_dbal(session_db).paginate(**params)

        only = data.get('fields')
        serialized_result = ParentPaginationSchema(only=only).dump(result)

        return serialized_result

    return _f


@pytest.fixture(scope='session')
def fx_parent__create(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    def _f(data: dict[str, Any]):
        return fx_parent_dbal(session_db).create(**data)

    return _f


@pytest.fixture(scope='session')
def fx_parent__update(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    def _f(data: dict[str, Any]):
        return fx_parent_dbal(session_db).update(**data)

    return _f


@pytest.fixture(scope='session')
def fx_child__create(fx_db, fx_parent_dbal):
    session_db, _, child_model, _ = fx_db

    class ChildDBAL(SqlaDBAL[child_model]):
        """DBAL for Children."""

    def _f(data: dict[str, Any]):
        return ChildDBAL(session_db).create(**data)

    return _f


@pytest.fixture(scope='session')
def fx_father__create(fx_db, fx_parent_dbal):
    session_db, _, _, father_model = fx_db

    class FathersDBAL(SqlaDBAL[father_model]):
        """DBAL for Fathers."""

    def _f(data: dict[str, Any]):
        return FathersDBAL(session_db).create(**data)

    return _f


@pytest.fixture
def fx_parents__non_deletion(fx_parent__create, fx_child__create, fx_father__create):
    def _create_item() -> Result:
        new_father = fx_father__create({'first': next(UNIQUE_STRING)})

        parent_data = {
            'first': next(UNIQUE_STRING),
            'second': f'full {next(UNIQUE_STRING)}',
            'father_id': new_father.id,
        }
        new_parent = fx_parent__create(parent_data)
        fx_child__create({'first': next(UNIQUE_STRING), 'parent_id': new_parent.id})
        return new_parent

    return _create_item


@pytest.fixture
def fx_make_stmt(fx_db, fx_parents__non_deletion):
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
