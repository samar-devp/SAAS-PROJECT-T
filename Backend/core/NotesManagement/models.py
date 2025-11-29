"""
Advanced Notes Management System
Comprehensive note-taking, organization, and collaboration
"""

from django.db import models
from uuid import uuid4
from datetime import date, datetime
from AuthN.models import *


class NoteCategory(models.Model):
    """Note Categories"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_note_categories'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_note_categories'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    color_code = models.CharField(max_length=7, default='#3498db')
    icon = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Note(models.Model):
    """Note Model"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_notes'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_notes'
    )
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='created_notes'
    )
    category = models.ForeignKey(
        NoteCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notes'
    )
    
    # Note Details
    title = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Organization
    tags = models.JSONField(default=list, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    # Sharing & Collaboration
    is_shared = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        BaseUserModel,
        related_name='shared_notes',
        blank=True
    )
    can_edit = models.ManyToManyField(
        BaseUserModel,
        related_name='editable_notes',
        blank=True
    )
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    images = models.JSONField(default=list, blank=True)
    
    # Reminders
    reminder_date = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    
    # Version Control
    version = models.IntegerField(default=1)
    parent_note = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='versions'
    )
    
    # Metadata
    word_count = models.IntegerField(default=0)
    reading_time_minutes = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['created_by', 'is_archived']),
            models.Index(fields=['category', 'is_archived']),
        ]
    
    def __str__(self):
        return self.title


class NoteComment(models.Model):
    """Note Comments"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    note = models.ForeignKey(
        Note, on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='note_comments'
    )
    comment = models.TextField()
    parent_comment = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.note.title}"


class NoteVersion(models.Model):
    """Note Version History"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    note = models.ForeignKey(
        Note, on_delete=models.CASCADE,
        related_name='version_history'
    )
    version_number = models.IntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    changed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    change_summary = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ('note', 'version_number')
    
    def __str__(self):
        return f"{self.note.title} - v{self.version_number}"


class NoteTemplate(models.Model):
    """Note Templates"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_note_templates'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_note_templates'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    template_content = models.TextField()
    category = models.ForeignKey(
        NoteCategory, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

