from rest_framework import serializers
from .models import (
    Case, Person, CasePerson, Evidence, EvidenceTransfer, 
    EvidenceImage, Document, Task, TimelineActivity, 
    Notification, UserProfile, AccessRequest
)


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'username', 'full_name', 'role', 
            'department', 'is_active', 'metadata', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'id', 'first_name', 'last_name', 'middle_name', 
            'date_of_birth', 'ssn', 'email', 'phone', 
            'address', 'city', 'state', 'zip_code', 'country', 
            'person_type', 'notes', 'aliases', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CasePersonSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source='person.__str__', read_only=True)
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    
    class Meta:
        model = CasePerson
        fields = [
            'id', 'case', 'case_number', 'person', 'person_name', 
            'role', 'involvement_description', 'date_added', 
            'is_primary', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EvidenceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceImage
        fields = [
            'id', 'evidence', 'image', 'caption', 
            'uploaded_at', 'uploaded_by'
        ]
        read_only_fields = ['id', 'uploaded_at']


class EvidenceTransferSerializer(serializers.ModelSerializer):
    evidence_number = serializers.CharField(source='evidence.evidence_number', read_only=True)
    
    class Meta:
        model = EvidenceTransfer
        fields = [
            'id', 'evidence', 'evidence_number', 
            'from_department', 'to_department', 
            'transferred_by', 'received_by', 
            'transfer_date', 'notes'
        ]
        read_only_fields = ['id']


class EvidenceSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    owner_name = serializers.CharField(source='owner_person.__str__', read_only=True)
    seized_from_name = serializers.CharField(source='seized_from_person.__str__', read_only=True)
    custodian_name = serializers.CharField(source='custodian_person.__str__', read_only=True)
    images = EvidenceImageSerializer(many=True, read_only=True)
    transfers = EvidenceTransferSerializer(many=True, read_only=True)
    
    class Meta:
        model = Evidence
        fields = [
            'id', 'evidence_number', 'ibs_number', 'case', 'case_number',
            'device_type', 'item_name', 'description', 'brand', 'model',
            'color', 'serial_number', 'imei', 'imei_numbers', 'location',
            'current_department', 'received_by', 'received_date',
            'status', 'state', 'damages', 'damage_description',
            'examiner_name', 'acquisition_date', 'acquisition_notes',
            'make', 'firmware_version', 'mac_address',
            'acquisition_method', 'acquisition_tool',
            'hash_algorithm', 'hash_verified', 'device_condition',
            'chain_of_custody_notes', 'forensic_image_path',
            'owner_person', 'owner_name',
            'seized_from_person', 'seized_from_name',
            'custodian_person', 'custodian_name',
            'seizure_authority', 'seizure_date', 'seizure_location',
            'collected_date', 'collected_by', 'location_found',
            'storage_location', 'file_path', 'file_size', 'file_type',
            'hash_md5', 'hash_sha1', 'hash_sha256',
            'device_specific_data', 'tags', 'notes',
            'images', 'transfers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CaseSerializer(serializers.ModelSerializer):
    evidence_count = serializers.SerializerMethodField()
    persons_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Case
        fields = [
            'id', 'case_number', 'case_name', 'description',
            'status', 'priority', 'case_type',
            'date_opened', 'date_closed', 'prosecutor', 
            'department', 'jurisdiction',
            'incident_date', 'incident_location', 
            'evidence_location', 'notes', 'tags',
            'evidence_count', 'persons_count', 'tasks_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'case_number', 'created_at', 'updated_at']
    
    def get_evidence_count(self, obj):
        return obj.evidence.count()
    
    def get_persons_count(self, obj):
        return obj.case_persons.count()
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()


class CaseDetailSerializer(CaseSerializer):
    """Detailed case serializer with nested relationships"""
    evidence = EvidenceSerializer(many=True, read_only=True)
    case_persons = CasePersonSerializer(many=True, read_only=True)
    
    class Meta(CaseSerializer.Meta):
        fields = CaseSerializer.Meta.fields + ['evidence', 'case_persons']


class DocumentSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    evidence_number = serializers.CharField(source='evidence.evidence_number', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'case', 'case_number', 'evidence', 'evidence_number',
            'document_type', 'title', 'description',
            'file_name', 'file_path', 'file_size', 'file_type',
            'author', 'date_created', 'version',
            'is_confidential', 'access_level', 'tags', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'case', 'case_number', 'task_name', 'description',
            'task_type', 'status', 'priority', 'assigned_to',
            'due_date', 'estimated_hours', 'actual_hours',
            'completion_percentage', 'dependencies', 'tags', 'notes',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TimelineActivitySerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    evidence_number = serializers.CharField(source='related_evidence.evidence_number', read_only=True)
    person_name = serializers.CharField(source='related_person.__str__', read_only=True)
    task_name = serializers.CharField(source='related_task.task_name', read_only=True)
    
    class Meta:
        model = TimelineActivity
        fields = [
            'id', 'case', 'case_number', 'activity_type',
            'title', 'description', 'activity_date', 'performed_by',
            'related_evidence', 'evidence_number',
            'related_person', 'person_name',
            'related_task', 'task_name',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'case', 'case_number', 'notification_type',
            'title', 'message', 'priority', 'recipient',
            'is_read', 'read_at', 'metadata',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class AccessRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True, allow_null=True)
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    evidence_number = serializers.CharField(source='evidence.evidence_number', read_only=True)
    
    class Meta:
        model = AccessRequest
        fields = [
            'id', 'requester', 'requester_name',
            'case', 'case_number', 
            'evidence', 'evidence_number',
            'reason', 'status', 
            'reviewer', 'reviewer_name',
            'review_notes', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'requester', 'created_at', 'updated_at', 'reviewed_at']
