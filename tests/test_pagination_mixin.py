from datetime import timezone
from math import ceil
from uuid import UUID

import pytest
from spilli_dbal.dbal.exceptions import DBALPaginateException

from tests.conftest import UNIQUE_STRING


def test_pagination__pagination(fx_parent__create, fx_parent__paginate):
    ids = [fx_parent__create({'first': next(UNIQUE_STRING)}).id for _ in range(3)]

    data = {'page': 1, 'per_page': 2, 'ids': ids, 'fields': ['items.id', 'items.first']}
    items = fx_parent__paginate(data)

    assert items['items']
    assert len(items['items']) == 2
    for item in items['items']:
        assert UUID(item['id'])
        assert isinstance(item['first'], str)

    data = {'page': 1, 'per_page': 2, 'ids': ids, 'fields': ['items.id', 'items.first']}
    items = fx_parent__paginate(data)

    assert items['items']
    assert len(items['items']) == 2
    for item in items['items']:
        assert UUID(item['id'])
        assert isinstance(item['first'], str)


def test_pagination__sorting(fx_parent__create, fx_parent__paginate):
    ids = [fx_parent__create({'first': next(UNIQUE_STRING)}).id for _ in range(3)]

    data = {'ids': ids, 'sort__created_at': 'asc'}
    items_asc = fx_parent__paginate(data)
    asc_ids = [item['id'] for item in items_asc['items']]

    data = {'ids': ids, 'sort__created_at': 'desc'}
    items_desc = fx_parent__paginate(data)
    desc_ids = [item['id'] for item in items_desc['items']]

    assert asc_ids[0] == desc_ids[-1]


def test_pagination__searching(fx_parent__create, fx_parent__paginate):
    new_item = fx_parent__create({'first': next(UNIQUE_STRING)})
    fx_parent__create({'first': next(UNIQUE_STRING)})
    search_substring = new_item.first[3:]

    data = {'fields': ['items.id', 'items.first'], 'contain__first': search_substring}
    items = fx_parent__paginate(data)
    for item in items['items']:
        assert search_substring in item['first']


def test_pagination__get_fields_of_list(fx_db, fx_parent__create, fx_parent__paginate):
    _, _, _, Fathers = fx_db
    fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {'fields': ['items.id', 'items.first']}
    items = fx_parent__paginate(data)

    assert list(items['items'][0]) == ['id', 'first']


def test_pagination__filtrating(fx_parent__create, fx_parent__update, fx_parent__paginate):
    first_item = fx_parent__create({'first': next(UNIQUE_STRING)})
    _ = [fx_parent__create({'first': next(UNIQUE_STRING)}) for _ in range(10)]

    patched_item_payload = {'id': first_item.id, 'first': 'first for test filtrating'}
    patched_first_item = fx_parent__update(patched_item_payload)

    data = {'eq__first': patched_first_item.first}
    items = fx_parent__paginate(data)

    assert len(items['items']) == 1
    assert items['items'][0]['id'] == str(first_item.id)


def test_pagination__interval_filtration(fx_parent__create, fx_parent__paginate):
    item_1 = fx_parent__create({'first': next(UNIQUE_STRING)})
    item_2 = fx_parent__create({'first': next(UNIQUE_STRING)})
    item_3 = fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {
        'ids': [item_1.id, item_2.id, item_3.id],
        'sort__created_at': 'asc',
        'ge__created_at': item_1.created_at.replace(tzinfo=timezone.utc),
        'le__created_at': item_2.created_at.replace(tzinfo=timezone.utc),
    }
    items_asc = fx_parent__paginate(data)

    assert items_asc['items']
    assert len(items_asc['items']) == 2
    assert items_asc['items'][0]['id'] == str(item_1.id)
    assert items_asc['items'][1]['id'] == str(item_2.id)

    data = {
        'ids': [item_1.id, item_2.id, item_3.id],
        'sort__created_at': 'desc',
        'ge__created_at': item_1.created_at.replace(tzinfo=timezone.utc),
        'le__created_at': item_2.created_at.replace(tzinfo=timezone.utc),
    }
    items_desc = fx_parent__paginate(data)

    assert items_desc['items']
    assert len(items_desc['items']) == 2
    assert items_desc['items'][0]['id'] == str(item_2.id)
    assert items_desc['items'][1]['id'] == str(item_1.id)


