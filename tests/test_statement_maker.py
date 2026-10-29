from spilli_dbal.statement_maker import StatementMaker
from sqlalchemy import select

from tests.conftest import UNIQUE_STRING


def test_statement_maker__init(fx_table_models):
    Parents, _, _ = fx_table_models

    stmt = StatementMaker(Parents, limit=0, offset=1).make_stmt()
    assert stmt.compile().string == select(Parents).limit(1).offset(1).compile().string


def test_statement_maker__filter__lt(fx_table_models, fx_make_stmt, fx_parent__create, fx_session):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parent__create(fx_session, {'first': next(UNIQUE_STRING)})

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'created_at', 'opr': 'lt', 'value': parent_1.created_at}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.created_at < parent_1.created_at)
        .limit(0)
        .offset(1)
        .compile()
        .string
    )

    assert compiled_stmt == compiled_control_stmt


def test_statement_maker__filter__le(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'created_at', 'opr': 'le', 'value': parent_1.created_at}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.created_at <= parent_1.created_at)
        .limit(0)
        .offset(1)
        .compile()
        .string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter__eq(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'id', 'opr': 'eq', 'value': parent_1.id}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents).where(Parents.id == parent_1.id).limit(0).offset(1).compile().string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter__ne(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'id', 'opr': 'ne', 'value': parent_1.id}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents).where(Parents.id != parent_1.id).limit(0).offset(1).compile().string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter__ge(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'created_at', 'opr': 'ge', 'value': parent_1.created_at}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.created_at >= parent_1.created_at)
        .limit(0)
        .offset(1)
        .compile()
        .string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter__gt(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'created_at', 'opr': 'gt', 'value': parent_1.created_at}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.created_at > parent_1.created_at)
        .limit(0)
        .offset(1)
        .compile()
        .string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter_in(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'id', 'opr': 'in', 'value': [parent_1.id]}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents).where(Parents.id.in_([parent_1.id])).limit(0).offset(1).compile().string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter_contains(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={'and': [{'col': 'id', 'opr': 'ilike', 'value': parent_1.first[:4]}]},
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.id.ilike(f'%{parent_1.first[:4]}%'))
        .limit(0)
        .offset(1)
        .compile()
        .string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__filter__le_ge(fx_table_models, fx_make_stmt, fx_parents__non_deletion):
    Parents, _, _ = fx_table_models

    parent_1 = fx_parents__non_deletion()

    statement_maker = fx_make_stmt(
        Parents,
        where={
            'and': [
                {'col': 'created_at', 'opr': 'le', 'value': parent_1.created_at},
                {'col': 'created_at', 'opr': 'ge', 'value': parent_1.created_at},
            ]
        },
    )
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.created_at <= parent_1.created_at, Parents.created_at >= parent_1.id)
        .limit(0)
        .offset(1)
        .compile()
        .string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__sort(fx_table_models, fx_make_stmt):
    Parents, _, _ = fx_table_models

    statement_maker = fx_make_stmt(Parents, order_by=[{'col': 'id', 'opr': 'asc'}])
    compiled_stmt = statement_maker.compile().string

    compiled_control_stmt = (
        select(Parents).order_by(Parents.id.asc()).limit(0).offset(1).compile().string
    )

    assert compiled_stmt in compiled_control_stmt
