# Generated by Django 2.2.9 on 2020-07-26 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_auto_20200626_2325'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date'], 'verbose_name': 'Пост', 'verbose_name_plural': 'Посты'},
        ),
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(max_length=600, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='Номер'),
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Тайтл'),
        ),
    ]
