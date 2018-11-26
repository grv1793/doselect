# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-25 11:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import document.file_validator
import document.utils


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=256, upload_to=document.utils.generate_file_path, validators=[document.file_validator.FileValidator()])),
                ('date_uploaded', models.DateTimeField(auto_now_add=True, verbose_name='Date uploaded')),
                ('document_type', models.ForeignKey(help_text='Document type like Registration Certificate, Licence, etc..', on_delete=django.db.models.deletion.PROTECT, to='document.DocumentType')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Document',
                'verbose_name_plural': 'User Documents',
            },
        ),
    ]