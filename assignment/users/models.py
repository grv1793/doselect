# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.db import models

# Create your models here.
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.core.mail import send_mail
from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.sessions.models import SessionManager, Session

from rest_framework import status
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from document.models import Document


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

class UserManager(BaseUserManager):

    """
    Custom manager for blowhorn user
    """

    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Create and Save an User with email and password
            :param str email: user email
            :param str password: user password
            :param bool is_staff: whether user staff or not
            :param bool is_superuser: whether user admin or not
            :return users.models.User user: user
            :raise ValueError: email is not set
        """
        now = timezone.now()

        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)

        is_active = extra_fields.pop("is_active", False)

        user = self.model(email=email, is_staff=is_staff, is_active=is_active,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save an User with the given email and password.
        :param str email: user email
        :param str password: user password
        :return users.models.User user: admin user
        """
        return self._create_user(email, password, True, True, is_active=True,
                                 **extra_fields)

    def _set_response(self, is_success, _status, message):
        return {
            'is_success': is_success,
            'status': _status,
            'message': message
        }

    def do_login(self, request, email, password, **extra_fields):
        """
            Returns the JWT token in case of success, returns the error response in case of login failed.
        """
        user = authenticate(email=email, password=password)

        if not user or not user.is_active:
            return False

        login(request, user)
        token = self.generate_auth_token(user)

        message = {
            'token': token,
            'user': user
        }
        return message

    def generate_auth_token(self, user):
        # Generating the JWT Token
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return token


class UserDocument(Document):
    user = models.ForeignKey('users.User', related_name='user_documents', on_delete=models.PROTECT)
    class Meta:
        verbose_name = _('User Document')
        verbose_name_plural = _('User Documents')


class User(AbstractBaseUser, PermissionsMixin):
    """
    Blowhorn user does not have the username field
    It uses email as USERNAME_FIELD for authentication
    The following attributes are inherited from the superclasses:
        * password
        * last_login
        * is_superuser
    """

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(
        _('Name of User'), blank=True, max_length=255, db_index=True)

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True
    )

    is_staff = models.BooleanField(
        _('staff status'), default=False, help_text=_(
            'Designates whether the user can log into this admin site.'))

    is_active = models.BooleanField(_('active'), default=False, help_text=_(
        'Designates whether this user should be treated as '
        'active. Unselect this instead of deleting accounts.'))

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def is_staff_user(self):
        """
        Check if user is staff. Returns `true` on success, otherwise `false`.
        """

        return self.is_staff

    def is_active_user(self):
        """
        Check if user is active. Returns `true` on success, otherwise `false`.
        """

        return self.is_active


class UserSessionManager(SessionManager):

    def is_valid_key(self, request):
        """
        :param request: django request
        :returns: boolean
        """
        user = request.user
        token = request.data.get('access_key', None)
        current_session = self.get_session_using_token(token)

        ''' Below query is added to remove multiple devices which are (may be)
            already logged in whose session data not available in UserSession.
            This query can be changed to get a single session after some period
            of time.
        '''
        session_keys = list(self.get_session_keys_using_user(user, token))
        if not current_session and len(session_keys) > 0:
            logout(request)
            return False
        return True

    def get_session_using_token(self, token):
        """
        :param token: jwt token (string)
        :returns: Django session of given token (instance)
        """
        session = None
        try:
            session = UserSession.objects.get(token=token)
        except UserSession.DoesNotExist:
            logging.info('Session doesn\'t exists')
        return session

    def get_session_using_session_key(self, session_key):
        session = None
        try:
            session = UserSession.objects.get(session_key=session_key)
        except UserSession.DoesNotExist:
            logging.info('Session doesn\'t exists')
        return session

    def get_session_keys_using_user(self, user, token):
        """
        :param user: instance of User,
        :param token: jwt token (string)
        :returns: Django session keys of given user excluding given token
        """
        return UserSession.objects.filter(Q(user=user) &
                ~Q(token=token)).values_list('session_key', flat=True)

    def remove_sessions_using_session_keys(self, session_keys):
        """
        :param session_keys: list of session_keys
        :returns: count of removed sessions
        """
        return UserSession.objects.filter(
            session_key__in=list(session_keys)).delete()

    def remove_session_using_token(self, token):
        """
        :param token: token (string)
        :returns: count of deleted sessions
        """
        return UserSession.objects.filter(token=token).delete()

    def remove_django_sessions(self, session_keys):
        """
        :param session_keys: session_keys (list)
        :returns: number of deleted django sessions
        """
        sessions = None
        if session_keys:
            sessions = Session.objects.filter(
                session_key__in=list(session_keys)
            ).delete()
        return sessions


class UserSession(models.Model):
    session_key = models.CharField(_('Session Key'), max_length=40,
                                   primary_key=True)
    user = models.ForeignKey(User, related_name='session_user',
                             on_delete=models.PROTECT)
    token = models.CharField(_('Token'), max_length=255, unique=True)

    objects = UserSessionManager()

    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')

    def __str__(self):
        return '%s: %s' % (self.session_key, self.user)
