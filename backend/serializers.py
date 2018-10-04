from django.contrib.auth import get_user_model
from rest_framework import serializers

from webapp.models import *

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone', 'last_login', 'first_login', 'is_staff', 'is_superuser')


# Allows to get a user using only their ID
class UserSingleSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone')


class UserEditSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=255, required=False)
    new_password = serializers.CharField(max_length=255, required=False)
    new_password_confirmation = serializers.CharField(max_length=255, required=False)
    first_login = serializers.BooleanField(required=False)
    phone = serializers.RegexField(regex=r'^\+?1?\d{9,15}$', required=False)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            'id', 'title', 'start_date', 'end_date', 'winner_photo', 'start_location_id', 'end_location_id',
            'is_active',)


class EmergencyContactSerializer(serializers.Serializer):
    emergency_contact = serializers.RegexField(regex=r'^\+?1?\d{9,15}$')


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'is_disqualified', 'is_winner',)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'latitude', 'longitude')


class TeamLocationStopSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    location_id = serializers.IntegerField()


class ChallengeSubmitSerializer(serializers.Serializer):
    challenge_id = serializers.IntegerField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    picture = serializers.ImageField(required=False)
    base64_picture = serializers.CharField(required=False)


class ChallengeReviewSerializer(serializers.Serializer):
    challenge_id = serializers.IntegerField()
    team_id = serializers.IntegerField()


class ChallengeSubmissionDeletionSerializer(serializers.Serializer):
    challenge_id = serializers.IntegerField()
