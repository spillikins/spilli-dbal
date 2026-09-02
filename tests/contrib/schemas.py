from datetime import timezone

from marshmallow import fields
from marshmallow import validate
from spilli_dbal.schemas import BaseSchema


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


class PaginationSchema(BaseSchema):
    page = fields.Integer(required=True, validate=[validate.Range(min=1)])
    per_page = fields.Integer(required=True, validate=[validate.Range(min=1)])
    pages = fields.Integer(required=True, validate=[validate.Range(min=0)])
    total = fields.Integer(required=True, validate=[validate.Range(min=0)])


class MetadataSchema(BaseSchema):
    pagination = fields.Nested(PaginationSchema)


class PaginateResultSchema(BaseSchema):
    _metadata = fields.Nested(MetadataSchema)


class ParentPaginationSchema(PaginateResultSchema):
    items = fields.Nested(ParentSchema, required=True, many=True)
