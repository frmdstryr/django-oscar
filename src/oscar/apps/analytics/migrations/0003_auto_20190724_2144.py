# Generated by Django 2.2 on 2019-07-25 01:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_auto_20140827_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersearch',
            name='result_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='usersearch',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
