from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import timedelta
from .models import Document, Case, Evidence
import json
from django.utils.safestring import mark_safe


@login_required
def document_analytics(request):
    """
    Document analytics dashboard showing comprehensive statistics and insights
    """
    # Total documents count
    total_documents = Document.objects.count()
    
    # Documents by type
    docs_by_type = Document.objects.values('document_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Convert to display format with labels
    docs_by_type_data = []
    for item in docs_by_type:
        doc_type = item['document_type']
        doc_type_display = dict(Document.TYPE_CHOICES).get(doc_type, doc_type)
        docs_by_type_data.append({
            'type': doc_type,
            'type_display': doc_type_display,
            'count': item['count']
        })
    
    # Documents by access level
    docs_by_access = Document.objects.values('access_level').annotate(
        count=Count('id')
    ).order_by('-count')
    
    docs_by_access_data = []
    for item in docs_by_access:
        access_level = item['access_level']
        access_display = dict(Document.ACCESS_CHOICES).get(access_level, access_level)
        docs_by_access_data.append({
            'level': access_level,
            'level_display': access_display,
            'count': item['count']
        })
    
    # Recent document activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_docs_count = Document.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Recent documents
    recent_documents = Document.objects.select_related('case', 'evidence').order_by('-created_at')[:10]
    
    # Documents per case (top 10 cases by document count)
    cases_with_doc_count = Case.objects.annotate(
        doc_count=Count('documents')
    ).filter(doc_count__gt=0).order_by('-doc_count')[:10]
    
    # Cases without documents
    cases_without_docs = Case.objects.annotate(
        doc_count=Count('documents')
    ).filter(doc_count=0, status='active').count()
    
    # Document Age Analysis
    from datetime import datetime
    now = timezone.now()
    
    # Documents older than 1 year
    one_year_ago = now - timedelta(days=365)
    very_old_docs = Document.objects.filter(
        created_at__lt=one_year_ago
    ).select_related('case', 'evidence').order_by('created_at')[:10]
    
    # Documents by age categories
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)
    one_eighty_days_ago = now - timedelta(days=180)
    
    age_analysis = {
        'very_recent': Document.objects.filter(created_at__gte=thirty_days_ago).count(),
        'recent': Document.objects.filter(created_at__lt=thirty_days_ago, created_at__gte=ninety_days_ago).count(),
        'moderate': Document.objects.filter(created_at__lt=ninety_days_ago, created_at__gte=one_eighty_days_ago).count(),
        'old': Document.objects.filter(created_at__lt=one_eighty_days_ago, created_at__gte=one_year_ago).count(),
        'very_old': Document.objects.filter(created_at__lt=one_year_ago).count(),
    }
    
    # Monthly document creation trend (last 12 months)
    from django.db.models.functions import TruncMonth
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_trend = Document.objects.filter(
        created_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Convert to chart-friendly format
    monthly_labels = [item['month'].strftime('%b %Y') for item in monthly_trend]
    monthly_counts = [item['count'] for item in monthly_trend]
    
    # Confidential documents count
    confidential_docs = Document.objects.filter(is_confidential=True).count()
    
    # Document completeness by case type
    # Check which required document types are missing for each case
    required_doc_types = ['ontvangstbewijs', 'intake', 'kvi', 'na-sporing', 'procesverbaal', 'rapport']
    
    # Get all active cases
    active_cases = Case.objects.filter(status='active')
    incomplete_cases = []
    
    for case in active_cases:
        case_docs = case.documents.values_list('document_type', flat=True)
        missing_types = [dt for dt in required_doc_types if dt not in case_docs]
        if missing_types:
            incomplete_cases.append({
                'case': case,
                'missing_types': [dict(Document.TYPE_CHOICES).get(dt, dt) for dt in missing_types]
            })
    
    # Sort by number of missing documents (most incomplete first)
    incomplete_cases.sort(key=lambda x: len(x['missing_types']), reverse=True)
    
    # Top 10 incomplete cases
    incomplete_cases = incomplete_cases[:10]
    
    # File size statistics
    from django.db.models import Sum, Avg
    total_file_size = Document.objects.aggregate(total=Sum('file_size'))['total'] or 0
    avg_file_size = Document.objects.aggregate(avg=Avg('file_size'))['avg'] or 0
    
    # Convert bytes to human readable format
    def human_readable_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"
    
    total_file_size_readable = human_readable_size(total_file_size)
    avg_file_size_readable = human_readable_size(avg_file_size)
    
    # Prepare chart data for JavaScript
    docs_by_type_labels = [item['type_display'] for item in docs_by_type_data]
    docs_by_type_counts = [item['count'] for item in docs_by_type_data]
    
    docs_by_access_labels = [item['level_display'] for item in docs_by_access_data]
    docs_by_access_counts = [item['count'] for item in docs_by_access_data]
    
    context = {
        'total_documents': total_documents,
        'docs_by_type_data': docs_by_type_data,
        'docs_by_access_data': docs_by_access_data,
        'recent_docs_count': recent_docs_count,
        'recent_documents': recent_documents,
        'cases_with_doc_count': cases_with_doc_count,
        'cases_without_docs': cases_without_docs,
        'very_old_docs': very_old_docs,
        'age_analysis': age_analysis,
        'confidential_docs': confidential_docs,
        'incomplete_cases': incomplete_cases,
        'total_file_size_readable': total_file_size_readable,
        'avg_file_size_readable': avg_file_size_readable,
        
        # JSON data for charts
        'docs_by_type_labels_json': mark_safe(json.dumps(docs_by_type_labels)),
        'docs_by_type_counts_json': mark_safe(json.dumps(docs_by_type_counts)),
        'docs_by_access_labels_json': mark_safe(json.dumps(docs_by_access_labels)),
        'docs_by_access_counts_json': mark_safe(json.dumps(docs_by_access_counts)),
        'monthly_labels_json': mark_safe(json.dumps(monthly_labels)),
        'monthly_counts_json': mark_safe(json.dumps(monthly_counts)),
        
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Document Analytics', 'url': None},
        ],
    }
    
    return render(request, 'forensics/document_analytics.html', context)


