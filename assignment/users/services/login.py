# Django and System libraries
import json
import logging
from django.conf import settings
from django.db.models import Q
from django.db import transaction

# 3rd party libraries
from rest_framework import status

# blowhorn imports
from users.models import User, UserSession
from users.serializers import UserSessionSerializer
from common.mixins import CreateModelMixin

class LogIn(object):
    """Driver Authentication is done here."""

    def __init__(self, request, data):
        self.request = request
        self.error_message = ''
        self.login_response = None
        self.response_data = None
        self.status_code = status.HTTP_200_OK

        self.email = data.get("email")
        self.password = data.get("password")

        if not (self.email and self.password):
            self.error_message = 'Invalid data sent'

    def _login(self):
        if self.error_message:
            return self.error_message, status.HTTP_400_BAD_REQUEST

        login_response = self._login_with_email()
        print(login_response)
        if not login_response:
            self.response_data = 'Invalid Credentials'
            self.status_code = status.HTTP_401_UNAUTHORIZED
        else:
            response = self._get_login_response(login_response)
            self.status_code = response.get('status')
            self.response_data = response.get('message')
        return self.response_data, self.status_code

    def _login_with_email(self):

        return User.objects.do_login(
            request=self.request,
            email=self.email,
            password=self.password
        )

    def _get_login_response(self, login_response):
        with transaction.atomic():
            user = login_response.get('user')
            token = login_response.get('token')

            current_session_key = self.request.session.session_key
            session_keys = list(UserSession.objects.get_session_keys_using_user(user, token))
            UserSession.objects.remove_sessions_using_session_keys(session_keys)
            UserSession.objects.remove_django_sessions(session_keys)
            self._save_user_session(user.pk, current_session_key, token)

            response = {"access_key": token}
            return {
                'status': status.HTTP_200_OK,
                'message': response
            }

    def _save_user_session(self, user_id, current_session_key, token):
        session_data = {
            'user': user_id,
            'session_key': current_session_key,
            'token': token
        }
        CreateModelMixin().create(data=session_data, serializer_class=UserSessionSerializer)
