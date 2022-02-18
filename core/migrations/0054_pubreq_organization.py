# Generated by Django 3.2.10 on 2022-02-02 22:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0053_auto_20220202_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='pubreq',
            name='organization',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='pubreqs', to='core.organization'),
            preserve_default=False,
        ),
    ]