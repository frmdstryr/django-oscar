# Generated by Django 2.1.1 on 2018-09-27 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0007_configuration_shop_logo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='shop_logo',
            field=models.ImageField(default='img/ui/image_not_found.jpg', max_length=255, upload_to='images/promotions/'),
        ),
    ]
