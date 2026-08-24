from spilli_dbal.exc import SpillDBALError


class DBALException(SpillDBALError):
    """Main exception for DBAL."""


class DBALCreateException(DBALException):
    """Exception for create methods."""


class DBALObjectNotFoundException(DBALException):
    """Exception for read methods."""


class DBALColumnNonExistException(DBALException):
    """Exception if the column is not in the table."""


class DBALUnexpectedValueTypeException(DBALException):
    """Exception for unexpected value type."""


class DBALNotNullConstraintFailedException(DBALException):
    """Exception NOT NULL constraint failed."""


class DBALForeignKeyConstraintFailedException(DBALException):
    """Exception FOREIGN KEY constraint failed."""


class DBALUpdateException(DBALException):
    """Exception for update methods."""


class DBALPaginateException(DBALException):
    """Exception for paginate mixin."""
