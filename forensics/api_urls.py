from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    CaseViewSet, PersonViewSet, CasePersonViewSet,
    EvidenceViewSet, EvidenceTransferViewSet, EvidenceImageViewSet,
    DocumentViewSet, TaskViewSet, TimelineActivityViewSet,
    NotificationViewSet, UserProfileViewSet, AccessRequestViewSet
)
from .api_root import api_root

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'cases', CaseViewSet, basename='case')
router.register(r'persons', PersonViewSet, basename='person')
router.register(r'case-persons', CasePersonViewSet, basename='caseperson')
router.register(r'evidence', EvidenceViewSet, basename='evidence')
router.register(r'evidence-transfers', EvidenceTransferViewSet, basename='evidencetransfer')
router.register(r'evidence-images', EvidenceImageViewSet, basename='evidenceimage')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'timeline-activities', TimelineActivityViewSet, basename='timelineactivity')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')
router.register(r'access-requests', AccessRequestViewSet, basename='accessrequest')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
]
