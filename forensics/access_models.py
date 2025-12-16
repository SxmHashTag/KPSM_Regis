import uuid
from django.db import models
from django.utils import timezone


class AccessRequest(models.Model):
    """Model to track user access requests - Offline system"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200, help_text="Full name of the requester")
    badge_number = models.CharField(max_length=50, help_text="Badge or ID number (Required)")
    department = models.CharField(max_length=100, help_text="Department/Unit")
    phone_extension = models.CharField(max_length=30, blank=True, help_text="Office extension (optional)")
    requested_username = models.CharField(max_length=150, help_text="Desired username for login")
    reason = models.TextField(help_text="Reason for requesting system access")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=100, blank=True, help_text="Admin who reviewed")
    review_notes = models.TextField(blank=True, help_text="Admin notes on decision")
    temp_password = models.CharField(max_length=50, blank=True, help_text="Temporary password if approved")
    
    def __str__(self):
        return f"{self.full_name} - {self.status}"
    
    class Meta:
        db_table = 'access_requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['badge_number']),
        ]
