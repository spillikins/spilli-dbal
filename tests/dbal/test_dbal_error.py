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


@pytest.mark.parametrize('data', column_non_exist_data)
def test_dbal__create_error__non_exist_column(fx_session, fx_parent_dbal, data):
    with pytest.raises(DBALUnexpectedValueTypeException) as e:
        fx_parent_dbal(fx_session).create(**data)

    assert (
        e.value.args[0].args[0] == f"'{list(data)[0]}' is an invalid keyword argument for Parents"
    )


@pytest.mark.parametrize('data', value_type_wrong_data)
def test_dbal__create_error__value_type_wrong(fx_session, fx_parent_dbal, data):
    with pytest.raises(DBALUnexpectedValueTypeException) as e:
        fx_parent_dbal(fx_session).create(**data)

    type_as_string = type(list(data.values())[0]).__name__
    assert (
        e.value.args[0].orig.args[0]
        == f"Error binding parameter 1: type '{type_as_string}' is not supported"
    )


def test_dbal__create_error__not_null_constraint_failed(fx_session, fx_parent_dbal):
    data = {'first': None}

    with pytest.raises(DBALNotNullConstraintFailedException) as e:
        fx_parent_dbal(fx_session).create(**data)

    assert e.value.args[0] == 'NOT NULL constraint failed: parents.first'


def test_dbal__create_error__foreign_key_constraint_failed(fx_session, fx_parent_dbal):
    data = {'first': next(UNIQUE_STRING), 'father_id': uuid4()}

    with pytest.raises(DBALForeignKeyConstraintFailedException) as e:
        fx_parent_dbal(fx_session).create(**data)

    assert e.value.args[0] == 'FOREIGN KEY constraint failed'


@pytest.mark.parametrize('data', [{'first': [1, 2, 3]}])
def test_dbal__bulk_create_error(fx_session, fx_parent_dbal, data):
    with pytest.raises(DBALCreateException):
        fx_parent_dbal(fx_session).bulk_create([data])


def test_dbal__read_error(fx_session, fx_parent_dbal):
    with pytest.raises(DBALObjectNotFoundException):
        fx_parent_dbal(fx_session).read(uuid4())


def test_dbal__update_error__non_exist_object(fx_session, fx_parent_dbal):
    updated_params = {'first': next(UNIQUE_STRING)}
    non_exist_id = uuid4()
    with pytest.raises(DBALObjectNotFoundException) as e:
        fx_parent_dbal(fx_session).update(non_exist_id, **updated_params)

    assert e.value.args[0].args[0] == 'No row was found when one was required'


@pytest.mark.parametrize('data', column_non_exist_data)
def test_dbal__update_error__non_exist_column(fx_session, fx_parent_dbal, data):
    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(fx_session).create(**params)

    updated_params = {**data, 'first': next(UNIQUE_STRING)}

    with pytest.raises(DBALColumnNonExistException) as e:
        fx_parent_dbal(fx_session).update(new.id, **updated_params)

    assert e.value.args[0].args[0] == f'Unconsumed column names: {list(data)[0]}'


@pytest.mark.parametrize('data', value_type_wrong_data)
def test_dbal__update_error__value_type_wrong(fx_session, fx_parent_dbal, data):
    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(fx_session).create(**params)

    updated_params = {**data}

    with pytest.raises(DBALUnexpectedValueTypeException) as e:
        fx_parent_dbal(fx_session).update(new.id, **updated_params)

    type_as_string = type(list(data.values())[0]).__name__
    assert (
        e.value.args[0].orig.args[0]
        == f"Error binding parameter 1: type '{type_as_string}' is not supported"
    )


def test_dbal__update_error__not_null_constraint_failed(fx_session, fx_parent_dbal):
    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(fx_session).create(**params)

    updated_params = {'first': None}

    with pytest.raises(DBALNotNullConstraintFailedException) as e:
        fx_parent_dbal(fx_session).update(new.id, **updated_params)

    assert e.value.args[0] == 'NOT NULL constraint failed: parents.first'


def test_dbal__update_error__foreign_key_constraint_failed(fx_session, fx_parent_dbal):
    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(fx_session).create(**params)

    updated_params = {'father_id': uuid4()}

    with pytest.raises(DBALForeignKeyConstraintFailedException) as e:
        fx_parent_dbal(fx_session).update(new.id, **updated_params)

    assert e.value.args[0] == 'FOREIGN KEY constraint failed'


@pytest.mark.parametrize('data', [{'first': [1, 2, 3]}])
def test_dbal__bulk_update_error(fx_session, fx_parent_dbal, data):
    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(fx_session).create(**params)

    updated_params = [{'id': new.id, **data}]
    with pytest.raises(DBALUpdateException):
        fx_parent_dbal(fx_session).bulk_update(updated_params)


def test_dbal__bulk_update_non_exist_id_error(fx_session, fx_parent_dbal):
    data = {'first': next(UNIQUE_STRING)}
    updated_params = [{'id': uuid4(), **data}]
    with pytest.raises(DBALObjectNotFoundException):
        fx_parent_dbal(fx_session).bulk_update(updated_params)
