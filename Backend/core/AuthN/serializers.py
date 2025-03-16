from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, SystemOwnerProfile, OrganizationProfile, AdminProfile, UserProfile


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash password
        return CustomUser.objects.create(**validated_data)


# System Owner Profile Serializer
class SystemOwnerProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = SystemOwnerProfile
        fields = ['id', 'user', 'company_name']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'system_owner'
        user = CustomUser.objects.create_user(**user_data)
        return SystemOwnerProfile.objects.create(user=user, **validated_data)


# Organization Profile Serializer (FK to System Owner)
class OrganizationProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    system_owner = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = OrganizationProfile
        fields = ['id', 'user', 'organization_name', 'system_owner']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'organization'
        user = CustomUser.objects.create_user(**user_data)
        return OrganizationProfile.objects.create(user=user, **validated_data)


# Admin Profile Serializer (FK to Organization)
class AdminProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    organization = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = AdminProfile
        fields = ['id', 'user', 'admin_name', 'organization']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'admin'
        user = CustomUser.objects.create_user(**user_data)
        return AdminProfile.objects.create(user=user, **validated_data)


# User Profile Serializer (FK to Admin)
class UserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    admin = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'user_name', 'admin']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'user'
        user = CustomUser.objects.create_user(**user_data)
        return UserProfile.objects.create(user=user, **validated_data)
