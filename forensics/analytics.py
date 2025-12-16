"""Analytics module for forensics data"""
from django.db.models import Count, Q, F, Value, CharField
from django.db.models.functions import TruncMonth, TruncWeek, Coalesce
from django.utils import timezone
from datetime import timedelta
from .models import Case, Evidence


def get_date_range(period, start_date=None, end_date=None):
    """
    Get start and end date based on period or custom range.
    Period options: '1m', '3m', '6m', '1y', 'all', 'custom'
    Returns: (start_date, end_date) tuple
    """
    now = timezone.now()
    
    if period == 'custom' and (start_date or end_date):
        return (start_date, end_date)
    elif period == '1m':
        return (now - timedelta(days=30), now)
    elif period == '3m':
        return (now - timedelta(days=90), now)
    elif period == '6m':
        return (now - timedelta(days=180), now)
    elif period == '1y':
        return (now - timedelta(days=365), now)
    else:  # 'all'
        return (None, None)


def get_case_analytics(period='all', start_date=None, end_date=None, status_filter=None, priority_filter=None, department_filter=None):
    """Get case analytics for a given time period with filters"""
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Base queryset
    cases = Case.objects.all()
    if date_start:
        cases = cases.filter(date_opened__gte=date_start)
    if date_end:
        cases = cases.filter(date_opened__lte=date_end)
    if status_filter:
        cases = cases.filter(status=status_filter)
    if priority_filter:
        cases = cases.filter(priority=priority_filter)
    if department_filter:
        cases = cases.filter(department=department_filter)
    
    # Total counts
    total_cases = cases.count()
    active_cases = cases.filter(status='active').count()
    closed_cases = cases.filter(status='closed').count()
    suspended_cases = cases.filter(status='suspended').count()
    archived_cases = cases.filter(status='archived').count()
    
    # Status distribution
    status_distribution = cases.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Priority distribution
    priority_distribution = cases.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    # Case type distribution
    case_type_distribution = cases.exclude(case_type='').values('case_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Department distribution
    department_distribution = cases.exclude(department='').values('department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly trend (for charts)
    monthly_trend = cases.annotate(
        month=TruncMonth('date_opened')
    ).values('month').annotate(
        opened=Count('id'),
        closed=Count('id', filter=Q(status='closed'))
    ).order_by('month')
    
    # Average case duration (for closed cases)
    closed_with_dates = cases.filter(
        status='closed',
        date_closed__isnull=False
    )
    
    avg_duration_days = None
    if closed_with_dates.exists():
        total_duration = sum([
            (case.date_closed - case.date_opened).days 
            for case in closed_with_dates
        ])
        avg_duration_days = total_duration / closed_with_dates.count()
    
    # Top prosecutors
    top_prosecutors = cases.exclude(prosecutor='').values('prosecutor').annotate(
        case_count=Count('id')
    ).order_by('-case_count')[:5]
    
    return {
        'total_cases': total_cases,
        'active_cases': active_cases,
        'closed_cases': closed_cases,
        'suspended_cases': suspended_cases,
        'archived_cases': archived_cases,
        'status_distribution': list(status_distribution),
        'priority_distribution': list(priority_distribution),
        'case_type_distribution': list(case_type_distribution),
        'department_distribution': list(department_distribution),
        'monthly_trend': list(monthly_trend),
        'avg_duration_days': round(avg_duration_days, 1) if avg_duration_days else None,
        'top_prosecutors': list(top_prosecutors),
    }


def get_evidence_analytics(period='all', start_date=None, end_date=None, status_filter=None, device_type_filter=None):
    """Get evidence analytics for a given time period with filters"""
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Base queryset
    evidence = Evidence.objects.all()
    if date_start:
        evidence = evidence.filter(collected_date__gte=date_start)
    if date_end:
        evidence = evidence.filter(collected_date__lte=date_end)
    if status_filter:
        evidence = evidence.filter(status=status_filter)
    if device_type_filter:
        evidence = evidence.filter(device_type=device_type_filter)
    
    # Total counts
    total_evidence = evidence.count()
    by_status = {
        'collected': evidence.filter(status='collected').count(),
        'processing': evidence.filter(status='processing').count(),
        'analyzed': evidence.filter(status='analyzed').count(),
        'reviewed': evidence.filter(status='reviewed').count(),
        'archived': evidence.filter(status='archived').count(),
        'returned': evidence.filter(status='returned').count(),
        'destroyed': evidence.filter(status='destroyed').count(),
    }
    
    # Device type distribution
    device_type_distribution = evidence.values('device_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Status distribution
    status_distribution = evidence.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Department distribution (current location)
    department_distribution = evidence.values('current_department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly collection trend
    monthly_trend = evidence.annotate(
        month=TruncMonth('collected_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Evidence with/without case assignment
    assigned_to_case = evidence.filter(case__isnull=False).count()
    unassigned = evidence.filter(case__isnull=True).count()
    
    # Evidence with IBS numbers
    with_ibs = evidence.exclude(ibs_number='').count()
    without_ibs = evidence.filter(ibs_number='').count()
    
    # Top device types
    top_device_types = evidence.values('device_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Evidence by examiner
    top_examiners = evidence.exclude(examiner_name='').values('examiner_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return {
        'total_evidence': total_evidence,
        'by_status': by_status,
        'device_type_distribution': list(device_type_distribution),
        'status_distribution': list(status_distribution),
        'department_distribution': list(department_distribution),
        'monthly_trend': list(monthly_trend),
        'assigned_to_case': assigned_to_case,
        'unassigned': unassigned,
        'with_ibs': with_ibs,
        'without_ibs': without_ibs,
        'top_device_types': list(top_device_types),
        'top_examiners': list(top_examiners),
    }


def get_combined_analytics(period='all', start_date=None, end_date=None, 
                          case_status=None, case_priority=None, case_department=None,
                          evidence_status=None, evidence_device_type=None):
    """Get combined analytics including both cases and evidence with filters"""
    case_data = get_case_analytics(period, start_date, end_date, case_status, case_priority, case_department)
    evidence_data = get_evidence_analytics(period, start_date, end_date, evidence_status, evidence_device_type)
    
    # Calculate additional combined metrics
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Average evidence per case
    cases = Case.objects.all()
    if date_start:
        cases = cases.filter(date_opened__gte=date_start)
    if date_end:
        cases = cases.filter(date_opened__lte=date_end)
    if case_status:
        cases = cases.filter(status=case_status)
    if case_priority:
        cases = cases.filter(priority=case_priority)
    if case_department:
        cases = cases.filter(department=case_department)
    
    total_cases = cases.count()
    total_evidence_in_cases = Evidence.objects.filter(case__isnull=False)
    if date_start:
        total_evidence_in_cases = total_evidence_in_cases.filter(collected_date__gte=date_start)
    if date_end:
        total_evidence_in_cases = total_evidence_in_cases.filter(collected_date__lte=date_end)
    if evidence_status:
        total_evidence_in_cases = total_evidence_in_cases.filter(status=evidence_status)
    if evidence_device_type:
        total_evidence_in_cases = total_evidence_in_cases.filter(device_type=evidence_device_type)
    
    avg_evidence_per_case = None
    if total_cases > 0:
        avg_evidence_per_case = round(total_evidence_in_cases.count() / total_cases, 2)
    
    # Cases with no evidence
    cases_without_evidence = cases.annotate(
        evidence_count=Count('evidence')
    ).filter(evidence_count=0).count()
    
    return {
        'period': period,
        'case_analytics': case_data,
        'evidence_analytics': evidence_data,
        'avg_evidence_per_case': avg_evidence_per_case,
        'cases_without_evidence': cases_without_evidence,
    }


def get_comparison_analytics():
    """Get comparison analytics for multiple time periods"""
    periods = ['1m', '3m', '6m', '1y', 'all']
    comparison = {}
    
    for period in periods:
        comparison[period] = {
            'cases': get_case_analytics(period)['total_cases'],
            'evidence': get_evidence_analytics(period)['total_evidence'],
        }
    
    return comparison


def get_team_statistics(period='all', start_date=None, end_date=None):
    """Get detailed statistics broken down by team/department"""
    from django.db.models import Q
    
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Get all departments from Case model
    departments = Case.DEPARTMENT_CHOICES
    team_stats = []
    
    for dept_code, dept_name in departments:
        # Filter cases by department
        dept_cases = Case.objects.filter(department=dept_code)
        if date_start:
            dept_cases = dept_cases.filter(date_opened__gte=date_start)
        if date_end:
            dept_cases = dept_cases.filter(date_opened__lte=date_end)
        
        total_cases = dept_cases.count()
        
        if total_cases == 0:
            continue  # Skip departments with no cases
        
        # Case status breakdown
        active_cases = dept_cases.filter(status='active').count()
        closed_cases = dept_cases.filter(status='closed').count()
        suspended_cases = dept_cases.filter(status='suspended').count()
        archived_cases = dept_cases.filter(status='archived').count()
        
        # Priority breakdown
        critical_cases = dept_cases.filter(priority='critical').count()
        high_cases = dept_cases.filter(priority='high').count()
        
        # Evidence for this department's cases
        dept_evidence = Evidence.objects.filter(case__in=dept_cases)
        if date_start:
            dept_evidence = dept_evidence.filter(collected_date__gte=date_start)
        if date_end:
            dept_evidence = dept_evidence.filter(collected_date__lte=date_end)
        
        total_evidence = dept_evidence.count()
        avg_evidence_per_case = round(total_evidence / total_cases, 2) if total_cases > 0 else 0
        
        # Evidence status breakdown
        evidence_collected = dept_evidence.filter(status='collected').count()
        evidence_processing = dept_evidence.filter(status='processing').count()
        evidence_analyzed = dept_evidence.filter(status='analyzed').count()
        
        team_stats.append({
            'department_code': dept_code,
            'department_name': dept_name,
            'total_cases': total_cases,
            'active_cases': active_cases,
            'closed_cases': closed_cases,
            'suspended_cases': suspended_cases,
            'archived_cases': archived_cases,
            'critical_cases': critical_cases,
            'high_priority_cases': high_cases,
            'total_evidence': total_evidence,
            'avg_evidence_per_case': avg_evidence_per_case,
            'evidence_collected': evidence_collected,
            'evidence_processing': evidence_processing,
            'evidence_analyzed': evidence_analyzed,
        })
    
    # Sort by total cases descending
    team_stats.sort(key=lambda x: x['total_cases'], reverse=True)
    
    return team_stats
