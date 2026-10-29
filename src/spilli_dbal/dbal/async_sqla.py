from collections.abc import Sequence
from typing import Any
from typing import Literal

from spilli_dbal.dbal.exceptions import DBALCreateException
from spilli_dbal.dbal.exceptions import DBALMultipleResultsFoundException
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
from spilli_dbal.dbal.exceptions import DBALUnexpectedValueTypeException
from spilli_dbal.dbal.exceptions import DBALUpdateException
from spilli_dbal.dbal.paginate import AsyncPageMixin
from spilli_dbal.dbal.sqla import compile_error_handler
from spilli_dbal.dbal.sqla import integrity_error_handler
from spilli_dbal.dbal.sqla import SqlaDBALBase
from sqlalchemy import Result
from sqlalchemy import update
from sqlalchemy.exc import CompileError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError


class AsyncSqlaDBAL[M](SqlaDBALBase[M], AsyncPageMixin):
    """Async SqlaDBAL, implement base CRUD sqlalchemy operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs) -> M:
        new_obj = self._make_instance(**kwargs)

        self._session.add(new_obj)

        try:
            await self._session.commit()

        except CompileError as e:
            await self._session.rollback()
            compile_error_handler(e)
            raise DBALCreateException(e)

        except IntegrityError as e:
            await self._session.rollback()
            integrity_error_handler(e, self._session)
            raise DBALCreateException(e)

        except ProgrammingError as e:
            await self._session.rollback()
            raise DBALUnexpectedValueTypeException(e)

        except Exception as e:
            await self._session.rollback()
            raise DBALCreateException(e)

        return new_obj

    async def bulk_create(self, data: list[dict]) -> Result[Any]:
        try:
            new_objects = await self._session.execute(self._stmt_bulk_insert(), data)
        except (IntegrityError, ProgrammingError) as e:
            raise DBALCreateException(e)

        return new_objects

    async def read(self, id: Any) -> M:
        try:
            result = await self._session.scalars(self._stmt_read_by_id(id))
            return result.one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)

    async def bulk_read(self, ids: list[Any]) -> Sequence[M]:
        return await self.read_filtered_list(id=ids)

    async def read_all(self) -> Sequence[M]:
        result = await self._session.scalars(self._stmt_read_all())
        return result.all()

    async def read_filtered(self, **kwargs) -> M:
        try:
            result = await self._session.scalars(self._stmt_read_filtered(**kwargs))
            return result.one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)
        except MultipleResultsFound as e:
            raise DBALMultipleResultsFoundException(e)

    async def read_filtered_list(
        self, sort_order: Literal['asc', 'desc'] = 'asc', sort_field: str | None = None, **kwargs
    ) -> Sequence[M]:
        stmt = self._stmt_read_filtered_list(sort_order=sort_order, sort_field=sort_field, **kwargs)
        result = await self._session.scalars(stmt)
        return result.all()

    async def update(self, id: Any, **data) -> M:
        try:
            result = await self._session.scalars(self._stmt_update(id, **data))
            obj = result.one()

        except CompileError as e:
            compile_error_handler(e)
            raise DBALUpdateException(e)

        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)

        except IntegrityError as e:
            await self._session.rollback()
            integrity_error_handler(e, self._session)
            raise DBALUpdateException(e)

        except ProgrammingError as e:
            await self._session.rollback()
            raise DBALUnexpectedValueTypeException(e)

        except Exception as e:
            await self._session.rollback()
            raise DBALUpdateException(e)

        return obj

    async def bulk_update(self, data: list[dict]) -> None:
        try:
            await self._session.execute(update(self._model), data)
        except ProgrammingError as e:
            raise DBALUpdateException(e)
        except StaleDataError as e:
            raise DBALObjectNotFoundException(e)

    async def delete(self, id: Any) -> None:
        await self._session.execute(self._stmt_delete(id))

    async def bulk_delete(self, ids: list[Any]) -> None:
        await self._session.execute(self._stmt_bulk_delete(ids))
