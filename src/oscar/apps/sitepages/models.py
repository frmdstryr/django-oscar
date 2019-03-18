from oscar.apps.sitepages.abstract_models import (
    AbstractArticlePage, AbstractArticleNoNavPage,
    AbstractArticleLeftBarPage, AbstractArticleLeftBarNoNavPage,
    AbstractArticleLeftRightBarPage, AbstractArticleLeftRightBarNoNavPage,
    AbstractBlankShopPage
)
from oscar.core.loading import is_model_registered

__all__ = []

if not is_model_registered('sitepages', 'ArticlePage'):
    class ArticlePage(AbstractArticlePage):
        pass

    __all__.append('ArticlePage')


if not is_model_registered('sitepages', 'ArticleNoNavPage'):
    class ArticleNoNavPage(AbstractArticleNoNavPage):
        pass

    __all__.append('ArticleNoNavPage')


if not is_model_registered('sitepages', 'ArticleLeftBarNoNavPage'):
    class ArticleLeftBarNoNavPage(AbstractArticleLeftBarNoNavPage):
        pass

    __all__.append('ArticleLeftBarNoNavPage')


if not is_model_registered('sitepages', 'ArticleNoNavPage'):
    class ArticleNoNavPage(AbstractArticleNoNavPage):
        pass

    __all__.append('ArticleNoNavPage')


if not is_model_registered('sitepages', 'ArticleLeftRightBarNoNavPage'):
    class ArticleLeftRightBarNoNavPage(AbstractArticleLeftRightBarNoNavPage):
        pass

    __all__.append('ArticleLeftRightBarNoNavPage')


if not is_model_registered('sitepages', 'ArticleLeftRightBarNoNavPage'):
    class ArticleLeftRightBarNoNavPage(AbstractArticleLeftRightBarNoNavPage):
        pass

    __all__.append('ArticleLeftRightBarNoNavPage')


if not is_model_registered('sitepages', 'BlankShopPage'):
    class BlankShopPage(AbstractBlankShopPage):
        pass

    __all__.append('BlankShopPage')
