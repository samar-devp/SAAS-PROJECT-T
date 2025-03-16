import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model


# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


# Custom User Model with UUID as Primary Key
class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # ✅ UUID as primary key
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(
        max_length=50,
        choices=[("system_owner", "System Owner"), ("organization", "Organization"), ("admin", "Admin"), ("user", "User")]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=now)  # ✅ Add this field

    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


# Get the CustomUser model
CustomUser = get_user_model()


# ✅ System Owner Profile (Top-Level)
class SystemOwnerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # ✅ UUID as primary key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)

    def __str__(self):
        return self.company_name


# ✅ Organization Profile (Belongs to System Owner as a CustomUser FK)
class OrganizationProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # ✅ UUID as primary key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=255)
    system_owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="organizations", limit_choices_to={'role': 'system_owner'}
    )  # ✅ Directly linking to CustomUser with system_owner role

    def __str__(self):
        return self.organization_name


# ✅ Admin Profile (Belongs to an Organization as a CustomUser FK)
class AdminProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # ✅ UUID as primary key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    admin_name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="admins", limit_choices_to={'role': 'organization'}
    )  # ✅ Directly linking to CustomUser with organization role

    def __str__(self):
        return self.admin_name


# ✅ User Profile (Belongs to an Admin as a CustomUser FK)
class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # ✅ UUID as primary key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255)
    admin = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="users", limit_choices_to={'role': 'admin'}
    )  # ✅ Directly linking to CustomUser with admin role

    def __str__(self):
        return self.user_name
