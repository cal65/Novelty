# Generated by Django 3.2.6 on 2022-10-02 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goodreads', '0006_auto_20220714_0513'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='exportdata',
            constraint=models.UniqueConstraint(fields=('book_id', 'username'), name='book_per_user'),
        ),
    ]