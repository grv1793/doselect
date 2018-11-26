from django.db import models
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ImproperlyConfigured, ValidationError
from datetime import date, datetime

from document.file_validator import FileValidator
from document.utils import generate_file_path


@python_2_unicode_compatible
class DocumentType(models.Model):
    name = models.CharField(
        _("Document Type"),
        max_length=64,
        null=False,
        unique=True,
        help_text=_(
            "Document name like Registration Certificate, Licence, etc..")
    )
    code = models.CharField(
        _("Document Code"),
        max_length=25,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][a-zA-Z_]+$',
                message=_(
                    "Code can only contain the letters a-z, A-Z and underscore")
            )
        ],
        help_text=_(
            "Short name for document. RC for Registration Certificate, etc..")
    )
    creation_date = models.DateTimeField(_("Creation Date"), auto_now_add=True)

    USER_DOCUMENT = 'user_doc'
    DOCUMENT_NOT_SPECIFIED = 'not_specified'
    IDENTIFIERS = (
        (USER_DOCUMENT, _('User Document')),
        (DOCUMENT_NOT_SPECIFIED, _('Not Specified'))
    )

    identifier = models.CharField(
        _('Document Identifier'),
        default=DOCUMENT_NOT_SPECIFIED, max_length=100,
        choices=IDENTIFIERS)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Document Type")
        verbose_name_plural = _("Document Types")


@python_2_unicode_compatible
class Document(models.Model):
    filename = models.FileField(upload_to=generate_file_path, validators=[FileValidator()], max_length=256)
    document_type = models.ForeignKey(
        'document.DocumentType', on_delete=models.PROTECT,
        help_text=_("Document type like Registration Certificate, Licence, etc..")
    )
    extension = models.CharField(
        _("Document Extension"),
        max_length=10,
        null=False,
        blank=False,
        help_text=_(
            "Document extension like png, jpeg etc..")
    )
    date_uploaded = models.DateTimeField(_("Date uploaded"), auto_now_add=True)

    def __str__(self):
        return str(self.filename) if self.filename else str(self.id)

    class Meta:
        abstract = True
        app_label = "document"
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
