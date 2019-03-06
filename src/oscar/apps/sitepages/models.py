from django.db import models

from oscar.core.blocks import (
    ImageBlock, HeadingBlock, BlockQuote, ProductChooserBlock, ProductListBlock
)
from wagtail.core.blocks import RichTextBlock
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.images.blocks import ImageChooserBlock


class ArticlePage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]


class ArticleLeftBarPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]


class ArticleLeftBarNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]


class ArticleNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]


class ArticleLeftRightBarNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]


class ArticleLeftRightNoNavPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

class BlankShopPage(Page):
    body = StreamField([
        ('heading', HeadingBlock()),
        ('paragraph', RichTextBlock()),
        ('image', ImageBlock()),
        ('product', ProductChooserBlock()),
        ('product_list', ProductListBlock()),
    ])

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]
