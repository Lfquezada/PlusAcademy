# Generated by Django 3.1.7 on 2021-05-22 17:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('usuarios', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Moneda',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.TextField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TipoPago',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.TextField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_pago', models.DateField(auto_now_add=True)),
                ('cantidad', models.IntegerField()),
                ('codigo_curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.curso')),
                ('moneda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pagos.moneda')),
                ('tipo_pago', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pagos.tipopago')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]