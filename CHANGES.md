## Version 5.3.2

* Add raise specific exception for bad format parameters to `PageMixin`.

## Version 5.3.1

* Add handlers for specific errors.

## Version 5.3.0

* Create specific exceptions for errors.

## Version 5.2.2

* Add parameter sorting result for `read_filtered_list`.

## Version 5.2.1

* Fix count for paginate.

## Version 5.2.0

* Remove actions classes.

## Version 5.1.3

* Fix `paginate` method from `PageMixin`.

## Version 5.1.2

* Fix `BaseAction` and `BaseWebAction`.

## Version 5.1.1

* Fix delete methods to DBAL.

## Version 5.1.0

* Fix absolute imports.
* Add filtration methods to dbal.

## Version 5.0.0

* Complete redesign of the module architecture and the proposed approach to working with the database.
* Adding `Action` for independence from web frameworks.
* Add an access layer to work with the database - DBAL.
* Refactoring the method to obtain paginated results.
* Remove Python version 3.11.

## Version 4.3.0

* Add validate UTC timezone for datetime fields in `BaseSchema`.
* Remove Python version 3.9 and 3.10.

## Version 4.2.0

* Add method `.to_dict()` to `ModelMixin`.
* Add validate UTC timezone for datetime field in `ModelMixine`.

## Version 4.1.0

* Add bulk methods to `CreateMixin`, `ReadMixin`, `UpdateMixin` and `DeleteMixin` mixins.

## Version 4.0.0

* Add `Validation` decorators.

## Version 3.0.0

* Add method `paginate()` to `ReadMixin`.
* Change interface for methods `read()` from `ReadMixin`, `delete()` from `DeleteMixin`.

## Version 2.1.0

* `PaginateMixin` removed, this functional moved to `ReadMixin`.
* Add parameter `deserialize` to `CreateMixin`, `ReadMixin` and `UpdateMixin`.
* Improved docstrings.


## Version 2.0.0

* Refactoring of the module has been carried out. Improved class and method interfaces.

## Version 1.0.0

* Initial public release.
