import pytest
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException

from tests.conftest import UNIQUE_STRING


def test_dbal__create(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    assert new.id
    assert new.first == params['first']


def test_dbal__bulk_create(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    data = [{'first': next(UNIQUE_STRING)}]
    fx_parent_dbal(session_db).bulk_create(data)

    result = fx_parent_dbal(session_db).read_filtered_list(first=data[0]['first'])

    assert result[0].id
    assert result[0].first == data[0]['first']


def test_dbal__read(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    result = fx_parent_dbal(session_db).read(new.id)

    assert result.id == new.id
    assert result.first == new.first


def test_dbal__bulk_read(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    result = fx_parent_dbal(session_db).bulk_read([new.id])

    assert result[0].id == new.id
    assert result[0].first == new.first


def test_dbal__read_all(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    fx_parent_dbal(session_db).create(**params)

    result = fx_parent_dbal(session_db).read_all()

    assert result


def test_dbal__update(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    updated_params = {'first': next(UNIQUE_STRING)}
    updated = fx_parent_dbal(session_db).update(new.id, **updated_params)

    assert updated.id == new.id
    assert updated_params['first'] == new.first


def test_dbal__bulk_update(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    updated_params = [{'id': new.id, 'first': next(UNIQUE_STRING)}]
    fx_parent_dbal(session_db).bulk_update(updated_params)

    result = fx_parent_dbal(session_db).read(new.id)

    assert new.id == result.id
    assert new.first == result.first


def test_dbal__delete(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    new_1 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    new_2 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})

    fx_parent_dbal(session_db).delete(new_2.id)

    with pytest.raises(DBALObjectNotFoundException):
        fx_parent_dbal(session_db).read(new_2.id)

    result = fx_parent_dbal(session_db).read(new_1.id)
    assert result


def test_dbal__bulk_delete(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    new_1 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    new_2 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})

    fx_parent_dbal(session_db).bulk_delete([new_2.id])

    with pytest.raises(DBALObjectNotFoundException):
        fx_parent_dbal(session_db).read(new_2.id)

    result = fx_parent_dbal(session_db).read(new_1.id)
    assert result


def test_dbal__read_one_filtered(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    new_1 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})

    result = fx_parent_dbal(session_db).read_filtered(first=new_1.first)

    assert result == new_1


def test_dbal__read_filtered_list(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    new_1 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    new_2 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    new_3 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    fx_parent_dbal(session_db).create(**{'first': new_3.first, 'second': 'Not None'})

    result = fx_parent_dbal(session_db).read_filtered_list(first=new_1.first)

    assert result == [new_1]

    result = fx_parent_dbal(session_db).read_filtered_list(first=[new_1.first, new_2.first])

    assert result == [new_1, new_2]

    result = fx_parent_dbal(session_db).read_filtered_list(
        id=[new_1.id, new_2.id, new_3.id], first=new_3.first
    )

    assert result == [new_3]

    result = fx_parent_dbal(session_db).read_filtered_list(first=new_3.first, second=None)

    assert result == [new_3]


def test_dbal__read_filtered_list_with_sort(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    new_1 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    new_2 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    new_3 = fx_parent_dbal(session_db).create(**{'first': next(UNIQUE_STRING)})
    fx_parent_dbal(session_db).create(**{'first': new_3.first, 'second': 'Not None'})

    result = fx_parent_dbal(session_db).read_filtered_list(first=[new_1.first, new_2.first])

    assert result == [new_1, new_2]

    result = fx_parent_dbal(session_db).read_filtered_list(
        first=[new_1.first, new_2.first], sort_order='asc', sort_field='first'
    )

    assert result == [new_1, new_2]

    result = fx_parent_dbal(session_db).read_filtered_list(
        first=[new_1.first, new_2.first], sort_order='desc', sort_field='first'
    )

    assert result == [new_2, new_1]
