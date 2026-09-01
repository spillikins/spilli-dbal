from datetime import datetime
from datetime import UTC
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.exc import StatementError


@pytest.mark.parametrize('date_time', [None, datetime.now(UTC)])
def test_model_mixin__validate_timezone(fx_db, date_time):
    session, _, _, Fathers = fx_db

    f = Fathers(first='first', created_at=date_time)
    session.add(f)
    session.flush()


@pytest.mark.parametrize('date_time', ['', 'not_date_time'])
def test_model_mixin__validate_timezone_not_datetime(fx_db, date_time):
    session, _, _, Fathers = fx_db

    f = Fathers(first='first', created_at=date_time)
    session.add(f)

    with pytest.raises(StatementError) as e:
        session.flush()

    session.rollback()

    assert e.value.args[0] == '(builtins.TypeError) Value must be a datetime object.'


@pytest.mark.parametrize('date_time', [datetime.now(ZoneInfo('Europe/Moscow')), datetime.now()])
def test_model_mixin__validate_timezone_not_utc(fx_db, date_time):
    session, _, _, Fathers = fx_db

    f = Fathers(first='first', created_at=date_time)
    session.add(f)

    with pytest.raises(StatementError) as e:
        session.flush()

    session.rollback()

    assert e.value.args[0] == '(builtins.ValueError) Only UTC datetime are allowed.'
