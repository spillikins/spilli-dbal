import uuid
from datetime import datetime
from datetime import timezone

from spilli_dbal.models.fields import UTCDateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


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
        UTCDateTime,
        nullable=False,
        default=make_datetime_with_utc,
        comment='Date and time created',
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, onupdate=make_datetime_with_utc, comment='Date and time updated'
    )
