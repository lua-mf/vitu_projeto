# Generated by Django 5.0.4 on 2024-05-20 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0010_ordemservico_anotacoes_internas_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordemservico',
            name='numero',
            field=models.CharField(default=1, max_length=10, unique=True),
            preserve_default=False,
        ),
    ]
