# Generated by Django 3.2.6 on 2024-07-24 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goodreads', '0012_lists'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookslists',
            name='rank',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
