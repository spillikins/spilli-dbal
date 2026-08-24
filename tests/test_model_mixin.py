from datetime import datetime

import pytest


@pytest.mark.parametrize('date_time', ['', None, 'not_date_time', datetime.now()])
def test_model_mixin__validate_timezone(fx_db, date_time):
    session, _, _, Fathers = fx_db

    with pytest.raises(ValueError, match=r'.* <created_at> .*') as e:
        Fathers(first='first', created_at=date_time)

    assert e.value.args[0] == (
        'Field <created_at> must be datetime with UTC timezone, but received timezone: <None>'
    )
