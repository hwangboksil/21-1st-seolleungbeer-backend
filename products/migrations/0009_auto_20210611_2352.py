# Generated by Django 2.2.12 on 2021-06-11 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_merge_20210611_2349'),
    ]

    operations = [

        migrations.AddField(
            model_name='subcategory',
            name='korean_name',
            field=models.CharField(max_length=50, null=True, unique=True),
        ),
    ]
