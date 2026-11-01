import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


@pytest.fixture
def fx_dbal_call():
    """Фабрика для выполнения CRUD-методов."""

    async def _factory(session, table_dbal, method_name: str, *args, **kwargs):
        dbal = table_dbal(session)
        method = getattr(dbal, method_name)

        if isinstance(session, Session):
            return method(*args, **kwargs)
        elif isinstance(session, AsyncSession):
            return await method(*args, **kwargs)
        else:
            raise TypeError(f'Unsupported session type: {type(session)}')

    return _factory


@pytest.fixture(
    params=[('fx_session', 'fx_parent_dbal'), ('fx_async_session', 'fx_async_parent_dbal')],
    ids=['sync', 'async'],
)
def fx_env(request):
    """Resolve a matching session/DBAL pair before the async test enters its event loop.

    Async fixtures cannot be requested lazily via ``request.getfixturevalue`` from inside
    an async test: fixture setup would need a new event loop while the test's loop is
    already running.
    """

    session = request.getfixturevalue(request.param[0])
    dbal_class = request.getfixturevalue(request.param[1])

    return session, dbal_class
