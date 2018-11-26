from datetime import date
from django.conf import settings
import json
import logging
import random
import string
from datetime import timedelta, datetime

MEDIA_UPLOAD_STRUCTURE = getattr(
    settings, "MEDIA_UPLOAD_STRUCTURE", ""
)

doc_code = 'user_doc'

def encode_day(nday, size, chars):
    a = nday
    nday_enc = []

    while a:
        nday_enc.append(a % size)
        a = int(a / size)

    encoded = ''.join([chars[x] for x in reversed(nday_enc)])
    return encoded


def get_unique_friendly_id(prefix=None):
    chars = string.digits + string.ascii_uppercase
    size = len(chars)
    year = 2015
    friendly_id = None
    reference_date = datetime(year, 1, 1)
    now = datetime.now()
    delta = now - reference_date
    days_since = delta.days
    day = encode_day(days_since, size, chars)
    for size in [3, 4]:
        for i in range(5):
            code = ''.join(random.sample(chars, size))
            friendly_id = day + code

    if prefix:
        friendly_id = prefix + '-' + friendly_id

    return friendly_id.upper()


def generate_file_path(instance, filename):
    """
    Returns the file path as per the defined directory structure.
    """

    doc_code = instance.document_type.code.replace(" ", "_") if hasattr(instance, "document_type") else ""
    module_name = instance._meta.app_label
    instance_label = instance._meta.object_name.lower().replace("document", "")
    if hasattr(instance, instance_label+"_id"):
        instance_handle = instance_label + "_" + str(getattr(instance, instance_label+"_id"))
    else:
        instance_handle = instance_label + "_" + str(instance.id)

    file_name = str(date.today()) + "/" + get_unique_friendly_id() + "/" + filename.upper()

    return MEDIA_UPLOAD_STRUCTURE.format(
        module_name=module_name,
        instance_handle=instance_handle,
        doc_code=doc_code,
        file_name=file_name
    ).replace("//", "/")
