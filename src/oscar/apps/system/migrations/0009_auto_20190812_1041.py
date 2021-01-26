# Generated by Django 2.2 on 2019-08-12 14:41

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0041_group_collection_permissions_verbose_name_plural'),
        ('system', '0008_auto_20180927_1628'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='configuration',
            name='dashboard_editor_context_menu',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='dashboard_editor_menubar',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='dashboard_editor_plugins',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='dashboard_editor_toolbar_layout',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='shop_date_picker_minute_step',
        ),
        migrations.AddField(
            model_name='configuration',
            name='shop_email',
            field=models.EmailField(default='sales@example.com', max_length=254),
        ),
        migrations.AddField(
            model_name='configuration',
            name='shop_logo_print',
            field=models.ImageField(default='img/ui/image_not_found.jpg', max_length=255, upload_to='images/promotions/'),
        ),
        migrations.AddField(
            model_name='configuration',
            name='shop_phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(default='1-800-799-9999', max_length=128),
        ),
        migrations.AddField(
            model_name='configuration',
            name='site',
            field=models.OneToOneField(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.Site'),
            preserve_default=False,
        ),
    ]