# -*- coding: utf-8 -*-
import json
import base64
import operator
from datetime import timedelta
from functools import reduce
from django.db.models import Q, F
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, status, exceptions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, views
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication

from users.services.login import LogIn
from users.models import UserDocument
from document.models import DocumentType
from users.permission import HasValidKey
from assignment.middleware import CsrfExemptSessionAuthentication

IST_OFFSET_HOURS = 5.5
DATE_FORMAT = "%Y-%m-%d"


@permission_classes([])
class Login(generics.CreateAPIView):
    """
    User Authentication to be done here.

    through 1. email + password

    Deletes all user sessions and django sessions.

    Saves the new session for user.

    POST(email, password)

    On Success: Returns User session token with 200 status
    On Failure: Returns 500 with the error.

    """

    authentication_classes = (BasicAuthentication)

    def post(self, request):
        """POST method for user login changes."""
        data = request.data

        login_class = LogIn(request, data)
        response, status_code = login_class._login()

        return Response(status=status_code, data=response)


class DocumentList(generics.ListCreateAPIView):
    permission_classes = (HasValidKey, )

    def get_document_data(self, docs):
        data = []
        for doc in docs:
            if not bool(doc.filename):
                continue
            doc_data = {}
            with open(str(doc.filename.url)[1:], "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())

            doc_data['encoded_content'] = encoded_string
            doc_data['extension'] = doc.extension
            doc_data['doc_type'] = str(doc.document_type)
            doc_data['id'] = doc.id
            doc_data['date_uploaded'] = (doc.date_uploaded + timedelta(
                hours=IST_OFFSET_HOURS)).strftime(DATE_FORMAT)
            data.append(doc_data)
        return data

    def get(self, request):
        response_data = ''
        status_code = status.HTTP_200_OK

        images = self.get_queryset()
        response_data = self.get_document_data(images)

        return Response(status=status_code, data=response_data)

    def get_queryset(self):
        query = self.get_query(self.request.query_params)
        return UserDocument.objects.filter(query).select_related('document_type')

    def get_query(self, params):
        doc_name = params.get('doc_name', None)
        extension = params.get('extension', None)
        start_date = params.get('start_date', None)
        end_date = params.get('end_date', None)

        query = [Q(user=self.request.user)]
        if doc_name:
            doc_type = self.get_doc_type(doc_name)
            query.append(Q(document_type=doc_type))
        if extension:
            query.append(Q(extension=extension))
        if start_date:
            query.append(Q(date_uploaded__date__gte=start_date))
        if end_date:
            query.append(Q(date_uploaded__date__lte=end_date))
        return reduce(operator.and_, query)


    def post(self, request):
        data = request.data
        response_data = 'Creation Success'
        status_code = status.HTTP_201_CREATED
        user = request.user
        doc_file = str(data.get('encoded_content', None))
        document_name = data.get('doc_type', None)
        extension = str(data.get('extension', None))

        if not doc_file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Invalid Data')

        document_type = self.get_doc_type(document_name)

        with transaction.atomic():
            user_doc = UserDocument.objects.create(**{
                'user_id': request.user.id,
                'document_type_id': document_type.id,
                'extension': extension
            })

            filename = '%s.%s' % (str(user_doc.id), extension)
            image_64_decode = base64.decodestring(doc_file)
            content = ContentFile(image_64_decode)
            user_doc.filename.save(filename, content, save=True)
            response_data = {
                'id': user_doc.id
            }

        return Response(status=status_code, data=response_data)

    def get_user_doc(self, pk):
        try:
            return UserDocument.objects.get(pk=pk)
        except UserDocument.DoesNotExist:
            raise exceptions.NotFound('Invalid User Document Id!!!')

    def get_doc_type(self, doc_name):
        try:
            return DocumentType.objects.get(name=doc_name)
        except DocumentType.DoesNotExist:
            raise exceptions.NotFound('Invalid Document name!!!')


class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (HasValidKey, )

    def get_document_data(self, doc):
        doc_data = {}
        if not bool(doc.filename):
            return doc_data
        with open(str(doc.filename.url)[1:], "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        doc_data['encoded_content'] = encoded_string
        doc_data['extension'] = doc.extension
        doc_data['doc_type'] = str(doc.document_type)
        doc_data['id'] = doc.id
        doc_data['date_uploaded'] = (doc.date_uploaded + timedelta(
            hours=IST_OFFSET_HOURS)).strftime(DATE_FORMAT)

        return doc_data

    def get(self, request, pk):
        response_data = ''
        status_code = status.HTTP_200_OK

        image = self.get_user_doc(pk)
        response_data = self.get_document_data(image)

        return Response(status=status_code, data=response_data)

    def patch(self, request, pk):
        data = request.data
        response_data = 'Updation Success'
        status_code = status.HTTP_200_OK
        user = request.user

        doc_file = str(data.get('encoded_content', None))
        document_name = data.get('doc_type', None)
        extension = str(data.get('extension', None))

        if not doc_file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Invalid Data')

        document_type = self.get_doc_type(document_name)
        user_doc = self.get_user_doc(pk)

        with transaction.atomic():
            user_doc.filename.delete()
            filename = '%s.%s' % (str(user_doc.id), extension)
            image_64_decode = base64.decodestring(doc_file)
            content = ContentFile(image_64_decode)
            user_doc.filename.save(filename, content, save=True)
            user_doc.extension = extension
            user_doc.save()
            response_data = {
                'id': user_doc.id
            }

        return Response(status=status_code, data=response_data)

    def delete(self, request, pk):
        user_doc = self.get_user_doc(pk)
        user_doc.filename.delete()
        user_doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_user_doc(self, pk):
        try:
            return UserDocument.objects.get(pk=pk)
        except UserDocument.DoesNotExist:
            raise exceptions.NotFound('Invalid User Document Id!!!')

    def get_doc_type(self, doc_name):
        try:
            return DocumentType.objects.get(name=doc_name)
        except DocumentType.DoesNotExist:
            raise exceptions.NotFound('Invalid Document name!!!')

