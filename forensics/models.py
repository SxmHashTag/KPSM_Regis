import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, EmailValidator
from django.utils import timezone

# Import AccessRequest model
from .access_models import AccessRequest
# Import Journal models
from .journal_models import DailyJournal, JournalComment


class UserProfile(models.Model):
    """Extended user profile with forensics-specific fields"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('investigator', 'Prosecutor'),
        ('analyst', 'Forensic Analyst'),
        ('user', 'Regular User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.username})"
    
    class Meta:
        db_table = 'user_profiles'


class Case(models.Model):
    """Core investigation cases"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    TYPE_CHOICES = [
        ('fraud', 'Fraud'),
        ('cybercrime', 'Cybercrime'),
        ('data_breach', 'Data Breach'),
        ('intellectual_property', 'Intellectual Property'),
        ('general', 'General'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('sur', 'SUR'),
        ('ar', 'AR'),
        ('jzz', 'JZZ'),
        ('zwacri', 'ZwaCri'),
        ('fraude', 'Fraude'),
        ('umm', 'UMM'),
        ('alpha', 'Alpha'),
        ('douane', 'Douane'),
        ('ind', 'IND'),
        ('verkeer', 'Verkeer'),
        ('kustwacht', 'Kustwacht'),
        ('pelican', 'Pelican'),
        ('ibs', 'IBS'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=100, unique=True, blank=True)
    case_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    case_type = models.CharField(max_length=30, choices=TYPE_CHOICES, blank=True, default='')
    date_opened = models.DateTimeField(default=timezone.now)
    date_closed = models.DateTimeField(null=True, blank=True)
    prosecutor = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True, help_text='Department handling the case')
    jurisdiction = models.CharField(max_length=200, blank=True)
    incident_date = models.DateTimeField(null=True, blank=True)
    incident_location = models.CharField(max_length=500, blank=True)
    evidence_location = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-generate case number if not provided
        if not self.case_number:
            from django.utils import timezone
            from django.db.models import Max
            year = timezone.now().strftime('%y')  # Get last 2 digits of year
            
            # Get all case numbers for this year and find the max
            cases_this_year = Case.objects.filter(
                case_number__startswith=f"{year}-"
            ).exclude(pk=self.pk)  # Exclude self in case of update
            
            max_num = 0
            for case in cases_this_year:
                try:
                    # Extract the numeric part (e.g., "0001" from "25-0001")
                    num = int(case.case_number.split('-')[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    continue
            
            next_num = max_num + 1
            
            # Format: YY-NNNN (e.g., 25-0001)
            self.case_number = f"{year}-{next_num:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.case_number} - {self.case_name}"
    
    class Meta:
        db_table = 'cases'
        ordering = ['-date_opened']
        indexes = [
            models.Index(fields=['case_number']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['date_opened']),
        ]


class Person(models.Model):
    """People involved in cases"""
    TYPE_CHOICES = [
        ('suspect', 'Suspect'),
        ('victim', 'Victim'),
        ('witness', 'Witness'),
        ('investigator', 'Investigator'),
        ('expert', 'Expert'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    ssn = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')
    person_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    notes = models.TextField(blank=True)
    aliases = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.person_type})"
    
    class Meta:
        db_table = 'persons'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name']),
            models.Index(fields=['first_name']),
            models.Index(fields=['person_type']),
        ]


class CasePerson(models.Model):
    """Many-to-many relationship between cases and persons"""
    ROLE_CHOICES = [
        ('suspect', 'Suspect'),
        ('victim', 'Victim'),
        ('witness', 'Witness'),
        ('investigator', 'Investigator'),
        ('expert', 'Expert'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='case_persons')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='person_cases')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    involvement_description = models.TextField(blank=True)
    date_added = models.DateTimeField(default=timezone.now)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.person} - {self.role} in {self.case.case_number}"
    
    class Meta:
        db_table = 'case_persons'
        unique_together = ['case', 'person', 'role']
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['person']),
        ]


