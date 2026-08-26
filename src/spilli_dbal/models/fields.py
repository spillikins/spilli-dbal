from datetime import datetime
from datetime import timezone

from sqlalchemy import DateTime
from sqlalchemy import Dialect
from sqlalchemy import TypeDecorator


class UTCDateTime(TypeDecorator):
    """This type ensures that only datetime objects with UTC timezone information are stored in the
    database."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return value

        if not isinstance(value, datetime):
            raise TypeError('Value must be a datetime object.')

        if value.tzinfo is None or value.tzinfo != timezone.utc:
            raise ValueError('Only UTC datetime are allowed.')

        return value

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
