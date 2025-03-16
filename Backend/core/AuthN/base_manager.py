# import uuid
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
# from django.db import models
# from django.core.exceptions import ValidationError
# from django.contrib.auth.hashers import make_password

# class CustomUserManager(BaseUserManager):
#     def create_user(self, email, username, password=None, **extra_fields):
#         if not email:
#             raise ValueError("Email is required")
#         email = self.normalize_email(email)
#         extra_fields.setdefault('is_active', True)
#         user = self.model(email=email, username=username, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, username, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         return self.create_user(email, username, password, **extra_fields)


# class CustomUser(AbstractBaseUser, PermissionsMixin):
#     ROLE_CHOICES = (
#         ('system_owner', 'System Owner'),
#         ('organization', 'Organization'),
#         ('admin', 'Admin'),
#         ('user', 'User'),
#     )

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     email = models.EmailField(unique=True)
#     username = models.CharField(max_length=150, unique=True)
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)  # Required for Django Admin
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     groups = models.ManyToManyField(
#         Group,
#         related_name="custom_user_groups",  # ✅ Prevents conflict with Django's built-in User model
#         blank=True
#     )
#     user_permissions = models.ManyToManyField(
#         Permission,
#         related_name="custom_user_permissions",  # ✅ Prevents conflict
#         blank=True
#     )

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']

#     objects = CustomUserManager()

#     def __str__(self):
#         return f"{self.username} ({self.role})"
