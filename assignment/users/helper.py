from rest_framework import exceptions

from users.models import UserDocument


def get_user_doc(pk):
    try:
        return UserDocument.objects.get(pk=pk)
    except UserDocument.DoesNotExist:
        raise exceptions.NotFound('Invalid User Document Id!!!')
