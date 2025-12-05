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
        fields = ['id', 'email', 'username', 'password', 'role', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': True},
        }

    def validate_phone_number(self, value):
        """Validate phone_number is required and unique for all roles"""
        # For partial updates, if value is not provided, skip validation
        if value is None and self.parent and hasattr(self.parent, 'partial') and self.parent.partial:
            return value
        
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        
        value = value.strip()
        queryset = BaseUserModel.objects.filter(phone_number=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        
        return value

    def validate_email(self, value):
        """Validate email is unique"""
        if not value or not value.strip():
            raise serializers.ValidationError("Email is required.")
        value = value.strip()
        
        queryset = BaseUserModel.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value

    def validate_username(self, value):
        """Validate username is unique"""
        if not value or not value.strip():
            raise serializers.ValidationError("Username is required.")
        value = value.strip()
        
        queryset = BaseUserModel.objects.filter(username=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash password
        return BaseUserModel.objects.create(**validated_data)


# ==================== REGISTRATION SERIALIZERS (Only for Registration) ====================

# System Owner Profile Serializer - ONLY FOR REGISTRATION
class SystemOwnerProfileSerializer(serializers.ModelSerializer):
    """
    Registration serializer for System Owner.
    This serializer should ONLY be used in registration endpoints.
    """
    user = CustomUserSerializer()

    class Meta:
        model = SystemOwnerProfile
        fields = ['id', 'user', 'company_name']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'system_owner'
        user = BaseUserModel.objects.create_user(**user_data)
        return SystemOwnerProfile.objects.create(user=user, **validated_data)


# Organization Profile Serializer - ONLY FOR REGISTRATION
class OrganizationProfileSerializer(serializers.ModelSerializer):
    """
    Registration serializer for Organization.
    This serializer should ONLY be used in registration endpoints.
    """
    user = CustomUserSerializer()
    system_owner = serializers.PrimaryKeyRelatedField(queryset=BaseUserModel.objects.all())

    class Meta:
        model = OrganizationProfile
        fields = ['id', 'user', 'organization_name', 'system_owner']
    
    def validate_organization_name(self, value):
        """Validate that organization_name is unique"""
        if not value or not value.strip():
            raise serializers.ValidationError("Organization name is required.")
        
        value = value.strip()
        
        # Check if this is an update (instance exists) or create (no instance)
        if self.instance:
            # For update, check if another organization has this name
            if OrganizationProfile.objects.filter(organization_name__iexact=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("An organization with this name already exists.")
        else:
            # For create, check if any organization has this name
            if OrganizationProfile.objects.filter(organization_name__iexact=value).exists():
                raise serializers.ValidationError("An organization with this name already exists.")
        
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'organization'
        base_user = BaseUserModel.objects.create_user(**user_data)  # ✅ Create user

        # ✅ Create settings linked to this user
        OrganizationSettings.objects.create(organization=base_user)

        # ✅ Create and return the OrganizationProfile
        return OrganizationProfile.objects.create(user=base_user, **validated_data)
        
    


# Admin Profile Serializer - ONLY FOR REGISTRATION
class AdminProfileSerializer(serializers.ModelSerializer):
    """
    Registration serializer for Admin.
    This serializer should ONLY be used in registration endpoints.
    """
    user = CustomUserSerializer()
    organization = serializers.PrimaryKeyRelatedField(queryset=BaseUserModel.objects.all())
    
    class Meta:
        model = AdminProfile
        fields = ['id', 'user', 'admin_name', 'organization']
    
    def validate_admin_name(self, value):
        """Validate that admin_name is unique"""
        if not value or not value.strip():
            raise serializers.ValidationError("Admin name is required.")
        
        value = value.strip()
        
        # For registration (no instance), check if any admin has this name
        if AdminProfile.objects.filter(admin_name__iexact=value).exists():
            raise serializers.ValidationError("An admin with this name already exists.")
        
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'admin'
        user = BaseUserModel.objects.create_user(**user_data)
        # Create default ServiceShift
        admin_profile = AdminProfile.objects.create(user=user, **validated_data)
        ServiceShift.objects.create(admin=user,organization=admin_profile.organization)
        WeekOffPolicy.objects.create(admin=user,organization=admin_profile.organization)
        WeekOffPolicy.objects.create(admin=user,organization=admin_profile.organization)
        TaskType.objects.create(admin=user,organization=admin_profile.organization)
        ExpenseCategory.objects.create(admin=user,organization=admin_profile.organization)
        return admin_profile


# User Profile Serializer - ONLY FOR REGISTRATION
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Registration serializer for Employee/User.
    This serializer should ONLY be used in registration endpoints.
    """
    user = CustomUserSerializer()
    admin = serializers.PrimaryKeyRelatedField(
        queryset=BaseUserModel.objects.all(),
        required=False,  # Will be set automatically if logged-in user is admin
        allow_null=False
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=BaseUserModel.objects.filter(role='organization'),
        required=False,
        allow_null=True,
        write_only=False
    )
    custom_employee_id = serializers.CharField(required=True, max_length=255)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = ['id', 'is_active']
    
    def get_is_active(self, obj):
        """Return user is_active status"""
        return obj.user.is_active if obj.user else None
    
    def validate(self, attrs):
        """Validate that phone_number, date_of_joining, and gender are provided for user role"""
        # For updates (partial=True), only validate fields that are being updated
        is_update = self.instance is not None
        
        # For create (not update), validate required fields
        if not is_update:
            user_data = attrs.get('user', {})
            phone_number = user_data.get('phone_number') if user_data else None
            date_of_joining = attrs.get('date_of_joining')
            gender = attrs.get('gender')
            
            # For create, phone_number is required
            if not phone_number or not phone_number.strip():
                raise serializers.ValidationError({
                    'user': {
                        'phone_number': 'Phone number is required.'
                    }
                })
            
            # For create, date_of_joining is required
            if not date_of_joining:
                raise serializers.ValidationError({
                    'date_of_joining': 'Date of joining is required for user role.'
                })
            
            # For create, gender is required
            if not gender or not gender.strip():
                raise serializers.ValidationError({
                    'gender': 'Gender is required for user role.'
                })
        
        # For updates, only validate fields that are being provided
        if is_update:
            # Only validate phone_number if it's being provided in user_data
            if 'user' in attrs and attrs['user']:
                user_data = attrs.get('user', {})
                phone_number = user_data.get('phone_number') if user_data else None
                if phone_number is not None and not phone_number.strip():
                    raise serializers.ValidationError({
                        'user': {
                            'phone_number': 'Phone number cannot be empty.'
                        }
                    })
        
        return attrs
    
    def validate_custom_employee_id(self, value):
        """Validate that custom_employee_id is unique"""
        if not value or not value.strip():
            raise serializers.ValidationError("custom_employee_id is required and cannot be empty.")
        
        # Check if this is an update (instance exists) or create (no instance)
        if self.instance:
            # For update, check if another user has this ID
            if UserProfile.objects.filter(custom_employee_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("This custom_employee_id is already taken.")
        else:
            # For create, check if any user has this ID
            if UserProfile.objects.filter(custom_employee_id=value).exists():
                raise serializers.ValidationError("This custom_employee_id is already taken.")
        
        return value.strip()

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'user'
        
        # Ensure phone_number is provided for user role
        if 'phone_number' not in user_data or not user_data.get('phone_number'):
            raise serializers.ValidationError({"user": {"phone_number": "Phone number is required for user role."}})
        
        user = BaseUserModel.objects.create_user(**user_data)

        # Get admin - it should be provided by view logic or in request
        admin_user = validated_data.get('admin')
        if not admin_user:
            
            # Try to get from context (set by view)
            request = self.context.get('request')
            if request and request.user and request.user.role == 'admin':
                admin_user = request.user
            else:
                raise serializers.ValidationError({"admin": ["This field is required."]})
        
        try:
            admin_profile = AdminProfile.objects.get(user=admin_user)
        except AdminProfile.DoesNotExist:
            raise serializers.ValidationError({"admin": ["Selected admin has no AdminProfile"]})

        # Set organization from admin (override if provided in request)
        validated_data['organization'] = admin_profile.organization

        # Ensure custom_employee_id is provided
        if 'custom_employee_id' not in validated_data or not validated_data['custom_employee_id']:
            raise serializers.ValidationError({"custom_employee_id": "This field is required."})

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


# ==================== READ/UPDATE SERIALIZERS (For Listing and Updating) ====================

class AdminProfileReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for Admin Profile.
    Used for listing and retrieving admin data (NOT for registration).
    """
    email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminProfile
        fields = ['id', 'user_id', 'admin_name', 'organization', 'email', 'username', 'phone_number', 'status', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'organization', 'created_at', 'updated_at']
    
    def get_email(self, obj):
        """Return admin user email"""
        return obj.user.email if obj.user else None
    
    def get_username(self, obj):
        """Return admin user username"""
        return obj.user.username if obj.user else None
    
    def get_phone_number(self, obj):
        """Return admin user phone number"""
        return obj.user.phone_number if obj.user else None
    
    def get_status(self, obj):
        """Return admin user status (is_active)"""
        return obj.user.is_active if obj.user else None
    
    def get_is_active(self, obj):
        """Return admin user is_active directly"""
        return obj.user.is_active if obj.user else None
    
    def get_user_id(self, obj):
        """Return admin user ID (UID)"""
        return str(obj.user.id) if obj.user else None


class AdminProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer for Admin Profile.
    Used for updating admin data (NOT for registration).
    """
    email = serializers.EmailField(required=False, allow_blank=False)
    username = serializers.CharField(required=False, max_length=150)
    phone_number = serializers.CharField(required=False, max_length=20)
    is_active = serializers.BooleanField(required=False)
    
    class Meta:
        model = AdminProfile
        fields = ['admin_name', 'email', 'username', 'phone_number', 'is_active']
    
    def validate_admin_name(self, value):
        """Validate that admin_name is unique"""
        if value and value.strip():
            value = value.strip()
            # For update, check if another admin has this name
            if self.instance:
                if AdminProfile.objects.filter(admin_name__iexact=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("An admin with this name already exists.")
            return value
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if value and value.strip():
            value = value.strip()
            if self.instance and self.instance.user:
                if BaseUserModel.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError("A user with this email already exists.")
            return value
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness"""
        if value and value.strip():
            value = value.strip()
            if self.instance and self.instance.user:
                if BaseUserModel.objects.filter(username=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError("A user with this username already exists.")
            return value
        return value
    
    def validate_phone_number(self, value):
        """Validate phone_number uniqueness"""
        if value and value.strip():
            value = value.strip()
            if self.instance and self.instance.user:
                if BaseUserModel.objects.filter(phone_number=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError("A user with this phone number already exists.")
            return value
        return value
    
    def update(self, instance, validated_data):
        """Update admin profile and user details"""
        # Update admin_name if provided
        if 'admin_name' in validated_data:
            instance.admin_name = validated_data.pop('admin_name')
        
        # Update user fields if provided
        user = instance.user
        if user:
            if 'email' in validated_data:
                user.email = validated_data.pop('email')
            if 'username' in validated_data:
                user.username = validated_data.pop('username')
            if 'phone_number' in validated_data:
                user.phone_number = validated_data.pop('phone_number')
            if 'is_active' in validated_data:
                user.is_active = validated_data.pop('is_active')
            user.save()
        
        instance.save()
        return instance


class UserProfileReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for User/Employee Profile.
    Used for listing and retrieving employee data (NOT for registration).
    """
    email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = ['id', 'user', 'admin', 'organization']
    
    def get_email(self, obj):
        """Return user email"""
        return obj.user.email if obj.user else None
    
    def get_username(self, obj):
        """Return user username"""
        return obj.user.username if obj.user else None
    
    def get_phone_number(self, obj):
        """Return user phone number"""
        return obj.user.phone_number if obj.user else None
    
    def get_is_active(self, obj):
        """Return user is_active status"""
        return obj.user.is_active if obj.user else None
    
    def get_profile_photo_url(self, obj):
        """Return full URL for profile photo"""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None
    
    def get_user_id(self, obj):
        """Return user ID (UID)"""
        return str(obj.user.id) if obj.user else None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer for User/Employee Profile.
    Used for updating employee data (NOT for registration).
    """
    email = serializers.EmailField(required=False, allow_blank=False)
    username = serializers.CharField(required=False, max_length=150)
    phone_number = serializers.CharField(required=False, max_length=20)
    custom_employee_id = serializers.CharField(required=False, max_length=255)
    is_active = serializers.BooleanField(required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'user_name', 'custom_employee_id', 'email', 'username', 'phone_number',
            'date_of_birth', 'date_of_joining', 'gender', 'designation', 'job_title',
            'is_active'
        ]
    
    def validate_custom_employee_id(self, value):
        """Validate that custom_employee_id is unique"""
        if value and value.strip():
            value = value.strip()
            # For update, check if another user has this ID
            if self.instance:
                if UserProfile.objects.filter(custom_employee_id=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("This custom_employee_id is already taken.")
            return value
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if value and value.strip():
            value = value.strip()
            if self.instance and self.instance.user:
                if BaseUserModel.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError("A user with this email already exists.")
            return value
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness"""
        if value and value.strip():
            value = value.strip()
            if self.instance and self.instance.user:
                if BaseUserModel.objects.filter(username=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError("A user with this username already exists.")
            return value
        return value
    
    def validate_phone_number(self, value):
        """Validate phone_number uniqueness"""
        if value and value.strip():
            value = value.strip()
            if self.instance and self.instance.user:
                if BaseUserModel.objects.filter(phone_number=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError("A user with this phone number already exists.")
            return value
        return value
    
    def update(self, instance, validated_data):
        """Update user profile and user details"""
        # Update profile fields
        profile_fields = ['user_name', 'custom_employee_id', 'date_of_birth', 'date_of_joining', 
                         'gender', 'designation', 'job_title']
        for field in profile_fields:
            if field in validated_data:
                setattr(instance, field, validated_data.pop(field))
        
        # Update user fields if provided
        user = instance.user
        if user:
            if 'email' in validated_data:
                user.email = validated_data.pop('email')
            if 'username' in validated_data:
                user.username = validated_data.pop('username')
            if 'phone_number' in validated_data:
                user.phone_number = validated_data.pop('phone_number')
            if 'is_active' in validated_data:
                user.is_active = validated_data.pop('is_active')
            user.save()
        
        instance.save()
        return instance


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    organization_logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationSettings
        fields = '__all__'
    
    def validate(self, data):
        """Validate that auto_checkout and auto_shiftwise_checkout are not both enabled"""
        auto_checkout = data.get('auto_checkout_enabled', None)
        auto_shiftwise_checkout = data.get('auto_shiftwise_checkout_enabled', None)
        
        # Get current values from instance if updating
        if self.instance:
            if auto_checkout is None:
                auto_checkout = self.instance.auto_checkout_enabled
            if auto_shiftwise_checkout is None:
                auto_shiftwise_checkout = self.instance.auto_shiftwise_checkout_enabled
        
        # Check if both are enabled
        if auto_checkout and auto_shiftwise_checkout:
            raise serializers.ValidationError({
                'auto_checkout_enabled': 'Auto Checkout and Auto Shiftwise Checkout cannot be enabled simultaneously. Please enable only one.',
                'auto_shiftwise_checkout_enabled': 'Auto Checkout and Auto Shiftwise Checkout cannot be enabled simultaneously. Please enable only one.'
            })
        
        return data
    
    def get_organization_logo_url(self, obj):
        """Return full URL for organization logo"""
        if obj.organization_logo:
            # ImageField provides .url property for full URL
            try:
                return obj.organization_logo.url
            except (ValueError, AttributeError):
                # Fallback for string paths or when file doesn't exist
                from django.conf import settings
                if str(obj.organization_logo).startswith('http'):
                    return str(obj.organization_logo)
                return f"{settings.MEDIA_URL}{obj.organization_logo}"
        return None

class AllOrganizationProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()  # Read-only for representation
    system_owner = serializers.PrimaryKeyRelatedField(read_only=True)
    is_user_active = serializers.SerializerMethodField()  # 👈 custom field
    organization_settings = serializers.SerializerMethodField()  # Settings as nested object
    organization_logo = serializers.SerializerMethodField()  # Logo URL for easy access

    class Meta:
        model = OrganizationProfile
        fields = ['id', 'user', 'organization_name', 'system_owner', 'created_at', 'updated_at', 'is_user_active', 'organization_settings', 'organization_logo']
        read_only_fields = ['id', 'system_owner', 'created_at', 'user']

    def get_is_user_active(self, obj):
        return obj.user.is_active

    def get_user(self, obj):
        """Return user data using CustomUserSerializer"""
        if obj and obj.user:
            user_serializer = CustomUserSerializer(obj.user)
            return user_serializer.data
        return None

    def get_organization_settings(self, obj):
        """Return organization settings using OrganizationSettingsSerializer"""
        try:
            settings = obj.user.own_organization_profile_setting
            settings_serializer = OrganizationSettingsSerializer(settings)
            return settings_serializer.data
        except OrganizationSettings.DoesNotExist:
            return None
    
    def get_organization_logo(self, obj):
        """Return organization logo URL"""
        try:
            settings = obj.user.own_organization_profile_setting
            if settings and settings.organization_logo:
                # ImageField provides .url property for full URL
                try:
                    return settings.organization_logo.url
                except (ValueError, AttributeError):
                    # Fallback for string paths or when file doesn't exist
                    from django.conf import settings as django_settings
                    if str(settings.organization_logo).startswith('http'):
                        return str(settings.organization_logo)
                    return f"{django_settings.MEDIA_URL}{settings.organization_logo}"
            return None
        except OrganizationSettings.DoesNotExist:
            return None

    def update(self, instance, validated_data):
        """Update organization profile and user details"""
        # Get user data from initial_data (raw request data) to avoid DictField conversion issues
        user_data = {}
        if hasattr(self, 'initial_data') and 'user' in self.initial_data:
            raw_user_data = self.initial_data.get('user')
            if isinstance(raw_user_data, dict):
                user_data = raw_user_data
            elif raw_user_data is None:
                user_data = {}
        else:
            # Fallback to validated_data if initial_data not available
            user_data_raw = validated_data.pop('user', None)
            if isinstance(user_data_raw, dict):
                user_data = user_data_raw
        
        # Update organization profile fields
        if 'organization_name' in validated_data:
            new_org_name = validated_data['organization_name'].strip() if validated_data['organization_name'] else None
            if new_org_name and new_org_name != instance.organization_name:
                # Check uniqueness excluding current organization
                if OrganizationProfile.objects.filter(organization_name__iexact=new_org_name).exclude(id=instance.id).exists():
                    raise serializers.ValidationError({
                        'organization_name': ['An organization with this name already exists.']
                    })
            instance.organization_name = new_org_name
        
        # Update user fields if provided
        user = instance.user
        if user_data and isinstance(user_data, dict):
            # Validate and update email if changed
            if 'email' in user_data:
                email = user_data['email'].strip() if user_data['email'] else None
                if email:
                    if email != user.email:
                        # Check uniqueness excluding current user
                        if BaseUserModel.objects.filter(email=email).exclude(id=user.id).exists():
                            raise serializers.ValidationError({
                                'user': {'email': ['A user with this email already exists.']}
                            })
                        user.email = email
            
            # Validate and update username if changed
            if 'username' in user_data:
                username = user_data['username'].strip() if user_data['username'] else None
                if username:
                    if username != user.username:
                        # Check uniqueness excluding current user
                        if BaseUserModel.objects.filter(username=username).exclude(id=user.id).exists():
                            raise serializers.ValidationError({
                                'user': {'username': ['A user with this username already exists.']}
                            })
                        user.username = username
            
            # Validate and update phone_number if changed
            if 'phone_number' in user_data:
                phone_number = user_data['phone_number'].strip() if user_data['phone_number'] else None
                if phone_number:
                    if phone_number != user.phone_number:
                        # Check uniqueness excluding current user
                        if BaseUserModel.objects.filter(phone_number=phone_number).exclude(id=user.id).exists():
                            raise serializers.ValidationError({
                                'user': {'phone_number': ['A user with this phone number already exists.']}
                            })
                        user.phone_number = phone_number
            
            # Update is_active if provided
            if 'is_active' in user_data:
                user.is_active = user_data['is_active']
            
            # Update password if provided
            if 'password' in user_data and user_data['password']:
                user.set_password(user_data['password'])
            
            user.save()
        
        # Update organization settings if provided
        settings_data = {}
        if hasattr(self, 'initial_data') and 'organization_settings' in self.initial_data:
            raw_settings_data = self.initial_data.get('organization_settings')
            if isinstance(raw_settings_data, dict):
                settings_data = raw_settings_data
        
        if settings_data and isinstance(settings_data, dict):
            # Get or create organization settings
            try:
                org_settings = instance.user.own_organization_profile_setting
            except OrganizationSettings.DoesNotExist:
                # Create settings if they don't exist
                org_settings = OrganizationSettings.objects.create(organization=instance.user)
            
            # Ensure auto_checkout and auto_shiftwise_checkout are mutually exclusive
            if 'auto_checkout_enabled' in settings_data and settings_data.get('auto_checkout_enabled'):
                settings_data['auto_shiftwise_checkout_enabled'] = False
            elif 'auto_shiftwise_checkout_enabled' in settings_data and settings_data.get('auto_shiftwise_checkout_enabled'):
                settings_data['auto_checkout_enabled'] = False
            
            # Update settings fields
            settings_serializer = OrganizationSettingsSerializer(
                org_settings, 
                data=settings_data, 
                partial=True
            )
            if settings_serializer.is_valid():
                settings_serializer.save()
            else:
                raise serializers.ValidationError({
                    'organization_settings': settings_serializer.errors
                })
        
        instance.save()
        return instance


# ==================== ADDITIONAL UTILITY SERIALIZERS ====================

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change operation.
    
    Fields:
        - old_password (str, optional): Current password (required unless force_change=True)
        - new_password (str, required): New password (min 8 characters)
        - force_change (bool, optional): Force password change without old password
    """
    old_password = serializers.CharField(required=False, write_only=True, allow_blank=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    force_change = serializers.BooleanField(required=False, default=False)
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        if not value or len(value.strip()) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value.strip()
    
    def validate(self, attrs):
        """Cross-field validation."""
        force_change = attrs.get('force_change', False)
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        
        # If not force change, old_password is required
        if not force_change and not old_password:
            raise serializers.ValidationError({
                'old_password': 'Old password is required when force_change is False.'
            })
        
        return attrs


class EmployeeActivateSerializer(serializers.Serializer):
    """
    Serializer for employee activation/deactivation.
    
    Fields:
        - action (str, required): 'activate' or 'deactivate'
    """
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate'],
        default='deactivate'
    )


class EmployeeTransferSerializer(serializers.Serializer):
    """
    Serializer for transferring employees to another admin.
    
    Fields:
        - employee_ids (list, required): List of employee UUIDs
        - new_admin_id (UUID, required): Target admin UUID
    """
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    new_admin_id = serializers.UUIDField(required=True)
    
    def validate_employee_ids(self, value):
        """Validate employee_ids list."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("employee_ids list cannot be empty.")
        return value


class EmployeeStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating employee status for a specific date.
    
    Fields:
        - employee_ids (list, required): List of employee UUIDs
        - status (str, required): 'active' or 'inactive'
    """
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    status = serializers.ChoiceField(
        choices=['active', 'inactive'],
        required=True
    )


class GeoFencingUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating geo-fencing settings.
    
    Fields:
        - allow_geo_fencing (bool, optional): Enable/disable geo-fencing
        - radius (int, optional): Radius in meters (positive integer)
    """
    allow_geo_fencing = serializers.BooleanField(required=False, default=False)
    radius = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    
    def validate_radius(self, value):
        """Validate radius if provided."""
        if value is not None and value < 1:
            raise serializers.ValidationError("Radius must be a positive integer.")
        return value


class BulkActivateDeactivateSerializer(serializers.Serializer):
    """
    Serializer for bulk activate/deactivate operations.
    
    Fields:
        - employee_ids (list, required): List of employee UUIDs
        - action (str, required): 'activate' or 'deactivate'
    """
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate'],
        required=True
    )


class FcmTokenUpdateSerializer(serializers.Serializer):
    """
    Serializer for FCM token update.
    
    Fields:
        - fcm_token (str, required): Firebase Cloud Messaging token
    """
    fcm_token = serializers.CharField(required=True, max_length=255)
    
    def validate_fcm_token(self, value):
        """Validate FCM token."""
        if not value or not value.strip():
            raise serializers.ValidationError("FCM token cannot be empty.")
        return value.strip()