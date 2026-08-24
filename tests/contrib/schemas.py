from datetime import timezone

from marshmallow import fields
from spilli_dbal.schemas import BaseSchema
from spilli_dbal.schemas import PaginateResultSchema


class IdSchema(BaseSchema):
    id = fields.UUID(required=True)


class FatherSchema(IdSchema):
    first = fields.String(required=True)
    second = fields.String()
    created_at = fields.DateTime()


class ChildSchema(IdSchema):
    first = fields.String(required=True)
    second = fields.String()
    parent_id = fields.UUID()


class ParentSchema(IdSchema):
    first = fields.String(required=True)
    second = fields.String(allow_none=False)
    father_id = fields.UUID()
    created_at = fields.AwareDateTime(default_timezone=timezone.utc)
    father = fields.Nested(FatherSchema)
    children = fields.Nested(ChildSchema, many=True)


class ParentPaginationSchema(PaginateResultSchema):
    items = fields.Nested(ParentSchema, required=True, many=True)
