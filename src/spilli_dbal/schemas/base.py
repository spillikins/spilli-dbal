from datetime import datetime
from datetime import timezone
from typing import Any

from marshmallow import post_dump
from marshmallow import RAISE
from marshmallow import Schema
from marshmallow import validates_schema


class BaseSchema(Schema):
    _empty_values = ('', None, ..., [], {}, (), set())
    _skipped_keys = ()

    class Meta:
        unknown = RAISE

    @post_dump()
    def _delete_keys_with_empty_value(self, data: Any, many: bool = False) -> Any:
        """Clearing hierarchical structures from empty values.

        Cleaning occurs for objects of the list and dict types, other types do not clean.

        :param data: An object for cleaning.
        :param many: Should be set to `True` if ``obj`` is a collection so that the object will be
            serialized to a list.
        :return: Cleaned object.
        """
        if isinstance(data, dict):
            pre_cleaned_dict = {
                k: self._delete_keys_with_empty_value(v, many=many) for k, v in data.items()
            }

            cleaned_dict = {}
            for k, v in pre_cleaned_dict.items():
                if k not in self._skipped_keys and v in self._empty_values:
                    continue
                else:
                    cleaned_dict[k] = v

            return cleaned_dict

        elif isinstance(data, list):
            pre_cleaned_list = [
                self._delete_keys_with_empty_value(item, many=many) for item in data
            ]
            return [item for item in pre_cleaned_list if item not in self._empty_values]

        else:
            return data

    @staticmethod
    def validate_utc_timezone(key: str, value: datetime) -> None:
        time_zone = getattr(value, 'tzinfo', None)
        if time_zone != timezone.utc:
            raise ValueError(
                f'Field <{key}> must be datetime with UTC timezone, but timezone: <{time_zone}>'
            )

    @validates_schema
    def validate_datetime_fields(self, data: dict, **kwargs) -> None:
        for k, v in data.items():
            if isinstance(v, datetime):
                self.validate_utc_timezone(k, v)
