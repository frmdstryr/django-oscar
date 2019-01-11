# Generated by Django 2.1.1 on 2019-01-05 19:26

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0009_auto_20181129_1245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rangeproduct',
            name='display_order',
        ),
        migrations.AddField(
            model_name='rangeproduct',
            name='sort_order',
            field=models.IntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='benefit',
            name='range',
            field=modelcluster.fields.ParentalKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offer.Range', verbose_name='Range'),
        ),
        migrations.AlterField(
            model_name='condition',
            name='range',
            field=modelcluster.fields.ParentalKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offer.Range', verbose_name='Range'),
        ),
        migrations.AlterField(
            model_name='conditionaloffer',
            name='description',
            field=wagtail.core.fields.RichTextField(blank=True, help_text='This is displayed on the offer browsing page', verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='range',
            name='description',
            field=wagtail.core.fields.RichTextField(blank=True),
        ),
        migrations.AlterField(
            model_name='rangeproduct',
            name='range',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, to='offer.Range'),
        ),
        migrations.AlterField(
            model_name='rangeproductfileupload',
            name='range',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_uploads', to='offer.Range', verbose_name='Range'),
        ),
    ]
