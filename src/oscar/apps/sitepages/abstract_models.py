from django.db import models

from oscar.core.blocks import (
    ImageBlock, HeadingBlock, BlockQuote, TableBlock, ListBlock, CharBlock,
    ProductChooserBlock, ProductListBlock
)

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import RichTextBlock, RawHTMLBlock, PageChooserBlock
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock


DEFAULT_BLOCKS = [
    ('heading', HeadingBlock()),
    ('paragraph', RichTextBlock()),
    ('image', ImageBlock()),
    ('table', TableBlock()),
    ('list', ListBlock(CharBlock(label="Item"))),
    ('pages', ListBlock(PageChooserBlock(required=False))),
    ('documents', ListBlock(DocumentChooserBlock(required=False))),
    ('products', ProductListBlock()),
    ('html', RawHTMLBlock()),
]


class AbstractLandingPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticlePage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftBarPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftBarNoNavPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleNoNavPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftRightBarNoNavPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftRightBarPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractBlankShopPage(Page):
    body = StreamField(DEFAULT_BLOCKS)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True
