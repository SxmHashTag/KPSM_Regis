from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Case, Person, CasePerson, Evidence, EvidenceTransfer,
    EvidenceImage, Document, Task, TimelineActivity,
    Notification, UserProfile, AccessRequest
)
from .serializers import (
    CaseSerializer, CaseDetailSerializer, PersonSerializer,
    CasePersonSerializer, EvidenceSerializer, EvidenceTransferSerializer,
    EvidenceImageSerializer, DocumentSerializer, TaskSerializer,
    TimelineActivitySerializer, NotificationSerializer,
    UserProfileSerializer, AccessRequestSerializer
)


class CaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing forensic cases.
    """
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'case_type', 'department']
    search_fields = ['case_number', 'case_name', 'description', 'prosecutor']
    ordering_fields = ['date_opened', 'date_closed', 'created_at', 'case_number']
    ordering = ['-date_opened']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CaseDetailSerializer
        return CaseSerializer
    
    @action(detail=True, methods=['get'])
    def evidence(self, request, pk=None):
        """Get all evidence for a specific case"""
        case = self.get_object()
        evidence = case.evidence.all()
        serializer = EvidenceSerializer(evidence, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def persons(self, request, pk=None):
        """Get all persons associated with a specific case"""
        case = self.get_object()
        case_persons = case.case_persons.all()
        serializer = CasePersonSerializer(case_persons, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for a specific case"""
        case = self.get_object()
        tasks = case.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class PersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing persons (suspects, victims, witnesses, etc.).
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['person_type', 'city', 'state', 'country']
    search_fields = ['first_name', 'last_name', 'middle_name', 'email', 'ssn']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']


class CasePersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing case-person relationships.
    """
    queryset = CasePerson.objects.all()
    serializer_class = CasePersonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['case', 'person', 'role', 'is_primary']
    ordering_fields = ['date_added', 'created_at']
    ordering = ['-date_added']


class EvidenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing evidence items.
    """
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'case', 'device_type', 'status', 'state', 
        'current_department', 'damages'
    ]
    search_fields = [
        'evidence_number', 'ibs_number', 'item_name', 
        'description', 'serial_number', 'imei', 'brand', 'model'
    ]
    ordering_fields = ['collected_date', 'created_at', 'evidence_number']
    ordering = ['-collected_date']
    
    @action(detail=True, methods=['get'])
    def transfers(self, request, pk=None):
        """Get chain of custody transfers for specific evidence"""
        evidence = self.get_object()
        transfers = evidence.transfers.all()
        serializer = EvidenceTransferSerializer(transfers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all images for specific evidence"""
        evidence = self.get_object()
        images = evidence.images.all()
        serializer = EvidenceImageSerializer(images, many=True)
        return Response(serializer.data)


class EvidenceTransferViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing evidence transfers (chain of custody).
    """
    queryset = EvidenceTransfer.objects.all()
    serializer_class = EvidenceTransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['evidence', 'from_department', 'to_department']
    ordering_fields = ['transfer_date', 'created_at']
    ordering = ['-transfer_date']


class EvidenceImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing evidence images.
    """
    queryset = EvidenceImage.objects.all()
    serializer_class = EvidenceImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['evidence']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing case documents.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'case', 'evidence', 'document_type', 
        'is_confidential', 'access_level'
    ]
    search_fields = ['title', 'description', 'author', 'file_name']
    ordering_fields = ['date_created', 'created_at']
    ordering = ['-date_created']


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing investigation tasks.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['case', 'task_type', 'status', 'priority', 'assigned_to']
    search_fields = ['task_name', 'description', 'assigned_to']
    ordering_fields = ['due_date', 'created_at', 'priority']
    ordering = ['-created_at']


class TimelineActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing timeline activities.
    """
    queryset = TimelineActivity.objects.all()
    serializer_class = TimelineActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['case', 'activity_type', 'related_evidence', 'related_person']
    search_fields = ['title', 'description', 'performed_by']
    ordering_fields = ['activity_date', 'created_at']
    ordering = ['-activity_date']


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notifications.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['case', 'notification_type', 'priority', 'is_read']
    ordering_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.is_read = True
        from django.utils import timezone
        notification.read_at = timezone.now()
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user profiles.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['username', 'full_name']
    ordering_fields = ['created_at', 'full_name']
    ordering = ['full_name']


class AccessRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing access requests.
    """
    queryset = AccessRequest.objects.all()
    serializer_class = AccessRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'requester', 'case', 'evidence']
    ordering_fields = ['created_at', 'reviewed_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an access request"""
        access_request = self.get_object()
        access_request.status = 'approved'
        access_request.reviewer = request.user
        from django.utils import timezone
        access_request.reviewed_at = timezone.now()
        access_request.review_notes = request.data.get('review_notes', '')
        access_request.save()
        serializer = self.get_serializer(access_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny an access request"""
        access_request = self.get_object()
        access_request.status = 'denied'
        access_request.reviewer = request.user
        from django.utils import timezone
        access_request.reviewed_at = timezone.now()
        access_request.review_notes = request.data.get('review_notes', '')
        access_request.save()
        serializer = self.get_serializer(access_request)
        return Response(serializer.data)
