from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import *
from ServiceShift.models import *
from ServiceWeekOff.models import *
from TaskControl.models import *
from Expenditure.models import * 
from django.db import transaction

class CustomUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)
    class Meta:
        model = BaseUserModel
        fields = ['id', 'email', 'username', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash password
        return BaseUserModel.objects.create(**validated_data)


# System Owner Profile Serializer
class SystemOwnerProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = SystemOwnerProfile
        fields = ['id', 'user', 'company_name']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'system_owner'
        user = BaseUserModel.objects.create_user(**user_data)
        return SystemOwnerProfile.objects.create(user=user, **validated_data)


# Organization Profile Serializer (FK to System Owner)
class OrganizationProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    system_owner = serializers.PrimaryKeyRelatedField(queryset=BaseUserModel.objects.all())

    class Meta:
        model = OrganizationProfile
        fields = ['id', 'user', 'organization_name', 'system_owner']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'organization'
        base_user = BaseUserModel.objects.create_user(**user_data)  # ✅ Create user

        # ✅ Create settings linked to this user
        OrganizationSettings.objects.create(organization=base_user)

        # ✅ Create and return the OrganizationProfile
        return OrganizationProfile.objects.create(user=base_user, **validated_data)
        
    


# Admin Profile Serializer (FK to Organization)
class AdminProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    organization = serializers.PrimaryKeyRelatedField(queryset=BaseUserModel.objects.all())

    class Meta:
        model = AdminProfile
        fields = ['id', 'user', 'admin_name', 'organization']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'admin'
        user = BaseUserModel.objects.create_user(**user_data)
        print(f"==>> validated_data: {validated_data}")
        # Create default ServiceShift
        admin_profile = AdminProfile.objects.create(user=user, **validated_data)
        ServiceShift.objects.create(admin=user,organization=admin_profile.organization)
        WeekOffPolicy.objects.create(admin=user,organization=admin_profile.organization)
        WeekOffPolicy.objects.create(admin=user,organization=admin_profile.organization)
        TaskType.objects.create(admin=user,organization=admin_profile.organization)
        ExpenseCategory.objects.create(admin=user,organization=admin_profile.organization)
        return admin_profile


class UserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    admin = serializers.PrimaryKeyRelatedField(queryset=BaseUserModel.objects.all())
    is_active = serializers.BooleanField(source='user.is_active', required=False)


    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = ['id']

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'user'
        user = BaseUserModel.objects.create_user(**user_data)

        admin_user = validated_data['admin']
        try:
            admin_profile = AdminProfile.objects.get(user=admin_user)
        except AdminProfile.DoesNotExist:
            raise serializers.ValidationError("Selected admin has no AdminProfile")

        validated_data['organization'] = admin_profile.organization

        # Create profile first
        profile = UserProfile.objects.create(user=user, **validated_data)

        # Assign defaults (M2M fields)
        shift_ids = ServiceShift.objects.filter(admin=admin_user, is_active=True).values_list('id', flat=True)[:1]
        week_off_ids = WeekOffPolicy.objects.filter(admin=admin_user).values_list('id', flat=True)[:1]
        location_ids = Location.objects.filter(admin=admin_user, is_active=True).values_list('id', flat=True)[:1]

        profile.shifts.set(shift_ids)
        profile.week_offs.set(week_off_ids)
        profile.locations.set(location_ids)

        return profile
    
    def update(self, instance, validated_data):
        # update only user.is_active
        print(f"==>> validated_data: {validated_data}")
        user_data = validated_data.pop('user', {})
        print(f"==>> user_data: {user_data}")
        if 'is_active' in user_data:
            print(f"==>> instance: {instance}")
            instance.user.is_active = user_data['is_active']
            instance.user.save()

        return instance


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = OrganizationSettings
        fields = '__all__'

class AllOrganizationProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    system_owner = serializers.PrimaryKeyRelatedField(queryset=BaseUserModel.objects.all())
    is_user_active = serializers.SerializerMethodField()  # 👈 custom field

    class Meta:
        model = OrganizationProfile
        fields = ['id', 'user', 'organization_name', 'system_owner', 'created_at', 'is_user_active']

    def get_is_user_active(self, obj):
        return obj.user.is_active