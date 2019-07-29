# Generated by Django 2.2rc1 on 2019-03-25 16:45

from django.db import migrations
import oscar.core.blocks
import wagtail.contrib.table_block.blocks
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.documents.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0041_group_collection_permissions_verbose_name_plural'),
        ('wagtailredirects', '0006_redirect_increase_max_length'),
        ('wagtailforms', '0003_capitalizeverbose'),
        ('wagtailmenus', '0022_auto_20170913_2125'),
        ('sitepages', '0004_articleleftrightbarnonavpage_articleleftrightnonavpage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articleleftrightnonavpage',
            name='page_ptr',
        ),
        migrations.AlterField(
            model_name='articleleftbarnonavpage',
            name='body',
            field=wagtail.core.fields.StreamField([('heading', wagtail.core.blocks.StructBlock([('heading_text', wagtail.core.blocks.CharBlock(classname='title', required=True)), ('size', wagtail.core.blocks.ChoiceBlock(blank=True, choices=[('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')], required=False))])), ('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('caption', wagtail.core.blocks.CharBlock(required=False)), ('attribution', wagtail.core.blocks.CharBlock(required=False))])), ('table', wagtail.contrib.table_block.blocks.TableBlock()), ('list', wagtail.core.blocks.ListBlock(wagtail.core.blocks.CharBlock(label='Item'))), ('pages', wagtail.core.blocks.ListBlock(wagtail.core.blocks.PageChooserBlock(required=False))), ('documents', wagtail.core.blocks.ListBlock(wagtail.documents.blocks.DocumentChooserBlock(required=False))), ('products', oscar.core.blocks.ProductListBlock()), ('html', wagtail.core.blocks.RawHTMLBlock())]),
        ),
        migrations.AlterField(
            model_name='articleleftrightbarnonavpage',
            name='body',
            field=wagtail.core.fields.StreamField([('heading', wagtail.core.blocks.StructBlock([('heading_text', wagtail.core.blocks.CharBlock(classname='title', required=True)), ('size', wagtail.core.blocks.ChoiceBlock(blank=True, choices=[('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')], required=False))])), ('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('caption', wagtail.core.blocks.CharBlock(required=False)), ('attribution', wagtail.core.blocks.CharBlock(required=False))])), ('table', wagtail.contrib.table_block.blocks.TableBlock()), ('list', wagtail.core.blocks.ListBlock(wagtail.core.blocks.CharBlock(label='Item'))), ('pages', wagtail.core.blocks.ListBlock(wagtail.core.blocks.PageChooserBlock(required=False))), ('documents', wagtail.core.blocks.ListBlock(wagtail.documents.blocks.DocumentChooserBlock(required=False))), ('products', oscar.core.blocks.ProductListBlock()), ('html', wagtail.core.blocks.RawHTMLBlock())]),
        ),
        migrations.AlterField(
            model_name='articlenonavpage',
            name='body',
            field=wagtail.core.fields.StreamField([('heading', wagtail.core.blocks.StructBlock([('heading_text', wagtail.core.blocks.CharBlock(classname='title', required=True)), ('size', wagtail.core.blocks.ChoiceBlock(blank=True, choices=[('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')], required=False))])), ('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('caption', wagtail.core.blocks.CharBlock(required=False)), ('attribution', wagtail.core.blocks.CharBlock(required=False))])), ('table', wagtail.contrib.table_block.blocks.TableBlock()), ('list', wagtail.core.blocks.ListBlock(wagtail.core.blocks.CharBlock(label='Item'))), ('pages', wagtail.core.blocks.ListBlock(wagtail.core.blocks.PageChooserBlock(required=False))), ('documents', wagtail.core.blocks.ListBlock(wagtail.documents.blocks.DocumentChooserBlock(required=False))), ('products', oscar.core.blocks.ProductListBlock()), ('html', wagtail.core.blocks.RawHTMLBlock())]),
        ),
        migrations.AlterField(
            model_name='articlepage',
            name='body',
            field=wagtail.core.fields.StreamField([('heading', wagtail.core.blocks.StructBlock([('heading_text', wagtail.core.blocks.CharBlock(classname='title', required=True)), ('size', wagtail.core.blocks.ChoiceBlock(blank=True, choices=[('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')], required=False))])), ('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('caption', wagtail.core.blocks.CharBlock(required=False)), ('attribution', wagtail.core.blocks.CharBlock(required=False))])), ('table', wagtail.contrib.table_block.blocks.TableBlock()), ('list', wagtail.core.blocks.ListBlock(wagtail.core.blocks.CharBlock(label='Item'))), ('pages', wagtail.core.blocks.ListBlock(wagtail.core.blocks.PageChooserBlock(required=False))), ('documents', wagtail.core.blocks.ListBlock(wagtail.documents.blocks.DocumentChooserBlock(required=False))), ('products', oscar.core.blocks.ProductListBlock()), ('html', wagtail.core.blocks.RawHTMLBlock())]),
        ),
        migrations.AlterField(
            model_name='blankshoppage',
            name='body',
            field=wagtail.core.fields.StreamField([('heading', wagtail.core.blocks.StructBlock([('heading_text', wagtail.core.blocks.CharBlock(classname='title', required=True)), ('size', wagtail.core.blocks.ChoiceBlock(blank=True, choices=[('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4')], required=False))])), ('paragraph', wagtail.core.blocks.RichTextBlock()), ('image', wagtail.core.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('caption', wagtail.core.blocks.CharBlock(required=False)), ('attribution', wagtail.core.blocks.CharBlock(required=False))])), ('table', wagtail.contrib.table_block.blocks.TableBlock()), ('list', wagtail.core.blocks.ListBlock(wagtail.core.blocks.CharBlock(label='Item'))), ('pages', wagtail.core.blocks.ListBlock(wagtail.core.blocks.PageChooserBlock(required=False))), ('documents', wagtail.core.blocks.ListBlock(wagtail.documents.blocks.DocumentChooserBlock(required=False))), ('products', oscar.core.blocks.ProductListBlock()), ('html', wagtail.core.blocks.RawHTMLBlock())]),
        ),
        migrations.DeleteModel(
            name='ArticleLeftBarPage',
        ),
        migrations.DeleteModel(
            name='ArticleLeftRightNoNavPage',
        ),
    ]