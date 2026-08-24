import uuid
from datetime import datetime
from datetime import timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import validates


def make_uuid4() -> uuid.UUID:
    return uuid.uuid4()


def make_datetime_with_utc() -> datetime:
    return datetime.now(timezone.utc)


class ModelMixin:
    """Mixin for table model."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, nullable=False, default=make_uuid4, comment='UUID'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=make_datetime_with_utc,
        comment='Date and time created',
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=make_datetime_with_utc, comment='Date and time updated'
    )

    @staticmethod
    def validate_utc_timezone(key: str, value: datetime) -> datetime:
        time_zone = getattr(value, 'tzinfo', None)
        if time_zone != timezone.utc:
            raise ValueError(
                f'Field <{key}> must be datetime with UTC timezone,'
                f' but received timezone: <{time_zone}>'
            )

        return value

    @validates('created_at', 'updated_at')
    def validate_timezone(self, key, value) -> datetime:
        return self.validate_utc_timezone(key, value)
