# Generated by Django 2.1.1 on 2018-09-11 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0013_auto_20170821_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_enabled',
            field=models.BooleanField(default=True, help_text='This flag indicates if this product is live and will be displayed or not', verbose_name='Is enabled?'),
        ),
    ]