class EvidenceTransfer(models.Model):
    """Track evidence transfers between departments (chain of custody)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey('Evidence', on_delete=models.CASCADE, related_name='transfers')
    from_department = models.CharField(max_length=20, blank=True, help_text='Department transferring from')
    to_department = models.CharField(max_length=20, blank=True, help_text='Department transferring to')
    transferred_by = models.CharField(max_length=200, blank=True)
    received_by = models.CharField(max_length=200, blank=True)
    transfer_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.evidence.evidence_number}: {self.from_department or 'Unassigned'} → {self.to_department or 'Unassigned'}"
    
    class Meta:
        db_table = 'evidence_transfers'
        ordering = ['-transfer_date']
        indexes = [
            models.Index(fields=['evidence']),
            models.Index(fields=['transfer_date']),
        ]


class EvidenceImage(models.Model):
    """Images associated with evidence items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey('Evidence', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='evidence_images/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"Image for {self.evidence.evidence_number}"
    
    class Meta:
        db_table = 'evidence_images'
        ordering = ['uploaded_at']


class Evidence(models.Model):
    """Evidence items with forensic tracking"""
    DEVICE_TYPE_CHOICES = [
        ('computer', 'Computer'),
        ('mobile', 'Mobile Device'),
        ('storage', 'Storage Device'),
        ('network', 'Network Device'),
        ('cloud', 'Cloud/Online Account'),
        ('drone', 'Drone/UAV'),
        ('gaming', 'Gaming Console'),
        ('car', 'Vehicle/Automotive'),
        ('iot', 'IoT Device'),
        ('memory', 'Memory/RAM'),
        ('video', 'Video Evidence'),
        ('dvr_nvr', 'DVR/NVR'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('reviewed', 'Reviewed'),
        ('archived', 'Archived'),
        ('returned', 'Returned'),
        ('destroyed', 'Destroyed'),
    ]
    
    STATE_CHOICES = [
        ('clean', 'Clean'),
        ('dirty', 'Dirty'),
        ('damaged', 'Damaged'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('sur', 'SUR'),
        ('ar', 'AR'),
        ('jzz', 'JZZ'),
        ('zwacri', 'ZwaCri'),
        ('fraude', 'Fraude'),
        ('umm', 'UMM'),
        ('alpha', 'Alpha'),
        ('douane', 'Douane'),
        ('ind', 'IND'),
        ('verkeer', 'Verkeer'),
        ('kustwacht', 'Kustwacht'),
        ('pelican', 'Pelican'),
        ('ibs', 'IBS'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence_number = models.CharField(max_length=100, unique=True, blank=True)
    ibs_number = models.CharField(max_length=50, blank=True, help_text='IBS tracking number (e.g., 24/46/123)')
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence')
    
    # Device type and basic info
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='other')
    item_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    imei = models.CharField(max_length=100, blank=True, help_text='Primary IMEI for mobile devices')
    imei_numbers = models.JSONField(default=list, blank=True, help_text='Additional IMEI numbers for dual/multi-SIM devices')
    location = models.CharField(max_length=500, blank=True)
    
    # Department and custody tracking
    current_department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True, help_text='Current department holding the device')
    received_by = models.CharField(max_length=200, blank=True, help_text='Person who received the device')
    received_date = models.DateTimeField(null=True, blank=True, help_text='Date device was received by current department')
    
    # Status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, null=True, blank=True)
    damages = models.BooleanField(default=False)
    damage_description = models.TextField(blank=True)
    
    # Examiner information
    examiner_name = models.CharField(max_length=200, blank=True)
    acquisition_date = models.DateTimeField(null=True, blank=True)
    acquisition_notes = models.TextField(blank=True)
    
    # Technical fields
    make = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=100, blank=True)
    mac_address = models.CharField(max_length=100, blank=True)
    acquisition_method = models.CharField(max_length=100, blank=True)
    acquisition_tool = models.CharField(max_length=100, blank=True)
    hash_algorithm = models.CharField(max_length=50, blank=True)
    hash_verified = models.BooleanField(default=False)
    device_condition = models.TextField(blank=True)
    
    # Forensic fields
    chain_of_custody_notes = models.TextField(blank=True)
    forensic_image_path = models.CharField(max_length=500, blank=True)
    
    # Ownership and custody
    owner_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_evidence')
    seized_from_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='seized_evidence')
    custodian_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='custody_evidence')
    seizure_authority = models.CharField(max_length=200, blank=True)
    seizure_date = models.DateTimeField(null=True, blank=True)
    seizure_location = models.CharField(max_length=500, blank=True)
    
    # Legacy/additional fields
    collected_date = models.DateTimeField(default=timezone.now)
    collected_by = models.CharField(max_length=200, blank=True)
    location_found = models.CharField(max_length=500, blank=True)
    storage_location = models.CharField(max_length=500, blank=True)
    file_path = models.FileField(upload_to='evidence/%Y/%m/%d/', blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    hash_md5 = models.CharField(max_length=32, blank=True)
    hash_sha1 = models.CharField(max_length=40, blank=True)
    hash_sha256 = models.CharField(max_length=64, blank=True)
    
    # Device-specific data stored as JSON
    device_specific_data = models.JSONField(default=dict, blank=True)
    
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-generate hashes if file is uploaded
        if self.file_path and not self.hash_md5:
            self.file_path.seek(0)
            content = self.file_path.read()
            self.hash_md5 = hashlib.md5(content).hexdigest()
            self.hash_sha1 = hashlib.sha1(content).hexdigest()
            self.hash_sha256 = hashlib.sha256(content).hexdigest()
            self.file_size = len(content)
            self.file_path.seek(0)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.evidence_number} - {self.item_name}"
    
    class Meta:
        db_table = 'evidence'
        ordering = ['-collected_date']
        indexes = [
            models.Index(fields=['evidence_number']),
            models.Index(fields=['ibs_number']),
            models.Index(fields=['case']),
            models.Index(fields=['device_type']),
            models.Index(fields=['status']),
        ]


