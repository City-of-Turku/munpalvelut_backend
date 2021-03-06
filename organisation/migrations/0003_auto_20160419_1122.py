# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-19 11:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organisation', '0002_auto_20160414_1115'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lang', models.CharField(max_length=3)),
                ('text', models.TextField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='description', to='organisation.Company')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='companydescription',
            unique_together=set([('company', 'lang')]),
        ),
    ]
