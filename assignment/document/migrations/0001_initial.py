# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-25 10:22
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Document name like Registration Certificate, Licence, etc..', max_length=64, unique=True, verbose_name='Document Type')),
                ('code', models.CharField(help_text='Short name for document. RC for Registration Certificate, etc..', max_length=25, validators=[django.core.validators.RegexValidator(message='Code can only contain the letters a-z, A-Z and underscore', regex=b'^[a-zA-Z_][a-zA-Z_]+$')], verbose_name='Document Code')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('identifier', models.CharField(choices=[(b'profile_photo', 'Profile Photo'), (b'uploaded_photo', 'Uploaded Photo'), (b'not_specified', 'Not Specified')], default=b'not_specified', max_length=100, verbose_name='Document Identifier')),
            ],
            options={
                'verbose_name': 'Document Type',
                'verbose_name_plural': 'Document Types',
            },
        ),
    ]
