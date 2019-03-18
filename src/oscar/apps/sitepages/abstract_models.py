from django.db import models

from oscar.core.blocks import (
    ImageBlock, HeadingBlock, BlockQuote, TableBlock,
    ProductChooserBlock, ProductListBlock
)

from wagtail.core.blocks import RichTextBlock
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.images.blocks import ImageChooserBlock


class AbstractArticlePage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftBarPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftBarNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftRightBarNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractArticleLeftRightBarPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True


class AbstractBlankShopPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('table', TableBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

    class Meta:
        abstract = True
