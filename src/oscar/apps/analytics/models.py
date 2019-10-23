from oscar.apps.analytics.abstract_models import (
    AbstractPageView, AbstractProductRecord, AbstractUserProductView,
    AbstractUserRecord, AbstractUserSearch, AbstractVisitor)
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('analytics', 'PageView'):
    class PageView(AbstractPageView):
        pass

    __all__.append('PageView')


if not is_model_registered('analytics', 'ProductRecord'):
    class ProductRecord(AbstractProductRecord):
        pass

    __all__.append('ProductRecord')


if not is_model_registered('analytics', 'UserRecord'):
    class UserRecord(AbstractUserRecord):
        pass

    __all__.append('UserRecord')


if not is_model_registered('analytics', 'UserProductView'):
    class UserProductView(AbstractUserProductView):
        pass

    __all__.append('UserProductView')


if not is_model_registered('analytics', 'UserSearch'):
    class UserSearch(AbstractUserSearch):
        pass

    __all__.append('UserSearch')


if not is_model_registered('analytics', 'Visitor'):
    class Visitor(AbstractVisitor):
        pass

    __all__.append('Visitor')
