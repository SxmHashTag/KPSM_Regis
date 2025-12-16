from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Case, Person, CasePerson, Evidence, EvidenceImage, EvidenceTransfer, Document, Task, TimelineActivity, Notification, UserProfile, AccessRequest, DailyJournal, JournalComment


@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    list_display = ['username', 'full_name', 'role', 'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['username', 'full_name', 'department']


@admin.register(Case)
class CaseAdmin(ImportExportModelAdmin):
    list_display = ['case_number', 'case_name', 'status', 'priority', 'case_type', 'date_opened', 'prosecutor']
    list_filter = ['status', 'priority', 'case_type', 'date_opened']
    search_fields = ['case_number', 'case_name', 'prosecutor', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('case_number', 'case_name', 'description', 'status', 'priority', 'case_type')
        }),
        ('Dates', {
            'fields': ('date_opened', 'date_closed', 'incident_date')
        }),
        ('Assignment', {
            'fields': ('prosecutor', 'department', 'jurisdiction')
        }),
        ('Location Details', {
            'fields': ('incident_location', 'evidence_location')
        }),
        ('Additional', {
            'fields': ('notes', 'tags', 'created_at', 'updated_at')
        }),
    )


@admin.register(Person)
class PersonAdmin(ImportExportModelAdmin):
    list_display = ['first_name', 'last_name', 'person_type', 'email', 'phone', 'created_at']
    list_filter = ['person_type', 'country', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'ssn']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CasePerson)
class CasePersonAdmin(ImportExportModelAdmin):
    list_display = ['case', 'person', 'role', 'is_primary', 'date_added']
    list_filter = ['role', 'is_primary', 'date_added']
    search_fields = ['case__case_number', 'person__first_name', 'person__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Evidence)
class EvidenceAdmin(ImportExportModelAdmin):
    list_display = ['evidence_number', 'item_name', 'device_type', 'case', 'status', 'collected_date', 'collected_by']
    list_filter = ['device_type', 'status', 'collected_date']
    search_fields = ['evidence_number', 'item_name', 'description', 'collected_by', 'serial_number', 'hash_md5', 'hash_sha256']
    readonly_fields = ['id', 'hash_md5', 'hash_sha1', 'hash_sha256', 'file_size', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('evidence_number', 'case', 'evidence_type', 'item_name', 'description', 'status')
        }),
        ('Collection Details', {
            'fields': ('collected_date', 'collected_by', 'location_found', 'storage_location')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'file_type', 'hash_md5', 'hash_sha1', 'hash_sha256')
        }),
        ('Chain of Custody & Additional', {
            'fields': ('chain_of_custody', 'tags', 'notes', 'created_at', 'updated_at')
        }),
    )


@admin.register(EvidenceImage)
class EvidenceImageAdmin(ImportExportModelAdmin):
    list_display = ['evidence', 'caption', 'uploaded_at', 'uploaded_by']
    list_filter = ['uploaded_at']
    search_fields = ['evidence__evidence_number', 'caption', 'uploaded_by']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(EvidenceTransfer)
class EvidenceTransferAdmin(ImportExportModelAdmin):
    list_display = ['evidence', 'from_department', 'to_department', 'received_by', 'transfer_date']
    list_filter = ['from_department', 'to_department', 'transfer_date']
    search_fields = ['evidence__evidence_number', 'received_by', 'transferred_by', 'notes']
    readonly_fields = ['id', 'transfer_date']
    date_hierarchy = 'transfer_date'


@admin.register(Document)
class DocumentAdmin(ImportExportModelAdmin):
    list_display = ['title', 'document_type', 'case', 'author', 'date_created', 'access_level', 'is_confidential']
    list_filter = ['document_type', 'access_level', 'is_confidential', 'date_created']
    search_fields = ['title', 'description', 'author']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):
    list_display = ['task_name', 'case', 'task_type', 'status', 'priority', 'assigned_to', 'due_date', 'completion_percentage']
    list_filter = ['task_type', 'status', 'priority', 'created_at']
    search_fields = ['task_name', 'description', 'assigned_to']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(TimelineActivity)
