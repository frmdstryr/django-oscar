# Generated by Django 2.1.1 on 2018-09-14 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0005_auto_20180914_1626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='dashboard_editor_context_menu',
            field=models.CharField(blank=True, default='copy cut paste link', max_length=255),
        ),
    ]