@pytest.mark.parametrize('page', [-1])
@pytest.mark.parametrize('per_page', [-1, 0])
def test_pagination__get_non_exist_page(fx_parent__create, fx_parent__paginate, page, per_page):
    fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {'page': page, 'per_page': per_page, 'include_metadata': 'enable'}
    with pytest.raises(DBALPaginateException):
        fx_parent__paginate(data)


@pytest.mark.parametrize('page', [1, 2])
@pytest.mark.parametrize('per_page', [1, 2])
def test_pagination__get_pages(fx_parent__create, fx_parent__paginate, page, per_page):
    fx_parent__create({'first': next(UNIQUE_STRING)})
    fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {'page': page, 'per_page': per_page, 'include_metadata': 'enable'}
    items = fx_parent__paginate(data)

    assert items['_metadata']['pagination']['page'] == page
    assert items['_metadata']['pagination']['per_page'] == per_page
    assert items['_metadata']['pagination']['pages'] == ceil(
        items['_metadata']['pagination']['total'] / per_page
    )
    assert items['_metadata']['pagination']['total'] > 1
    assert len(items['items']) == per_page


def test_pagination__count_pages_total(fx_parent__create, fx_parent__paginate):
    item_1 = fx_parent__create({'first': next(UNIQUE_STRING)})
    fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {'eq__id': item_1.id, 'include_metadata': 'enable'}
    items = fx_parent__paginate(data)

    assert items['_metadata']['pagination']['pages'] == 1
    assert items['_metadata']['pagination']['total'] == 1
    assert len(items['items']) == 1


def test_pagination__without_meta_pagination(fx_db, fx_parent__create, fx_parent__paginate):
    fx_parent__create({'first': next(UNIQUE_STRING)})
    fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {'page': 1, 'per_page': 2}
    items = fx_parent__paginate(data)

    assert '_metadata' not in items
    assert items['items']


def test_pagination__fields_for_relations(
    fx_parent__create,
    fx_child__create,
    fx_father__create,
    fx_parent__paginate,
):
    new_father_1 = fx_father__create({'first': next(UNIQUE_STRING)})
    new_parent_1 = fx_parent__create({'first': next(UNIQUE_STRING), 'father_id': new_father_1.id})
    fx_child__create({'first': next(UNIQUE_STRING), 'parent_id': new_parent_1.id})

    new_father = fx_father__create({'first': next(UNIQUE_STRING)})
    new_parent = fx_parent__create({'first': next(UNIQUE_STRING), 'father_id': new_father.id})
    new_child = fx_child__create({'first': next(UNIQUE_STRING), 'parent_id': new_parent.id})

    data = {
        'fields': [
            'items.id',
            'items.second',
            'items.created_at',
            'items.father.id',
            'items.father.created_at',
            'items.children.id',
            'items.children.parent_id',
        ],
        'eq__id': new_parent.id,
    }
    items = fx_parent__paginate(data)

    assert len(items['items']) == 1
    assert items['items'][0]['id'] == str(new_parent.id)
    assert items['items'][0].get('second') is None
    assert items['items'][0]['created_at'] == new_parent.created_at.isoformat()
    assert items['items'][0]['father'] == {
        'id': str(new_father.id),
        'created_at': new_father.created_at.isoformat(),
    }
    assert items['items'][0]['children'] == [
        {'id': str(new_child.id), 'parent_id': str(new_parent.id)}
    ]


def test_pagination__pagination__nullable(fx_parent__create, fx_parent__paginate):
    _ = [fx_parent__create({'first': next(UNIQUE_STRING)}).id for _ in range(3)]

    data = {'page': 0, 'per_page': 0, 'include_metadata': 'enable'}

    with pytest.raises(DBALPaginateException) as exc:
        fx_parent__paginate(data)

    assert exc.value.args[0] == 'Page <0> must be greater <1>.'


def test_pagination__format_param_error(fx_parent__create, fx_parent__paginate):
    item_1 = fx_parent__create({'first': next(UNIQUE_STRING)})
    fx_parent__create({'first': next(UNIQUE_STRING)})

    data = {'eq_id': item_1.id}

    with pytest.raises(DBALPaginateException) as exc:
        fx_parent__paginate(data)

    assert exc.value.args[0] == 'not enough values to unpack (expected 2, got 1)'
