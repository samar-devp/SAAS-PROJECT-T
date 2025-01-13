import uuid
from django.contrib.auth.hashers import make_password
from django.db import models

class SystemOwner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID as the primary key
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # To store hashed password
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Hash password before saving if it is not already hashed
        if not self.id or not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID as the primary key
    owner = models.ForeignKey('SystemOwner', on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # To store hashed password
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Hash password before saving if it is not already hashed
        if not self.id or not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.organization_name


class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID as the primary key
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)  # Foreign Key to Organization
    admin_name = models.CharField(max_length=255)  # Admin's name
    email = models.EmailField(unique=True)  # Admin's email, should be unique
    username = models.CharField(max_length=150, unique=True)  # Admin's unique username
    password = models.CharField(max_length=128)  # To store the hashed password
    is_active = models.BooleanField(default=True)  # Admin's active status
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when the admin is created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp of when the admin was last updated

    def save(self, *args, **kwargs):
        # Hash password before saving if it is not already hashed
        if not self.id or not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.admin_name


class Supervisor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID as the primary key
    admin = models.ForeignKey('Admin', on_delete=models.CASCADE)  # Foreign Key to Admin
    supervisor_name = models.CharField(max_length=255)  # Supervisor's name
    email = models.EmailField(unique=True)  # Supervisor's email, should be unique
    username = models.CharField(max_length=150, unique=True)  # Supervisor's unique username
    password = models.CharField(max_length=128)  # To store the hashed password
    is_active = models.BooleanField(default=True)  # Supervisor's active status
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when the supervisor is created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp of when the supervisor was last updated

    def save(self, *args, **kwargs):
        # Hash password before saving if it is not already hashed
        if not self.id or not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.supervisor_name


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID as the primary key
    admin = models.ForeignKey('Admin', on_delete=models.SET_NULL, null=True, blank=True)  # Foreign Key to Admin (nullable)
    supervisor = models.ForeignKey('Supervisor', on_delete=models.SET_NULL, null=True, blank=True)  # Foreign Key to Supervisor (nullable)
    employee_name = models.CharField(max_length=255)  # Employee's name
    email = models.EmailField(unique=True)  # Employee's email, should be unique
    username = models.CharField(max_length=150, unique=True)  # Employee's unique username
    password = models.CharField(max_length=128)  # To store the hashed password
    is_active = models.BooleanField(default=True)  # Employee's active status
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when the employee is created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp of when the employee was last updated

    def save(self, *args, **kwargs):
        # Hash password before saving if it is not already hashed
        if not self.id or not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.employee_name