class TimelineActivityAdmin(ImportExportModelAdmin):
    list_display = ['title', 'case', 'activity_type', 'activity_date', 'performed_by']
    list_filter = ['activity_type', 'activity_date']
    search_fields = ['title', 'description', 'performed_by']
    readonly_fields = ['id', 'created_at']


@admin.register(Notification)
class NotificationAdmin(ImportExportModelAdmin):
    list_display = ['title', 'notification_type', 'priority', 'recipient', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient']
    readonly_fields = ['id', 'created_at']


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'badge_number', 'department', 'requested_username', 'status', 'requested_at']
    list_filter = ['status', 'department', 'requested_at']
    search_fields = ['full_name', 'badge_number', 'requested_username', 'department']
    readonly_fields = ['id', 'requested_at', 'reviewed_at', 'temp_password']
    actions = ['approve_requests', 'reject_requests']
    fieldsets = (
        ('Request Information', {
            'fields': ('full_name', 'badge_number', 'department', 'phone_extension', 'requested_username', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'requested_at')
        }),
        ('Review', {
            'fields': ('reviewed_at', 'reviewed_by', 'review_notes', 'temp_password')
        }),
    )
    
    def approve_requests(self, request, queryset):
        """Admin action to approve access requests"""
        import secrets
        import string
        from django.utils import timezone
        from django.contrib.auth.models import User
        
        approved_count = 0
        passwords_info = []
        
        for access_request in queryset.filter(status='pending'):
            # Generate temporary password
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            
            try:
                # Create user account
                user = User.objects.create_user(
                    username=access_request.requested_username,
                    password=temp_password
                )
                user.first_name = access_request.full_name.split()[0] if access_request.full_name else ''
                user.last_name = ' '.join(access_request.full_name.split()[1:]) if len(access_request.full_name.split()) > 1 else ''
                user.is_active = True
                user.save()
                
                # Update request
                access_request.status = 'approved'
                access_request.reviewed_at = timezone.now()
                access_request.reviewed_by = request.user.username
                access_request.temp_password = temp_password
                access_request.save()
                
                passwords_info.append(f"✅ {access_request.full_name} - Username: {user.username} | Password: {temp_password}")
                approved_count += 1
                
            except Exception as e:
                self.message_user(request, f"Error creating user for {access_request.full_name}: {str(e)}", level='error')
        
        if approved_count > 0:
            # Display all passwords
            password_message = f"✅ Approved {approved_count} request(s). WRITE DOWN THESE PASSWORDS:\n\n" + "\n".join(passwords_info)
            self.message_user(request, password_message, level='success')
        else:
            self.message_user(request, "No pending requests were selected.", level='warning')
    
    approve_requests.short_description = "✅ Approve selected requests"
    
    def reject_requests(self, request, queryset):
        """Admin action to reject access requests"""
        from django.utils import timezone
        
        rejected_count = 0
        for access_request in queryset.filter(status='pending'):
            access_request.status = 'rejected'
            access_request.reviewed_at = timezone.now()
            access_request.reviewed_by = request.user.username
            access_request.save()
            rejected_count += 1
        
        if rejected_count > 0:
            self.message_user(request, f"❌ Rejected {rejected_count} request(s).", level='success')
        else:
            self.message_user(request, "No pending requests were selected.", level='warning')
    
    reject_requests.short_description = "❌ Reject selected requests"


@admin.register(DailyJournal)
class DailyJournalAdmin(ImportExportModelAdmin):
    list_display = ['date', 'user', 'title', 'is_pinned', 'created_at', 'updated_at']
    list_filter = ['is_pinned', 'date', 'created_at', 'user']
    search_fields = ['title', 'content', 'user__username', 'tags']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    fieldsets = (
        ('Journal Entry', {
            'fields': ('user', 'date', 'title', 'content', 'is_pinned')
        }),
        ('Metadata', {
            'fields': ('tags', 'created_at', 'updated_at')
        }),
    )


@admin.register(JournalComment)
class JournalCommentAdmin(ImportExportModelAdmin):
    list_display = ['journal', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['comment', 'user__username', 'journal__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'
