# Generated by Django 4.1.7 on 2023-04-13 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_book_isbn_alter_book_author_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.CharField(max_length=30),
        ),
    ]
