# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-11 12:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisation', '0011_picture'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='companylink',
            options={'ordering': ('linktype', 'id')},
        ),
        migrations.AddField(
            model_name='companydescription',
            name='shorttext',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
