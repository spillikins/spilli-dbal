from uuid import uuid4

import pytest
from spilli_dbal.dbal.exceptions import DBALColumnNonExistException
from spilli_dbal.dbal.exceptions import DBALCreateException
from spilli_dbal.dbal.exceptions import DBALForeignKeyConstraintFailedException
from spilli_dbal.dbal.exceptions import DBALNotNullConstraintFailedException
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
from spilli_dbal.dbal.exceptions import DBALUnexpectedValueTypeException
from spilli_dbal.dbal.exceptions import DBALUpdateException

from tests.conftest import UNIQUE_STRING

column_non_exist_data = [{'unknown': 'unknown'}, {'': 'unknown'}]
value_type_wrong_data = [{'first': [1, 2, 3]}, {'first': {'key': 'value'}}]


@pytest.mark.asyncio
@pytest.mark.parametrize('data', column_non_exist_data)
async def test_dbal__create_error__non_exist_column(fx_env, fx_unified_parent_dbal, data):
    session, dbal_class = fx_env

    with pytest.raises(DBALUnexpectedValueTypeException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'create', **data)

    assert (
        e.value.args[0].args[0] == f"'{list(data)[0]}' is an invalid keyword argument for Parents"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('data', value_type_wrong_data)
async def test_dbal__create_error__value_type_wrong(fx_env, fx_unified_parent_dbal, data):
    session, dbal_class = fx_env

    with pytest.raises(DBALUnexpectedValueTypeException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'create', **data)

    type_as_string = type(list(data.values())[0]).__name__
    assert (
        e.value.args[0].orig.args[0]
        == f"Error binding parameter 1: type '{type_as_string}' is not supported"
    )


@pytest.mark.asyncio
async def test_dbal__create_error__not_null_constraint_failed(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    data = {'first': None}

    with pytest.raises(DBALNotNullConstraintFailedException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'create', **data)

    assert e.value.args[0] == 'NOT NULL constraint failed: parents.first'


@pytest.mark.asyncio
async def test_dbal__create_error__foreign_key_constraint_failed(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    data = {'first': next(UNIQUE_STRING), 'father_id': uuid4()}

    with pytest.raises(DBALForeignKeyConstraintFailedException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'create', **data)

    assert e.value.args[0] == 'FOREIGN KEY constraint failed'


@pytest.mark.asyncio
@pytest.mark.parametrize('data', [{'first': [1, 2, 3]}])
async def test_dbal__bulk_create_error(fx_env, fx_unified_parent_dbal, data):
    session, dbal_class = fx_env

    with pytest.raises(DBALCreateException):
        await fx_unified_parent_dbal(session, dbal_class, 'bulk_create', [data])


@pytest.mark.asyncio
async def test_dbal__read_error(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    with pytest.raises(DBALObjectNotFoundException):
        await fx_unified_parent_dbal(session, dbal_class, 'read', uuid4())


@pytest.mark.asyncio
async def test_dbal__update_error__non_exist_object(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    updated_params = {'first': next(UNIQUE_STRING)}
    non_exist_id = uuid4()
    with pytest.raises(DBALObjectNotFoundException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'update', non_exist_id, **updated_params)

    assert e.value.args[0].args[0] == 'No row was found when one was required'


@pytest.mark.asyncio
@pytest.mark.parametrize('data', column_non_exist_data)
async def test_dbal__update_error__non_exist_column(fx_env, fx_unified_parent_dbal, data):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_unified_parent_dbal(session, dbal_class, 'create', **params)

    updated_params = {**data, 'first': next(UNIQUE_STRING)}

    with pytest.raises(DBALColumnNonExistException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'update', new.id, **updated_params)

    assert e.value.args[0].args[0] == f'Unconsumed column names: {list(data)[0]}'


@pytest.mark.asyncio
@pytest.mark.parametrize('data', value_type_wrong_data)
async def test_dbal__update_error__value_type_wrong(fx_env, fx_unified_parent_dbal, data):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_unified_parent_dbal(session, dbal_class, 'create', **params)

    updated_params = {**data}

    with pytest.raises(DBALUnexpectedValueTypeException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'update', new.id, **updated_params)

    type_as_string = type(list(data.values())[0]).__name__
    assert (
        e.value.args[0].orig.args[0]
        == f"Error binding parameter 1: type '{type_as_string}' is not supported"
    )


@pytest.mark.asyncio
async def test_dbal__update_error__not_null_constraint_failed(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_unified_parent_dbal(session, dbal_class, 'create', **params)

    updated_params = {'first': None}

    with pytest.raises(DBALNotNullConstraintFailedException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'update', new.id, **updated_params)

    assert e.value.args[0] == 'NOT NULL constraint failed: parents.first'


@pytest.mark.asyncio
async def test_dbal__update_error__foreign_key_constraint_failed(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_unified_parent_dbal(session, dbal_class, 'create', **params)

    updated_params = {'father_id': uuid4()}

    with pytest.raises(DBALForeignKeyConstraintFailedException) as e:
        await fx_unified_parent_dbal(session, dbal_class, 'update', new.id, **updated_params)

    assert e.value.args[0] == 'FOREIGN KEY constraint failed'


@pytest.mark.asyncio
@pytest.mark.parametrize('data', [{'first': [1, 2, 3]}])
async def test_dbal__bulk_update_error(fx_env, fx_unified_parent_dbal, data):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_unified_parent_dbal(session, dbal_class, 'create', **params)

    updated_params = [{'id': new.id, **data}]
    with pytest.raises(DBALUpdateException):
        await fx_unified_parent_dbal(session, dbal_class, 'bulk_update', updated_params)


@pytest.mark.asyncio
async def test_dbal__bulk_update_non_exist_id_error(fx_env, fx_unified_parent_dbal):
    session, dbal_class = fx_env

    data = {'first': next(UNIQUE_STRING)}
    updated_params = [{'id': uuid4(), **data}]
    with pytest.raises(DBALObjectNotFoundException):
        await fx_unified_parent_dbal(session, dbal_class, 'bulk_update', updated_params)
