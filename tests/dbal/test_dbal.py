import pytest
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException

from tests.constants import UNIQUE_STRING


@pytest.mark.asyncio
async def test_create(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new_obj = await fx_dbal_call(session, dbal_class, 'create', **params)

    assert new_obj.id is not None
    assert new_obj.first == params['first']


@pytest.mark.asyncio
async def test_dbal__bulk_create(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    data = [{'first': next(UNIQUE_STRING)}]
    await fx_dbal_call(session, dbal_class, 'bulk_create', data)

    result = await fx_dbal_call(session, dbal_class, 'read_filtered_list', first=data[0]['first'])

    assert result[0].id
    assert result[0].first == data[0]['first']


@pytest.mark.asyncio
async def test_dbal__read(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_dbal_call(session, dbal_class, 'create', **params)

    result = await fx_dbal_call(session, dbal_class, 'read', new.id)

    assert result.id == new.id
    assert result.first == new.first


@pytest.mark.asyncio
async def test_dbal__bulk_read(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_dbal_call(session, dbal_class, 'create', **params)

    result = await fx_dbal_call(session, dbal_class, 'bulk_read', [new.id])

    assert result[0].id == new.id
    assert result[0].first == new.first


@pytest.mark.asyncio
async def test_dbal__read_all(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    await fx_dbal_call(session, dbal_class, 'create', **params)

    result = await fx_dbal_call(session, dbal_class, 'read_all')

    assert result


@pytest.mark.asyncio
async def test_dbal__update(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_dbal_call(session, dbal_class, 'create', **params)

    updated_params = {'first': next(UNIQUE_STRING)}
    updated = await fx_dbal_call(session, dbal_class, 'update', new.id, **updated_params)

    assert updated.id == new.id
    assert updated_params['first'] == updated.first


@pytest.mark.asyncio
async def test_dbal__bulk_update(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    params = {'first': next(UNIQUE_STRING)}
    new = await fx_dbal_call(session, dbal_class, 'create', **params)

    updated_params = [{'id': new.id, 'first': next(UNIQUE_STRING)}]
    await fx_dbal_call(session, dbal_class, 'bulk_update', updated_params)

    result = await fx_dbal_call(session, dbal_class, 'read', new.id)

    assert result.id == updated_params[0]['id']
    assert result.first == updated_params[0]['first']


@pytest.mark.asyncio
async def test_dbal__delete(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    new_1 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    new_2 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})

    await fx_dbal_call(session, dbal_class, 'delete', new_2.id)

    with pytest.raises(DBALObjectNotFoundException):
        await fx_dbal_call(session, dbal_class, 'read', new_2.id)

    result = await fx_dbal_call(session, dbal_class, 'read', new_1.id)
    assert result


@pytest.mark.asyncio
async def test_dbal__bulk_delete(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    new_1 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    new_2 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})

    await fx_dbal_call(session, dbal_class, 'bulk_delete', [new_2.id])

    with pytest.raises(DBALObjectNotFoundException):
        await fx_dbal_call(session, dbal_class, 'read', new_2.id)

    result = await fx_dbal_call(session, dbal_class, 'read', new_1.id)
    assert result


@pytest.mark.asyncio
async def test_dbal__read_one_filtered(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    new_1 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})

    result = await fx_dbal_call(session, dbal_class, 'read_filtered', first=new_1.first)

    assert result == new_1


@pytest.mark.asyncio
async def test_dbal__read_filtered_list(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    new_1 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    new_2 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    new_3 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    await fx_dbal_call(
        session, dbal_class, 'create', **{'first': new_3.first, 'second': 'Not None'}
    )

    result = await fx_dbal_call(session, dbal_class, 'read_filtered_list', first=new_1.first)

    assert result == [new_1]

    result = await fx_dbal_call(
        session, dbal_class, 'read_filtered_list', first=[new_1.first, new_2.first]
    )

    assert result == [new_1, new_2]

    result = await fx_dbal_call(
        session,
        dbal_class,
        'read_filtered_list',
        id=[new_1.id, new_2.id, new_3.id],
        first=new_3.first,
    )

    assert result == [new_3]

    result = await fx_dbal_call(
        session, dbal_class, 'read_filtered_list', first=new_3.first, second=None
    )

    assert result == [new_3]


@pytest.mark.asyncio
async def test_dbal__read_filtered_list_with_sort(fx_env, fx_dbal_call):
    session, dbal_class = fx_env

    new_1 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    new_2 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    new_3 = await fx_dbal_call(session, dbal_class, 'create', **{'first': next(UNIQUE_STRING)})
    await fx_dbal_call(
        session, dbal_class, 'create', **{'first': new_3.first, 'second': 'Not None'}
    )

    result = await fx_dbal_call(
        session, dbal_class, 'read_filtered_list', first=[new_1.first, new_2.first]
    )

    assert result == [new_1, new_2]

    result = await fx_dbal_call(
        session,
        dbal_class,
        'read_filtered_list',
        first=[new_1.first, new_2.first],
        sort_order='asc',
        sort_field='first',
    )

    assert result == [new_1, new_2]

    result = await fx_dbal_call(
        session,
        dbal_class,
        'read_filtered_list',
        first=[new_1.first, new_2.first],
        sort_order='desc',
        sort_field='first',
    )

    assert result == [new_2, new_1]
