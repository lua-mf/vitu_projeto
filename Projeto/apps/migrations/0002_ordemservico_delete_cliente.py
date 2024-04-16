# Generated by Django 5.0.4 on 2024-04-16 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrdemServico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_completo', models.CharField(max_length=255)),
                ('cpf', models.CharField(max_length=14)),
                ('data_nascimento', models.DateField()),
                ('contato', models.CharField(max_length=15)),
                ('aparelho', models.CharField(max_length=225)),
                ('garantia', models.BooleanField()),
                ('descricao_problema', models.TextField()),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('senha', models.CharField(max_length=255)),
            ],
        ),
        migrations.DeleteModel(
            name='Cliente',
        ),
    ]
