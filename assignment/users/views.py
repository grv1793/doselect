# -*- coding: utf-8 -*-
import json
import os
import base64
import operator
from functools import reduce
from django.db import transaction
from django.db.models import Q
from django.core.files.base import ContentFile
from django.conf import settings

from rest_framework import generics, status, exceptions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.authentication import BasicAuthentication

from users.services.login import LogIn
from users.models import UserDocument
from document.models import DocumentType
from users.permission import HasValidKey
from users.helper import get_user_doc
from document.helper import get_doc_type, get_document_data, get_base64_encoded_string


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

    def post(self, request):
        """POST method for user login changes."""
        data = request.data

        login_class = LogIn(request, data)
        response, status_code = login_class._login()

        return Response(status=status_code, data=response)


class DocumentList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, HasValidKey)
    authentication_classes = (BasicAuthentication, )

    def get_documents_data(self, docs):
        data = []
        for doc in docs:
            doc_data = get_document_data(doc)
            data.append(doc_data) if doc_data else None
        return data

    def get(self, request):
        response_data = ''
        status_code = status.HTTP_200_OK

        # method 1
        # response_data = self.get_from_db()

        # method 2
        response_data = self.get_from_filesystem()

        return Response(status=status_code, data=response_data)

    def get_from_db(self):
        docs = self.get_queryset()
        return self.get_documents_data(docs)

    def get_from_filesystem(self):
        doc_path = str(os.path.join(settings.DOCUMENTS_DIR, 'users'))
        doc_path = str(os.path.join(doc_path, 'user_%s' % str(self.request.user.id)))
        doc_files = []
        base_dir_length = len(settings.BASE_DIR)
        for path, subdirs, files in os.walk(doc_path):
            for name in files:
                doc_id, extension = name.split('.')
                doc_data = {'id': int(doc_id), 'extension': extension}
                file_path = os.path.join(path, name)[base_dir_length + 1:].replace("\\", "/")
                doc_data['encoded_content'] = get_base64_encoded_string(file_path)
                doc_files.append(doc_data)
        return doc_files

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
            doc_type = get_doc_type(doc_name)
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

        document_type = get_doc_type(document_name)

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


class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, HasValidKey)
    authentication_classes = (BasicAuthentication, )

    def get(self, request, pk):
        response_data = ''
        status_code = status.HTTP_200_OK

        image = get_user_doc(pk)
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

        document_type = get_doc_type(document_name)
        user_doc = get_user_doc(pk)

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
        user_doc = get_user_doc(pk)
        user_doc.filename.delete()
        user_doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
