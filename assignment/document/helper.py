from datetime import date
from django.conf import settings
import json
import string
import base64
from datetime import timedelta

from rest_framework import exceptions

from document.models import DocumentType


IST_OFFSET_HOURS = 5.5
DATE_FORMAT = "%Y-%m-%d"


def get_doc_type(doc_name):
    try:
        return DocumentType.objects.get(name=doc_name)
    except DocumentType.DoesNotExist:
        raise exceptions.NotFound('Invalid Document name!!!')


def get_base64_encoded_string(file_path):
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string


def get_document_data(doc):
    doc_data = {}
    if not bool(doc.filename):
        return doc_data

    encoded_string = get_base64_encoded_string(str(doc.filename.url)[1:])

    doc_data['encoded_content'] = encoded_string
    doc_data['extension'] = doc.extension
    doc_data['doc_type'] = str(doc.document_type)
    doc_data['id'] = doc.id
    doc_data['date_uploaded'] = (doc.date_uploaded + timedelta(
        hours=IST_OFFSET_HOURS)).strftime(DATE_FORMAT)

    return doc_data
