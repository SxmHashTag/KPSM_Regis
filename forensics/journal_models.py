import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class DailyJournal(models.Model):
    """Daily work journal entries for tracking completed tasks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField(default=timezone.now)
    title = models.CharField(max_length=255, help_text='Brief title for the day')
    content = models.TextField(help_text='Detailed description of tasks completed')
    tags = models.JSONField(default=list, blank=True, help_text='Tags for categorizing work')
    is_pinned = models.BooleanField(default=False, help_text='Pin important entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_journals'
        ordering = ['-date', '-created_at']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['is_pinned']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.title}"


class JournalComment(models.Model):
    """Comments on journal entries for collaboration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(DailyJournal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'journal_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['journal', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.journal.date}"