class Document(models.Model):
    """Case-related documents and reports"""
    TYPE_CHOICES = [
        ('report', 'Report'),
        ('warrant', 'Warrant'),
        ('subpoena', 'Subpoena'),
        ('affidavit', 'Affidavit'),
        ('memo', 'Memo'),
        ('photo', 'Photo'),
        ('other', 'Other'),
    ]
    
    ACCESS_CHOICES = [
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('classified', 'Classified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    evidence = models.ForeignKey(Evidence, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    document_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_path = models.FileField(upload_to='documents/%Y/%m/%d/', blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    author = models.CharField(max_length=200, blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    version = models.CharField(max_length=20, default='1.0')
    is_confidential = models.BooleanField(default=False)
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='internal')
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.document_type})"
    
    class Meta:
        db_table = 'documents'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['document_type']),
        ]


class Task(models.Model):
    """Investigation tasks and workflow management"""
    TYPE_CHOICES = [
        ('investigation', 'Investigation'),
        ('analysis', 'Analysis'),
        ('documentation', 'Documentation'),
        ('evidence', 'Evidence'),
        ('legal', 'Legal'),
        ('meeting', 'Meeting'),
        ('review', 'Review'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('blocked', 'Blocked'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    task_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.CharField(max_length=200, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.IntegerField(null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completion_percentage = models.IntegerField(default=0)
    dependencies = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.task_name} ({self.status})"
    
    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]


class TimelineActivity(models.Model):
    """Chronological activity log for case timeline"""
    TYPE_CHOICES = [
        ('evidence_collected', 'Evidence Collected'),
        ('interview', 'Interview'),
        ('analysis', 'Analysis'),
        ('document_created', 'Document Created'),
        ('task_completed', 'Task Completed'),
        ('status_change', 'Status Change'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='timeline_activities')
    activity_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    activity_date = models.DateTimeField()
    performed_by = models.CharField(max_length=200, blank=True)
    related_evidence = models.ForeignKey(Evidence, on_delete=models.SET_NULL, null=True, blank=True)
    related_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    related_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.activity_date.strftime('%Y-%m-%d')}"
    
    class Meta:
        db_table = 'timeline_activities'
        ordering = ['-activity_date']
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['activity_date']),
        ]


class Notification(models.Model):
    """System notifications and alerts"""
    TYPE_CHOICES = [
        ('deadline_reminder', 'Deadline Reminder'),
        ('status_change', 'Status Change'),
        ('new_evidence', 'New Evidence'),
        ('task_assigned', 'Task Assigned'),
        ('system_alert', 'System Alert'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    recipient = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.notification_type}"
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case']),
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]
