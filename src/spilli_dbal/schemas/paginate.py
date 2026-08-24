from typing import Any

from marshmallow import fields
from marshmallow import INCLUDE
from marshmallow import pre_load
from marshmallow import validate
from marshmallow import ValidationError
from spilli_dbal.schemas import BaseSchema


class PaginateSchema(BaseSchema):
    class Meta:
        unknown = INCLUDE

    ids = fields.List(fields.UUID)
    page = fields.Integer(validate=[validate.Range(min=0)])
    per_page = fields.Integer(validate=[validate.Range(min=0)])
    include_metadata = fields.String(validate=validate.OneOf(['enable']))
    fields = fields.List(fields.String)

    @pre_load
    def extract_fields(self, data: dict[str, Any], many, **kwargs):
        prefixes = ['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in', 'sort', 'contain']

        for key, _ in data.items():
            if key in ['ids', 'include_metadata', 'fields', 'page', 'per_page']:
                continue
            else:
                prefix, *_ = key.split('__')
                if prefix in prefixes:
                    continue
                else:
                    raise ValidationError(f'Prefix <{prefix}> not allowed.')
        return data


class PaginationSchema(BaseSchema):
    page = fields.Integer(required=True, validate=[validate.Range(min=0)])
    per_page = fields.Integer(required=True, validate=[validate.Range(min=0)])
    pages = fields.Integer(required=True, validate=[validate.Range(min=0)])
    total = fields.Integer(required=True, validate=[validate.Range(min=0)])


class MetadataSchema(BaseSchema):
    pagination = fields.Nested(PaginationSchema)


class PaginateResultSchema(BaseSchema):
    _metadata = fields.Nested(MetadataSchema)
