from math import ceil
from typing import Any

from spilli_dbal.dbal.exceptions import DBALPaginateException
from spilli_dbal.statement_maker import StatementMaker
from sqlalchemy import func


class PageMixinBase:
    """Base mixin for pagination logic."""

    _filter_prefixes = ['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in']

    _search_prefixes = ['contain']

    _sort_prefixes = ['sort']
    _sort_value = {'asc': 'asc', 'desc': 'desc'}

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
                if value not in self._sort_value:
                    raise DBALPaginateException(
                        f'Invalid sort value <{value}>. Expected one of: {list(self._sort_value)}'
                    )
                order_by.append({'col': param, 'opr': self._sort_value[value]})
            elif prefix in self._search_prefixes:
                filters.append({'col': param, 'opr': 'ilike', 'value': value})
            else:
                raise DBALPaginateException(f'Expression for parameter <{name}> not implemented.')

        return order_by, filters

    def query_string_to_sql_json(
        self, page: int, per_page: int, ids: list[str] | None = None, **params: dict[str, Any]
    ) -> Any:
        sql_as_json = {'limit': per_page, 'offset': (page - 1) * per_page}

        order_by, filters = self._extract_expressions(params)

        if ids:
            filters.append({'col': 'id', 'opr': 'in', 'value': ids})

        if filters:
            sql_as_json['where'] = {'and': filters}

        if order_by:
            sql_as_json['order_by'] = order_by

        return sql_as_json

    def _validate_params(self, page: int, per_page: int):
        if page < 1:
            raise DBALPaginateException(f'Page <{page}> must be greater <1>.')
        if per_page < 1:
            raise DBALPaginateException(f'Per page <{per_page}> must be greater <1>.')

    def _prepare_request(self, ids: list[str] | None, page: int, per_page: int, data: dict) -> Any:
        sql_as_json = self.query_string_to_sql_json(ids=ids, page=page, per_page=per_page, **data)
        return StatementMaker(self._model, **sql_as_json).make_stmt()

    def _get_count_statement(self, statement: Any) -> Any:
        return (
            statement.with_only_columns(func.count())
            .select_from(self._model)
            .order_by(None)
            .limit(None)
            .offset(None)
        )

    def _build_metadata(self, total: int, page: int, per_page: int) -> dict:
        pages = ceil(total / per_page)
        return {'pagination': {'page': page, 'per_page': per_page, 'pages': pages, 'total': total}}


class PageMixin(PageMixinBase):
    """Read objects from database as page."""

    def paginate(
        self,
        ids: list[str] | None = None,
        page: int = 1,
        per_page: int = 20,
        include_metadata: bool = False,
        **data: dict[str, Any],
    ) -> Any:

        self._validate_params(page, per_page)
        statement = self._prepare_request(ids, page, per_page, data)

        items = self._session.scalars(statement).all()
        result = {'items': items}

        if include_metadata:
            total = self._session.scalar(self._get_count_statement(statement))
            result['_metadata'] = self._build_metadata(total, page, per_page)

        return result


class AsyncPageMixin(PageMixinBase):
    """Read objects from database as page for async sessions."""

    async def paginate(
        self,
        ids: list[str] | None = None,
        page: int = 1,
        per_page: int = 20,
        include_metadata: bool = False,
        **data: dict[str, Any],
    ) -> Any:

        self._validate_params(page, per_page)
        statement = self._prepare_request(ids, page, per_page, data)

        result_scalars = await self._session.scalars(statement)
        items = result_scalars.all()
        result = {'items': items}

        if include_metadata:
            count_stmt = self._get_count_statement(statement)
            total = await self._session.scalar(count_stmt)
            result['_metadata'] = self._build_metadata(total, page, per_page)

        return result
