# Generated by Django 2.2rc1 on 2019-03-25 16:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('promotions', '0004_auto_20190206_1950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ForeignKey(max_length=255, on_delete=django.db.models.deletion.PROTECT, to='images.OscarImage'),
        ),
    ]