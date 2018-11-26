from rest_framework import serializers
from users.models import UserSession

class UserSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserSession
        fields = '__all__'