# Generated by Django 2.1.1 on 2018-09-14 20:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0004_auto_20180914_1626'),
    ]

    operations = [
        migrations.RenameField(
            model_name='configuration',
            old_name='dashboard_editor_menubar_layout',
            new_name='dashboard_editor_menubar',
        ),
    ]