@login_required
def document_list(request):
    """
    Comprehensive document list with filtering and search
    """
    documents = Document.objects.select_related('case', 'evidence').all()
    
    # Search
    search = request.GET.get('search')
    if search:
        documents = documents.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(author__icontains=search) |
            Q(file_name__icontains=search) |
            Q(case__case_number__icontains=search) |
            Q(case__case_name__icontains=search)
        )
    
    # Filter by document type
    doc_type = request.GET.get('type')
    if doc_type:
        documents = documents.filter(document_type=doc_type)
    
    # Filter by access level
    access_level = request.GET.get('access_level')
    if access_level:
        documents = documents.filter(access_level=access_level)
    
    # Filter by case
    case_id = request.GET.get('case')
    if case_id:
        documents = documents.filter(case_id=case_id)
    
    # Filter by confidential status
    is_confidential = request.GET.get('confidential')
    if is_confidential == 'true':
        documents = documents.filter(is_confidential=True)
    elif is_confidential == 'false':
        documents = documents.filter(is_confidential=False)
    
    # Filter by author
    author = request.GET.get('author')
    if author:
        documents = documents.filter(author__icontains=author)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        from django.utils.dateparse import parse_date
        parsed_date = parse_date(date_from)
        if parsed_date:
            documents = documents.filter(date_created__gte=parsed_date)
    if date_to:
        from django.utils.dateparse import parse_date
        parsed_date = parse_date(date_to)
        if parsed_date:
            from datetime import time
            documents = documents.filter(
                date_created__lte=timezone.datetime.combine(parsed_date, time.max)
            )
    
    # Sorting
    sort_by = request.GET.get('sort', '-date_created')
    allowed_sorts = [
        'title', '-title',
        'document_type', '-document_type',
        'date_created', '-date_created',
        'author', '-author',
        'case__case_number', '-case__case_number'
    ]
    if sort_by in allowed_sorts:
        documents = documents.order_by(sort_by)
    else:
        documents = documents.order_by('-date_created')
    
    # Pagination
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except ValueError:
        per_page = 25
    
    paginator = Paginator(documents, per_page)
    page = request.GET.get('page')
    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)
    
    # Get filter options
    all_cases = Case.objects.all().order_by('-date_opened')
    all_authors = Document.objects.exclude(author='').values_list(
        'author', flat=True
    ).distinct().order_by('author')
    
    context = {
        'documents': documents,
        'search': search,
        'type_filter': doc_type,
        'access_level_filter': access_level,
        'case_filter': case_id,
        'confidential_filter': is_confidential,
        'author_filter': author,
        'date_from': date_from,
        'date_to': date_to,
        'per_page': per_page,
        'all_cases': all_cases,
        'all_authors': all_authors,
        'document_type_choices': Document.TYPE_CHOICES,
        'access_level_choices': Document.ACCESS_CHOICES,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Documents', 'url': None},
        ],
    }
    
    return render(request, 'forensics/document_list.html', context)


@login_required
def cases_without_documents(request):
    """
    View showing all active cases that don't have any documents, grouped by department
    """
    # Get all active cases without documents
    cases_list = Case.objects.annotate(
        doc_count=Count('documents')
    ).filter(doc_count=0, status='active').order_by('department', 'case_number')
    
    # Group cases by department
    from collections import defaultdict
    cases_by_dept = defaultdict(list)
    
    for case in cases_list:
        dept = case.department if case.department else 'unassigned'
        cases_by_dept[dept].append(case)
    
    # Convert to sorted list of tuples with department display names
    grouped_cases = []
    for dept_code, dept_cases in cases_by_dept.items():
        if dept_code == 'unassigned':
            dept_name = 'Unassigned'
        else:
            dept_name = dict(Case.DEPARTMENT_CHOICES).get(dept_code, dept_code)
        
        grouped_cases.append({
            'department_code': dept_code,
            'department_name': dept_name,
            'cases': dept_cases,
            'count': len(dept_cases)
        })
    
    # Sort by case count (descending), then by department name
    grouped_cases.sort(key=lambda x: (-x['count'], x['department_name']))
    
    context = {
        'grouped_cases': grouped_cases,
        'total_cases': cases_list.count(),
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Document Analytics', 'url': '/documents/analytics/'},
            {'name': 'Cases Without Documents', 'url': None},
        ],
    }
    
    return render(request, 'forensics/cases_without_documents.html', context)
