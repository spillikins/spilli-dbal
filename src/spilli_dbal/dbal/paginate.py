from math import ceil
from typing import Any

from spilli_dbal.dbal.exceptions import DBALPaginateException
from spilli_dbal.statement_maker import StatementMaker
from sqlalchemy import func


class PageMixin:
    """Read objects from database as page."""

    _filter_prefixes = ['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in']

    _search_prefixes = ['contain']

    _sort_prefixes = ['sort']
    _asc_value = 'asc'
    _desc_value = 'desc'

    def _extract_expressions(self, params: dict[str, Any]):
        order_by = []
        filters = []
        for name, value in params.items():
            try:
                prefix, param = name.split('__')
            except ValueError as exc:
                raise DBALPaginateException(exc.args[0]) from exc

            if prefix in self._filter_prefixes:
                filters.append({'col': param, 'opr': prefix, 'value': value})
            elif prefix in self._sort_prefixes:
                order_by.append({'col': param, 'opr': value})
            elif prefix in self._search_prefixes:
                filters.append({'col': param, 'opr': 'ilike', 'value': value})
            else:
                raise NotImplementedError(f'Expression for parameter <{name}> not implemented.')

        return order_by, filters

    def query_string_to_sql_json(
        self,
        page: int,
        per_page: int,
        ids: list[str] | None = None,
        **params: dict[str, Any],
    ) -> dict[str, Any]:
        sql_as_json = {'limit': per_page, 'offset': (page - 1) * per_page}

        order_by, filters = self._extract_expressions(params)

        if ids:
            filters.append({'col': 'id', 'opr': 'in', 'value': ids})

        if filters:
            sql_as_json['where'] = {'and': filters}

        if order_by:
            sql_as_json['order_by'] = order_by

        return sql_as_json

    def paginate(
        self,
        ids: list[str] | None = None,
        page: int = 1,
        per_page: int = 20,
        include_metadata: bool = False,
        **data: dict[str, Any],
    ) -> dict[str, Any]:

        if page < 1:
            raise DBALPaginateException(f'Page <{page}> must be greater <1>.')

        if per_page < 1:
            raise DBALPaginateException(f'Page <{per_page}> must be greater <1>.')

        sql_as_json = self.query_string_to_sql_json(ids=ids, page=page, per_page=per_page, **data)

        statement = StatementMaker(self._model, **sql_as_json).make_stmt()
        items = self._session.scalars(statement).all()

        result = {'items': items}

        if include_metadata:
            total = self._session.scalar(
                statement.with_only_columns(func.count())
                .select_from(self._model)
                .order_by(None)
                .limit(None)
                .offset(None)
            )

            pages = ceil(total / per_page)

            result['_metadata'] = {
                'pagination': {'page': page, 'per_page': per_page, 'pages': pages, 'total': total}
            }

        return result
