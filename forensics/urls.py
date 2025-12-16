from django.urls import path
from . import views
from . import access_views
from . import journal_views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),

    # Cases
    path('cases/', views.case_list, name='case_list'),
    path('cases/export/', views.case_export_csv, name='case_export_csv'),
    path('cases/create/', views.case_create, name='case_create'),
    path('cases/<uuid:pk>/', views.case_detail, name='case_detail'),
    path('cases/<uuid:pk>/edit/', views.case_update, name='case_update'),
    path('cases/<uuid:pk>/delete/', views.case_delete, name='case_delete'),
    path('cases/<uuid:pk>/export/csv/', views.case_detail_export_csv, name='case_detail_export_csv'),
    path('cases/<uuid:pk>/export/print/', views.case_detail_export_print, name='case_detail_export_print'),

    # Persons
    path('persons/', views.person_list, name='person_list'),
    path('persons/create/', views.person_create, name='person_create'),
    path('persons/<uuid:pk>/', views.person_detail, name='person_detail'),
    path('persons/<uuid:pk>/edit/', views.person_update, name='person_update'),
    path('persons/<uuid:pk>/delete/', views.person_delete, name='person_delete'),

    # Evidence
    path('evidence/', views.evidence_list, name='evidence_list'),
    path('evidence/export/', views.evidence_export_csv, name='evidence_export_csv'),
    path('evidence/location-search/', views.evidence_location_search, name='evidence_location_search'),
    path('evidence/create/', views.evidence_create, name='evidence_create'),
    path('evidence/<uuid:pk>/', views.evidence_detail, name='evidence_detail'),
    path('evidence/<uuid:pk>/edit/', views.evidence_update, name='evidence_update'),
    path('evidence/<uuid:pk>/delete/', views.evidence_delete, name='evidence_delete'),
    path('evidence/<uuid:pk>/export/print/', views.evidence_detail_export_print, name='evidence_detail_export_print'),
    path('evidence/<uuid:pk>/print-label/', views.evidence_print_label, name='evidence_print_label'),
    path('evidence/<uuid:pk>/quick-update/', views.evidence_quick_update_department, name='evidence_quick_update'),
    path('evidence/bulk-update/', views.evidence_bulk_update, name='evidence_bulk_update'),
    
    # Access Requests
    path('request-access/', access_views.access_request_create, name='access_request_create'),
    path('access-requests/', access_views.access_request_list, name='access_request_list'),
    path('access-requests/<uuid:pk>/review/', access_views.access_request_review, name='access_request_review'),
    
    # Daily Journals
    path('journals/', journal_views.journal_list, name='journal_list'),
    path('journals/my/', journal_views.my_journals, name='my_journals'),
    path('journals/create/', journal_views.journal_create, name='journal_create'),
    path('journals/<uuid:pk>/', journal_views.journal_detail, name='journal_detail'),
    path('journals/<uuid:pk>/edit/', journal_views.journal_edit, name='journal_edit'),
    path('journals/<uuid:pk>/delete/', journal_views.journal_delete, name='journal_delete'),
    path('journal-comments/<uuid:pk>/delete/', journal_views.comment_delete, name='comment_delete'),
]
