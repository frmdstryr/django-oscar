# Generated by Django 2.1.1 on 2018-11-29 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0008_auto_20181115_1953'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbsoluteDiscountPerUnitBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Absolute discount per unit benefit',
                'verbose_name_plural': 'Absolute discount per unit benefits',
                'proxy': True,
                'indexes': [],
            },
            bases=('offer.absolutediscountbenefit',),
        ),
        migrations.AlterField(
            model_name='benefit',
            name='type',
            field=models.CharField(blank=True, choices=[('Percentage', "Discount is a percentage off of the product's value"), ('Absolute', "Discount is a fixed amount off of the product's value"), ('Discount per unit', "Discount is a fixed amount off of the product's value per unit"), ('Multibuy', 'Discount is to give the cheapest product for free'), ('Fixed price', 'Get the products that meet the condition for a fixed price'), ('Shipping absolute', 'Discount is a fixed amount of the shipping cost'), ('Shipping fixed price', 'Get shipping for a fixed price'), ('Shipping percentage', 'Discount is a percentage off of the shipping cost')], max_length=128, verbose_name='Type'),
        ),
    ]
