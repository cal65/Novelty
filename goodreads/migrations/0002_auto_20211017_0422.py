# Generated by Django 3.2.8 on 2021-10-17 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goodreads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='authors',
            name='ts_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='books',
            name='ts_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='exportdata',
            name='narrative',
            field=models.CharField(max_length=250, null=True),
        ),
    ]
