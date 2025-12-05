"""
Contact Management Models
"""
from django.db import models
from django.utils.timezone import now
from AuthN.models import BaseUserModel


class Contact(models.Model):
    """
    Contact model to store contact details extracted from business cards or manually entered
    """
    SOURCE_CHOICES = [
        ('scanned', 'Scanned'),
        ('manual', 'Manual'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # Admin and User Assignment
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_contacts',
        help_text="Admin who owns this contact"
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='assigned_contacts',
        blank=True, null=True,
        help_text="User assigned to this contact (if created by user)"
    )
    
    # Basic Information
    full_name = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    
    # Contact Information
    mobile_number = models.CharField(max_length=20, default='')  # Required field
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)
    office_landline = models.CharField(max_length=20, blank=True, null=True)
    fax_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Email Information
    email_address = models.EmailField(blank=True, null=True)
    alternate_email = models.EmailField(blank=True, null=True)
    
    # Address Information
    full_address = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    
    # Web & Social Links
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Additional Information
    additional_notes = models.TextField(blank=True, null=True)
    
    # Business Card Image
    business_card_image = models.ImageField(upload_to='business_cards/', blank=True, null=True)
    
    # Metadata
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    created_by = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, related_name='created_contacts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', 'user']),
            models.Index(fields=['full_name']),
            models.Index(fields=['company_name']),
            models.Index(fields=['email_address']),
            models.Index(fields=['mobile_number']),
            models.Index(fields=['state', 'city']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.full_name or 'Unnamed Contact'} - {self.company_name or 'No Company'}"
