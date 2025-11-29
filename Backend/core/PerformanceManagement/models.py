"""
Advanced Performance Management System
OKRs, KPIs, Goal Library, Review Cycles, Rating Matrix, 360 Reviews
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from AuthN.models import *


class GoalLibrary(models.Model):
    """Goal Library - Predefined goals"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='goal_libraries'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_goal_libraries',
        null=True, blank=True
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Goal Metrics
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('percentage', 'Percentage'),
            ('number', 'Number'),
            ('currency', 'Currency'),
            ('boolean', 'Yes/No'),
            ('rating', 'Rating (1-5)')
        ],
        default='percentage'
    )
    target_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class OKR(models.Model):
    """Objectives and Key Results"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_okrs'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='employee_okrs'
    )
    
    # Objective
    objective = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('quarterly', 'Quarterly'), ('half_yearly', 'Half Yearly'), ('yearly', 'Yearly')],
        default='quarterly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Key Results
    key_results = models.JSONField(default=list, blank=True, help_text="List of key results with targets")
    
    # Progress
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', 'Not Started'),
            ('on_track', 'On Track'),
            ('at_risk', 'At Risk'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='not_started'
    )
    
    # Review
    reviewed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_okrs'
    )
    review_comments = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_start', '-created_at']
    
    def __str__(self):
        return f"{self.employee.email} - {self.objective}"


class KPI(models.Model):
    """Key Performance Indicators"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_kpis'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='employee_kpis'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    
    # Metric
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('percentage', 'Percentage'),
            ('number', 'Number'),
            ('currency', 'Currency'),
            ('boolean', 'Yes/No'),
            ('rating', 'Rating (1-5)')
        ],
        default='percentage'
    )
    target_value = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unit = models.CharField(max_length=50, blank=True, null=True)
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('below_target', 'Below Target'),
            ('on_target', 'On Target'),
            ('above_target', 'Above Target')
        ],
        default='below_target'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_start', 'name']
    
    def __str__(self):
        return f"{self.employee.email} - {self.name}"


class ReviewCycle(models.Model):
    """Performance Review Cycles"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='review_cycles'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_review_cycles',
        null=True, blank=True
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    cycle_type = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('half_yearly', 'Half Yearly'),
            ('yearly', 'Yearly'),
            ('custom', 'Custom')
        ],
        default='yearly'
    )
    
    # Period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Review Dates
    self_review_start = models.DateField(null=True, blank=True)
    self_review_end = models.DateField(null=True, blank=True)
    manager_review_start = models.DateField(null=True, blank=True)
    manager_review_end = models.DateField(null=True, blank=True)
    hr_review_start = models.DateField(null=True, blank=True)
    hr_review_end = models.DateField(null=True, blank=True)
    
    # Settings
    enable_360_review = models.BooleanField(default=False)
    enable_peer_review = models.BooleanField(default=False)
    enable_self_review = models.BooleanField(default=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.start_date} to {self.end_date}"


class RatingMatrix(models.Model):
    """Performance Rating Matrix"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='rating_matrices'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Rating Scale
    rating_scale = models.JSONField(
        default=list,
        help_text="[{'rating': 5, 'label': 'Excellent', 'min_score': 90}, ...]"
    )
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name


class PerformanceReview(models.Model):
    """Performance Reviews"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('self_review', 'Self Review'),
        ('manager_review', 'Manager Review'),
        ('hr_review', 'HR Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_performance_reviews'
    )
    review_cycle = models.ForeignKey(
        ReviewCycle, on_delete=models.CASCADE,
        related_name='reviews'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='performance_reviews'
    )
    reviewer = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='reviewed_performances',
        limit_choices_to={'role__in': ['admin', 'user']}
    )
    
    # Review Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    review_type = models.CharField(
        max_length=20,
        choices=[
            ('self', 'Self Review'),
            ('manager', 'Manager Review'),
            ('peer', 'Peer Review'),
            ('hr', 'HR Review'),
            ('360', '360 Review')
        ],
        default='manager'
    )
    
    # Ratings
    overall_rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rating_matrix = models.ForeignKey(
        RatingMatrix, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviews'
    )
    
    # Review Sections
    goals_achievement = models.TextField(blank=True, null=True)
    strengths = models.TextField(blank=True, null=True)
    areas_for_improvement = models.TextField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    development_plan = models.TextField(blank=True, null=True)
    
    # Section Ratings (JSON)
    section_ratings = models.JSONField(
        default=dict,
        blank=True,
        help_text="{'technical_skills': 4.5, 'communication': 4.0, ...}"
    )
    
    # Dates
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('review_cycle', 'employee', 'reviewer', 'review_type')
    
    def __str__(self):
        return f"{self.employee.email} - {self.review_cycle.name} - {self.review_type}"


class Review360(models.Model):
    """360 Degree Reviews"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    review_cycle = models.ForeignKey(
        ReviewCycle, on_delete=models.CASCADE,
        related_name='reviews_360'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='reviews_360_received'
    )
    reviewer = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='reviews_360_given'
    )
    
    relationship = models.CharField(
        max_length=50,
        choices=[
            ('peer', 'Peer'),
            ('subordinate', 'Subordinate'),
            ('manager', 'Manager'),
            ('client', 'Client'),
            ('other', 'Other')
        ],
        default='peer'
    )
    
    # Ratings
    ratings = models.JSONField(default=dict, blank=True)
    feedback = models.TextField(blank=True, null=True)
    strengths = models.TextField(blank=True, null=True)
    areas_for_improvement = models.TextField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('submitted', 'Submitted'), ('anonymous', 'Anonymous')],
        default='pending'
    )
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('review_cycle', 'employee', 'reviewer')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"360 Review - {self.employee.email} by {self.reviewer.email}"

