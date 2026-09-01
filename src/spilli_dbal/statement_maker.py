from typing import Any
from typing import Literal

from marshmallow import fields
from marshmallow import validate
from marshmallow import validates_schema
from spilli_dbal.schemas import BaseSchema
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy import Select
from sqlalchemy import select


class FilterSchema(BaseSchema):
    col = fields.String(required=True, validate=[validate.Length(min=1)])
    opr = fields.String(
        required=True,
        validate=[validate.OneOf(['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in', 'ilike'])],
    )
    value = fields.Raw(required=True)

    @validates_schema
    def validate_datetime_fields(self, data: dict, **kwargs) -> None:
        pass


class OrderBySchema(BaseSchema):
    col = fields.String(required=True, validate=[validate.Length(min=1)])
    opr = fields.String(required=True, validate=[validate.OneOf(['asc', 'desc'])])


class WhereSchema(BaseSchema):
    and_ = fields.List(fields.Nested(FilterSchema), data_key='and')


class SQLJSONSchema(BaseSchema):
    where = fields.Nested(WhereSchema)
    order_by = fields.Nested(OrderBySchema, many=True)
    limit = fields.Integer(validate=[validate.Range(min=0)])
    offset = fields.Integer(validate=[validate.Range(min=0)])


class StatementMaker:
    """The class builds a SQL statement as a SQLAlchemy object.

    The class works only with one table, is set during initialization in the `model` argument.

    The request is executed outside of this class
    """

    _map_conjunction = {'and': and_, 'or': or_}

    def __init__(
        self,
        model,
        where: dict[str, Any] | None = None,
        order_by: list[dict[str, Any]] | None = None,
        limit: int = 1000,
        offset: int = 0,
    ):
        self._model = model
        self._select = select
        self._where = where
        self._order_by = order_by
        self._limit = limit
        self._offset = offset

        self._validate()

    def _validate(self):
        data = {'limit': self._limit, 'offset': self._offset}

        if self._where is not None:
            data['where'] = self._where

        if self._order_by is not None:
            data['order_by'] = self._order_by

        SQLJSONSchema().load(data)

    def _make_expr(
        self, col: str, opr: Literal['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in', 'ilike'], value: Any
    ) -> bool | Any:
        if opr == 'lt':
            return getattr(self._model, col) < value
        if opr == 'le':
            return getattr(self._model, col) <= value
        elif opr == 'eq':
            return getattr(self._model, col) == value
        elif opr == 'ne':
            return getattr(self._model, col) != value
        elif opr == 'ge':
            return getattr(self._model, col) >= value
        elif opr == 'gt':
            return getattr(self._model, col) > value
        elif opr == 'in':
            return getattr(self._model, col).in_(value)
        elif opr == 'ilike':
            return getattr(self._model, col).ilike(f'%{value}%')
        else:
            raise NotImplementedError(f'Operator <{opr}> not implemented.')

    def _make_where_expression(
        self,
        expressions: (
            dict[Literal['and', 'or'], list[dict[Any, Any]]]
            | dict[Literal['col', 'opr', 'value'], Any]
        ),
    ):
        if 'and' in expressions:
            and_exprs = expressions['and']
            return self._map_conjunction['and'](
                *[self._make_where_expression(expr) for expr in and_exprs]
            )

        if 'or' in expressions:
            raise NotImplementedError('or')

        return self._make_expr(**expressions)

    def make_where(self, where_: dict[str, list[dict[Any, Any]]]) -> Select:
        if len(where_) != 1:
            raise NotImplementedError('Only one key "and" or "or" to top level.')

        return self._make_where_expression(where_)

    def make_order_by(self, order_by_: list[dict[str, Any]]) -> list[Any]:
        order_by_expressions = []
        for order in order_by_:
            if order['opr'] == 'asc':
                order_by_expressions.append(getattr(self._model, order['col']).asc())
            else:
                order_by_expressions.append(getattr(self._model, order['col']).desc())

        return order_by_expressions

    def make_stmt(self) -> Select:
        stmt = select(self._model)

        if self._where:
            stmt = stmt.where(self.make_where(self._where))

        if self._order_by:
            stmt = stmt.order_by(*self.make_order_by(self._order_by))

        stmt = stmt.limit(self._limit).offset(self._offset)
        return stmt
