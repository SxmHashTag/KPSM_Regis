from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import csv
from django.db import models, IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Case, Person, Evidence, EvidenceImage, EvidenceTransfer, Document
from . import analytics


def _extract_device_specific_data(post_data):
    """Extract device-specific fields from POST data"""
    device_specific_fields = [
        # Computer fields
        'computer_type', 'os_type', 'os_version', 'cpu', 'ram', 'storage_type',
        'storage_capacity', 'encryption_status', 'write_blocker_used',
        # Mobile fields
        'mobile_os_type', 'mobile_os_version', 'sim_status', 'lock_status', 'battery_level',
        # Storage fields
        'storage_device_type', 'capacity', 'connection_interface', 'filesystem',
        # Network fields
        'network_device_type', 'network_ip_address', 'subnet_mask', 'admin_access_method',
        # Cloud fields
        'service_provider', 'account_identifier', 'legal_authority', 'access_method',
        # Car fields
        'vehicle_make', 'vehicle_model', 'vehicle_year', 'vin_number', 'license_plate', 'odometer',
        # Video fields
        'video_source_type', 'camera_location', 'video_format', 'resolution', 'duration', 'frame_rate', 'date_diff_value', 'time_diff_value',
        # Gaming fields
        'console_type', 'account_username',
        # Drone fields
        'drone_storage_type', 'controller_serial',
        # IoT fields
        'iot_device_type', 'network_type',
        # Memory fields
        'memory_type', 'system_state', 'memory_size', 'acquisition_duration',
    ]
    
    device_data = {}
    for field in device_specific_fields:
        value = post_data.get(field)
        if value and value.strip():  # Only add non-empty values
            # Handle checkbox for write_blocker_used
            if field == 'write_blocker_used':
                device_data[field] = True
            else:
                device_data[field] = value.strip()
    
    # Handle multiple SIM cards (array data)
    sim_iccids = post_data.getlist('sim_iccid[]')
    sim_imsis = post_data.getlist('sim_imsi[]')
    sim_phone_numbers = post_data.getlist('sim_phone_number[]')
    sim_carriers = post_data.getlist('sim_carrier[]')
    sim_types = post_data.getlist('sim_type[]')
    sim_pin_statuses = post_data.getlist('sim_pin_status[]')
    sim_notes_list = post_data.getlist('sim_notes[]')
    
    # Build SIM cards array if any SIM data exists
    if any([sim_iccids, sim_imsis, sim_phone_numbers, sim_carriers, sim_types, sim_pin_statuses, sim_notes_list]):
        sim_cards = []
        # Get the maximum length to handle all SIM cards
        max_length = max(
            len(sim_iccids),
            len(sim_imsis),
            len(sim_phone_numbers),
            len(sim_carriers),
            len(sim_types),
            len(sim_pin_statuses),
            len(sim_notes_list)
        )
        
        for i in range(max_length):
            sim_card = {}
            if i < len(sim_iccids) and sim_iccids[i].strip():
                sim_card['iccid'] = sim_iccids[i].strip()
            if i < len(sim_imsis) and sim_imsis[i].strip():
                sim_card['imsi'] = sim_imsis[i].strip()
            if i < len(sim_phone_numbers) and sim_phone_numbers[i].strip():
                sim_card['phone_number'] = sim_phone_numbers[i].strip()
            if i < len(sim_carriers) and sim_carriers[i].strip():
                sim_card['carrier'] = sim_carriers[i].strip()
            if i < len(sim_types) and sim_types[i].strip():
                sim_card['sim_type'] = sim_types[i].strip()
            if i < len(sim_pin_statuses) and sim_pin_statuses[i].strip():
                sim_card['pin_status'] = sim_pin_statuses[i].strip()
            if i < len(sim_notes_list) and sim_notes_list[i].strip():
                sim_card['notes'] = sim_notes_list[i].strip()
            
            # Only add SIM card if it has at least one field
            if sim_card:
                sim_cards.append(sim_card)
        
        if sim_cards:
            device_data['sim_cards'] = sim_cards
    
    return device_data


# Dashboard
@login_required
def dashboard(request):
    """Main dashboard with statistics and recent activity"""
    search = request.GET.get('search')
    search_results = None
    
    if search:
        # Search across cases, persons, and evidence
        cases = Case.objects.filter(
            models.Q(case_number__icontains=search) |
            models.Q(case_name__icontains=search) |
            models.Q(prosecutor__icontains=search)
        )[:10]
        
        persons = Person.objects.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )[:10]
        
        evidence = Evidence.objects.filter(
            models.Q(evidence_number__icontains=search) |
            models.Q(ibs_number__icontains=search) |
            models.Q(item_name__icontains=search) |
            models.Q(brand__icontains=search) |
            models.Q(model__icontains=search) |
            models.Q(serial_number__icontains=search) |
            models.Q(imei__icontains=search)
        )[:10]
        
        search_results = {
            'cases': cases,
            'persons': persons,
            'evidence': evidence,
            'total': cases.count() + persons.count() + evidence.count(),
        }
    
    # Analytics Data
    # 1. Case Status Distribution
    case_status_data = Case.objects.values('status').annotate(count=Count('id')).order_by('status')
    case_status_labels = [item['status'].title() for item in case_status_data]
    case_status_counts = [item['count'] for item in case_status_data]
    
    # 2. Evidence by Device Type
    evidence_device_data = Evidence.objects.values('device_type').annotate(count=Count('id')).order_by('-count')[:10]
    evidence_device_labels = [dict(Evidence.DEVICE_TYPE_CHOICES).get(item['device_type'], item['device_type']) for item in evidence_device_data]
    evidence_device_counts = [item['count'] for item in evidence_device_data]
    # Combine labels and counts for easier template rendering
    evidence_by_type = [{'name': label, 'count': count} for label, count in zip(evidence_device_labels, evidence_device_counts)]
    
    # 3. Monthly Activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    cases_this_month = Case.objects.filter(date_opened__gte=thirty_days_ago).count()
    evidence_this_month = Evidence.objects.filter(collected_date__gte=thirty_days_ago).count()
    
    # Cases closed this month
    cases_closed_this_month = Case.objects.filter(
        status='closed',
        date_closed__gte=thirty_days_ago
    ).count()
    
    # 4. High Priority and Overdue Cases
    high_priority_cases = Case.objects.filter(
        priority__in=['high', 'critical'],
        status='active'
    ).order_by('-priority', 'date_opened')[:5]
    
    # Overdue cases (active for more than 90 days)
    ninety_days_ago = timezone.now() - timedelta(days=90)
    overdue_cases = Case.objects.filter(
        status='active',
        date_opened__lte=ninety_days_ago
    ).order_by('date_opened')[:5]
    
    # 5. Department inventory stats (by current location)
    department_stats = {}
    for code, name in Evidence.DEPARTMENT_CHOICES:
        department_stats[code] = {
            'name': name,
            'count': Evidence.objects.filter(current_department=code).count()
        }
    department_stats['unassigned'] = {
        'name': 'Unassigned',
        'count': Evidence.objects.filter(current_department='').count()
    }
    
    # 6. Recent activity (last 10 evidence items)
    recent_activity = Evidence.objects.select_related('case').prefetch_related('images').order_by('-created_at')[:10]
    
    context = {
        'total_cases': Case.objects.count(),
        'active_cases': Case.objects.filter(status='active').count(),
        'total_persons': Person.objects.count(),
        'total_evidence': Evidence.objects.count(),
        'recent_cases': Case.objects.all()[:5],
        'critical_cases': Case.objects.filter(priority='critical')[:5],
        'recent_evidence': Evidence.objects.all()[:5],
        'search': search,
        'search_results': search_results,
        # Analytics
        'case_status_labels': case_status_labels,
        'case_status_counts': case_status_counts,
        'evidence_device_labels': evidence_device_labels,
        'evidence_device_counts': evidence_device_counts,
        'evidence_by_type': evidence_by_type,
        'cases_this_month': cases_this_month,
        'evidence_this_month': evidence_this_month,
        'cases_closed_this_month': cases_closed_this_month,
        'high_priority_cases': high_priority_cases,
        'overdue_cases': overdue_cases,
        'department_stats': department_stats,
        'recent_activity': recent_activity,
    }
    return render(request, 'forensics/dashboard.html', context)


# Cases Views
@login_required
def case_list(request):
    """List all cases with filtering"""
    cases = Case.objects.all()
    
    # Search
    search = request.GET.get('search')
    if search:
        cases = cases.filter(
            models.Q(case_number__icontains=search) |
            models.Q(case_name__icontains=search) |
            models.Q(prosecutor__icontains=search) |
            models.Q(description__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        cases = cases.filter(status=status)
    
    # Filter by priority
    priority = request.GET.get('priority')
    if priority:
        cases = cases.filter(priority=priority)
    
    # Filter by department/team
    department = request.GET.get('department')
    if department:
        cases = cases.filter(department=department)
    
    # Filter by case type
    case_type = request.GET.get('case_type')
    if case_type:
        cases = cases.filter(case_type=case_type)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        from django.utils.dateparse import parse_date
        parsed_date = parse_date(date_from)
        if parsed_date:
            cases = cases.filter(date_opened__gte=parsed_date)
    if date_to:
        from django.utils.dateparse import parse_date
        parsed_date = parse_date(date_to)
        if parsed_date:
            from datetime import time
            cases = cases.filter(date_opened__lte=timezone.datetime.combine(parsed_date, time.max))
    
    # Sorting
    sort_by = request.GET.get('sort', '-date_opened')
    allowed_sorts = ['case_number', '-case_number', 'case_name', '-case_name', 'date_opened', '-date_opened', 'status', '-status', 'priority', '-priority']
    if sort_by in allowed_sorts:
        cases = cases.order_by(sort_by)
    else:
        cases = cases.order_by('-date_opened')

    # Pagination
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except ValueError:
        per_page = 25
    
    paginator = Paginator(cases, per_page)
    page = request.GET.get('page')
    try:
        cases = paginator.page(page)
    except PageNotAnInteger:
        cases = paginator.page(1)
    except EmptyPage:
        cases = paginator.page(paginator.num_pages)
    
    context = {
        'cases': cases,
        'search': search,
        'status_filter': status,
        'priority_filter': priority,
        'department_filter': department,
        'case_type_filter': case_type,
        'date_from': date_from,
        'date_to': date_to,
        'department_choices': Case.DEPARTMENT_CHOICES,
        'case_type_choices': Case.TYPE_CHOICES,
        'per_page': per_page,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': None},
        ],
    }
    return render(request, 'forensics/case_list.html', context)


@login_required
def case_detail(request, pk):
    """Detailed view of a case with all related information"""
    case = get_object_or_404(Case, pk=pk)
    
    # Get all documents: case documents + evidence documents
    evidence_docs = Document.objects.filter(evidence__case=case)
    case_docs = case.documents.all()
    all_documents = (case_docs | evidence_docs).distinct().order_by('-date_created')
    
    # Count unique persons from case and evidence
    case_person_ids = set(case.case_persons.values_list('person_id', flat=True))
    evidence_person_ids = set()
    for evidence in case.evidence.all():
        if evidence.owner_person_id:
            evidence_person_ids.add(evidence.owner_person_id)
        if evidence.seized_from_person_id:
            evidence_person_ids.add(evidence.seized_from_person_id)
        if evidence.custodian_person_id:
            evidence_person_ids.add(evidence.custodian_person_id)
    all_person_ids = case_person_ids | evidence_person_ids
    
    context = {
        'case': case,
        'evidence': case.evidence.all(),
        'persons': case.case_persons.all(),
        'persons_count': len(all_person_ids),
        'documents': case.documents.all(),
        'all_documents': all_documents,
        'tasks': case.tasks.all(),
        'timeline': case.timeline_activities.all()[:10],
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'}, 
            {'name': 'Cases', 'url': '/cases/'},
            {'name': case.case_number, 'url': None},
        ],
    }
    return render(request, 'forensics/case_detail.html', context)


@login_required
def case_create(request):
    """Create a new case"""
    if request.method == 'POST':
        case_number = request.POST.get('case_number', '').strip()
        
        try:
            case = Case.objects.create(
                case_number=case_number if case_number else '',  # Will auto-generate if empty
                case_name=request.POST.get('case_name'),
                description=request.POST.get('description', ''),
                status=request.POST.get('status', 'active'),
                priority=request.POST.get('priority', 'medium'),
                case_type=request.POST.get('case_type', ''),
                prosecutor=request.POST.get('prosecutor', ''),
                department=request.POST.get('department', ''),
            )
            messages.success(request, f'Case {case.case_number} created successfully!')
            return redirect('case_detail', pk=case.pk)
        except IntegrityError:
            # Duplicate case number
            messages.error(request, f'Case number "{case_number}" already exists. Please use a different case number.')
            # Re-render form with user's data preserved
            prosecutors = Case.objects.exclude(prosecutor='').values_list('prosecutor', flat=True).distinct().order_by('prosecutor')
            context = {
                'prosecutors': prosecutors,
                'form_data': request.POST,
                'breadcrumbs': [
                    {'name': 'Dashboard', 'url': '/'},
                    {'name': 'Cases', 'url': '/cases/'},
                    {'name': 'New Case', 'url': None},
                ],
            }
            return render(request, 'forensics/case_form.html', context)
    
    # Get distinct prosecutors from existing cases
    prosecutors = Case.objects.exclude(prosecutor='').values_list('prosecutor', flat=True).distinct().order_by('prosecutor')
    
    context = {
        'prosecutors': prosecutors,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': '/cases/'},
            {'name': 'New Case', 'url': None},
        ],
    }
    return render(request, 'forensics/case_form.html', context)


@login_required
def case_update(request, pk):
    """Update an existing case"""
    case = get_object_or_404(Case, pk=pk)
    
    if request.method == 'POST':
        # Get the new case number
        new_case_number = request.POST.get('case_number', '').strip()
        
        # Only update case_number if it's provided and different from current
        if new_case_number and new_case_number != case.case_number:
            # Check if new case number already exists
            if Case.objects.filter(case_number=new_case_number).exclude(pk=case.pk).exists():
                messages.error(request, f'Case number "{new_case_number}" already exists. Please choose a different number.')
                # Get distinct prosecutors for the error case
                prosecutors = Case.objects.exclude(prosecutor='').values_list('prosecutor', flat=True).distinct().order_by('prosecutor')
                context = {
                    'case': case,
                    'prosecutors': prosecutors,
                    'breadcrumbs': [
                        {'name': 'Dashboard', 'url': '/'},
                        {'name': 'Cases', 'url': '/cases/'},
                        {'name': case.case_number, 'url': f'/cases/{case.pk}/'},
                        {'name': 'Edit', 'url': None},
                    ],
                }
                return render(request, 'forensics/case_form.html', context)
            case.case_number = new_case_number
        
        case.case_name = request.POST.get('case_name')
        case.description = request.POST.get('description', '')
        case.status = request.POST.get('status')
        case.priority = request.POST.get('priority')
        case.case_type = request.POST.get('case_type', '')
        case.prosecutor = request.POST.get('prosecutor', '')
        case.department = request.POST.get('department', '')
        case.save()
        
        messages.success(request, 'Case updated successfully!')
        return redirect('case_detail', pk=case.pk)
    
    # Get distinct prosecutors from existing cases
    prosecutors = Case.objects.exclude(prosecutor='').values_list('prosecutor', flat=True).distinct().order_by('prosecutor')
    
    context = {
        'case': case,
        'prosecutors': prosecutors,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': '/cases/'},
            {'name': case.case_number, 'url': f'/cases/{case.pk}/'},
            {'name': 'Edit', 'url': None},
        ],
    }
    return render(request, 'forensics/case_form.html', context)


@login_required
def case_delete(request, pk):
    """Delete a case"""
    case = get_object_or_404(Case, pk=pk)
    
    if request.method == 'POST':
        case_number = case.case_number
        case.delete()
        messages.success(request, f'Case {case_number} deleted successfully!')
        return redirect('case_list')
    
    return render(request, 'forensics/case_confirm_delete.html', {'case': case})


@login_required
def case_detail_export_csv(request, pk):
    """Export case details with evidence to CSV"""
    case = get_object_or_404(Case, pk=pk)
    evidence_items = case.evidence.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="case_{case.case_number}_details.csv"'
    
    writer = csv.writer(response)
    
    # Case information section
    writer.writerow(['CASE DETAILS'])
    writer.writerow(['Case Number', case.case_number])
    writer.writerow(['Case Name', case.case_name])
    writer.writerow(['Status', case.get_status_display()])
    writer.writerow(['Priority', case.get_priority_display()])
    writer.writerow(['Case Type', case.get_case_type_display() if case.case_type else ''])
    writer.writerow(['Prosecutor', case.prosecutor])
    writer.writerow(['Date Opened', case.date_opened.strftime('%Y-%m-%d %H:%M')])
    if case.date_closed:
        writer.writerow(['Date Closed', case.date_closed.strftime('%Y-%m-%d %H:%M')])
    writer.writerow(['Description', case.description])
    writer.writerow([])
    
    # Evidence section
    writer.writerow(['EVIDENCE ITEMS'])
    writer.writerow([
        'Evidence Number', 'IBS Number', 'Item Name', 'Device Type', 'Brand', 'Model', 
        'Serial Number', 'IMEI', 'Status', 'Department', 'Collected Date', 'Examiner'
    ])
    
    for evidence in evidence_items:
        writer.writerow([
            evidence.evidence_number,
            evidence.ibs_number,
            evidence.item_name,
            evidence.get_device_type_display(),
            evidence.brand,
            evidence.model,
            evidence.serial_number,
            evidence.imei,
            evidence.get_status_display(),
            evidence.get_current_department_display() if evidence.current_department else '',
            evidence.collected_date.strftime('%Y-%m-%d %H:%M'),
            evidence.examiner_name
        ])
    
    return response


@login_required
def case_detail_export_print(request, pk):
    """Export case details to print-friendly HTML page"""
    case = get_object_or_404(Case, pk=pk)
    evidence_items = case.evidence.prefetch_related('images').all()
    persons = case.case_persons.select_related('person').all()
    
    context = {
        'case': case,
        'evidence_items': evidence_items,
        'persons': persons,
    }
    return render(request, 'forensics/case_detail_print.html', context)


# Person Views
@login_required
def person_list(request):
    """List all persons"""
    persons = Person.objects.all()
    
    # Search
    search = request.GET.get('search')
    if search:
        persons = persons.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(phone__icontains=search)
        )
    
    # Filter by person type
    person_type = request.GET.get('type')
    if person_type:
        persons = persons.filter(person_type=person_type)
    
    # Pagination
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except ValueError:
        per_page = 25
    
    paginator = Paginator(persons, per_page)
    page = request.GET.get('page')
    try:
        persons = paginator.page(page)
    except PageNotAnInteger:
        persons = paginator.page(1)
    except EmptyPage:
        persons = paginator.page(paginator.num_pages)
    
    context = {
        'persons': persons,
        'search': search,
        'type_filter': person_type,
        'per_page': per_page,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Persons', 'url': None},
        ],
    }
    return render(request, 'forensics/person_list.html', context)


@login_required
def person_create(request):
    """Create a new person"""
    if request.method == 'POST':
        from django.http import JsonResponse
        from django.utils.dateparse import parse_date
        
        # Parse date of birth if provided
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        if date_of_birth:
            try:
                date_of_birth = parse_date(date_of_birth)
            except:
                date_of_birth = None
        else:
            date_of_birth = None
        
        person = Person.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            middle_name=request.POST.get('middle_name', ''),
            date_of_birth=date_of_birth,
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            person_type=request.POST.get('person_type'),
            notes=request.POST.get('notes', ''),
        )
        
        # Check if this is an AJAX request (from modal)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'id': str(person.id),
                'first_name': person.first_name,
                'last_name': person.last_name,
                'person_type': person.get_person_type_display(),
            })
        
        messages.success(request, f'Person {person.first_name} {person.last_name} added successfully!')
        return redirect('person_list')
    
    context = {
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Persons', 'url': '/persons/'},
            {'name': 'New Person', 'url': None},
        ],
    }
    return render(request, 'forensics/person_form.html', context)


@login_required
def person_update(request, pk):
    """Update a person"""
    person = get_object_or_404(Person, pk=pk)
    
    if request.method == 'POST':
        person.first_name = request.POST.get('first_name')
        person.last_name = request.POST.get('last_name')
        person.middle_name = request.POST.get('middle_name', '')
        person.email = request.POST.get('email', '')
        person.phone = request.POST.get('phone', '')
        person.address = request.POST.get('address', '')
        person.person_type = request.POST.get('person_type')
        person.notes = request.POST.get('notes', '')
        person.save()
        
        messages.success(request, 'Person updated successfully!')
        return redirect('person_list')
    
    context = {
        'person': person,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Persons', 'url': '/persons/'},
            {'name': f'{person.first_name} {person.last_name}', 'url': None},
            {'name': 'Edit', 'url': None},
        ],
    }
    return render(request, 'forensics/person_form.html', context)


@login_required
def person_detail(request, pk):
    """View person details with all associated cases and evidence"""
    person = get_object_or_404(Person, pk=pk)
    
    # Get all cases this person is involved in
    case_persons = person.person_cases.select_related('case').all()
    cases = [cp.case for cp in case_persons]
    
    # Get all evidence owned by this person
    owned_evidence = person.owned_evidence.select_related('case').prefetch_related('images').all()
    
    # Get all evidence seized from this person
    seized_evidence = person.seized_evidence.select_related('case').prefetch_related('images').all()
    
    # Get all evidence in custody of this person
    custody_evidence = person.custody_evidence.select_related('case').prefetch_related('images').all()
    
    # Group evidence by case for each category
    owned_by_case = {}
    for evidence in owned_evidence:
        case_key = evidence.case.case_number if evidence.case else 'No Case'
        if case_key not in owned_by_case:
            owned_by_case[case_key] = {'case': evidence.case, 'evidence': []}
        owned_by_case[case_key]['evidence'].append(evidence)
    
    seized_by_case = {}
    for evidence in seized_evidence:
        case_key = evidence.case.case_number if evidence.case else 'No Case'
        if case_key not in seized_by_case:
            seized_by_case[case_key] = {'case': evidence.case, 'evidence': []}
        seized_by_case[case_key]['evidence'].append(evidence)
    
    custody_by_case = {}
    for evidence in custody_evidence:
        case_key = evidence.case.case_number if evidence.case else 'No Case'
        if case_key not in custody_by_case:
            custody_by_case[case_key] = {'case': evidence.case, 'evidence': []}
        custody_by_case[case_key]['evidence'].append(evidence)
    
    # Get all available cases for adding person to case
    available_cases = Case.objects.exclude(id__in=[c.id for c in cases])
    
    context = {
        'person': person,
        'case_persons': case_persons,
        'cases': cases,
        'owned_evidence': owned_evidence,
        'seized_evidence': seized_evidence,
        'custody_evidence': custody_evidence,
        'owned_by_case': owned_by_case,
        'seized_by_case': seized_by_case,
        'custody_by_case': custody_by_case,
        'available_cases': available_cases,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Persons', 'url': '/persons/'},
            {'name': f'{person.first_name} {person.last_name}', 'url': None},
        ],
    }
    return render(request, 'forensics/person_detail.html', context)


@login_required
def person_delete(request, pk):
    """Delete a person"""
    person = get_object_or_404(Person, pk=pk)
    
    if request.method == 'POST':
        name = f"{person.first_name} {person.last_name}"
        person.delete()
        messages.success(request, f'Person {name} deleted successfully!')
        return redirect('person_list')
    
    return render(request, 'forensics/person_confirm_delete.html', {'person': person})


# Evidence Views
@login_required
def evidence_quick_update_department(request, pk):
    """Quick update for evidence department/location via AJAX"""
    if request.method == 'POST':
        import json
        evidence = get_object_or_404(Evidence, pk=pk)
        data = json.loads(request.body)
        
        field = data.get('field')
        value = data.get('value')
        
        if field == 'current_department':
            old_department = evidence.current_department
            evidence.current_department = value
            
            # Log transfer if department changed
            if old_department != value:
                EvidenceTransfer.objects.create(
                    evidence=evidence,
                    from_department=old_department,
                    to_department=value,
                    received_by=evidence.received_by,
                    notes='Quick update from location search'
                )
        elif field == 'received_by':
            evidence.received_by = value
        
        evidence.save()
        
        # Return the display value
        response_data = {'success': True}
        if field == 'current_department' and value:
            response_data['display_value'] = evidence.get_current_department_display()
        else:
            response_data['display_value'] = value or '—'
        
        return JsonResponse(response_data)
    
    return JsonResponse({'success': False}, status=400)


@login_required
def evidence_location_search(request):
    """Quick search for evidence by location/department"""
    evidence_items = Evidence.objects.select_related('case').prefetch_related('images').all()
    
    # Filter by department (current location)
    department = request.GET.get('department')
    if department:
        if department == 'unassigned':
            evidence_items = evidence_items.filter(current_department='')
        else:
            evidence_items = evidence_items.filter(current_department=department)
    
    # Filter by received_by
    received_by = request.GET.get('received_by')
    if received_by:
        evidence_items = evidence_items.filter(received_by__icontains=received_by)
    
    # Search
    search = request.GET.get('search')
    if search:
        evidence_items = evidence_items.filter(
            models.Q(evidence_number__icontains=search) |
            models.Q(ibs_number__icontains=search) |
            models.Q(item_name__icontains=search) |
            models.Q(brand__icontains=search) |
            models.Q(model__icontains=search) |
            models.Q(serial_number__icontains=search) |
            models.Q(imei__icontains=search) |
            models.Q(case__case_number__icontains=search) |
            models.Q(storage_location__icontains=search) |
            models.Q(location_found__icontains=search)
        )
    
    # Get stats by department
    from django.db.models import Count, Sum
    department_stats = Evidence.objects.values('current_department').annotate(
        count=Count('id')
    ).order_by('current_department')
    
    # Calculate total evidence count
    total_evidence = Evidence.objects.count()
    
    # Pagination
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except ValueError:
        per_page = 25
    
    paginator = Paginator(evidence_items, per_page)
    page = request.GET.get('page')
    try:
        evidence_items = paginator.page(page)
    except PageNotAnInteger:
        evidence_items = paginator.page(1)
    except EmptyPage:
        evidence_items = paginator.page(paginator.num_pages)
    
    context = {
        'evidence_items': evidence_items,
        'department_filter': department,
        'received_by_filter': received_by,
        'search': search,
        'department_stats': department_stats,
        'total_evidence': total_evidence,
        'department_choices': Evidence.LOCATION_CHOICES,
        'per_page': per_page,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Evidence Location Search', 'url': None},
        ],
    }
    return render(request, 'forensics/evidence_location_search.html', context)


@login_required
def evidence_list(request):
    """List all evidence"""
    evidence_items = Evidence.objects.select_related('case').prefetch_related('images').all()
    
    # Search
    search = request.GET.get('search')
    if search:
        evidence_items = evidence_items.filter(
            models.Q(evidence_number__icontains=search) |
            models.Q(ibs_number__icontains=search) |
            models.Q(item_name__icontains=search) |
            models.Q(brand__icontains=search) |
            models.Q(model__icontains=search) |
            models.Q(serial_number__icontains=search) |
            models.Q(imei__icontains=search) |
            models.Q(case__case_number__icontains=search)
        )
    
    # Filter by IBS#
    ibs_filter = request.GET.get('ibs')
    if ibs_filter:
        evidence_items = evidence_items.filter(ibs_number=ibs_filter)
    
    # Filter by type
    device_type = request.GET.get('type')
    if device_type:
        evidence_items = evidence_items.filter(device_type=device_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        evidence_items = evidence_items.filter(status=status)
    
    # Filter by department
    department = request.GET.get('department')
    if department:
        evidence_items = evidence_items.filter(current_department=department)
    
    # Filter by state
    state = request.GET.get('state')
    if state:
        evidence_items = evidence_items.filter(state=state)
    
    # Filter by damages
    damages = request.GET.get('damages')
    if damages:
        evidence_items = evidence_items.filter(damages=(damages == 'true'))
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        from django.utils.dateparse import parse_date
        parsed_date = parse_date(date_from)
        if parsed_date:
            evidence_items = evidence_items.filter(collected_date__gte=parsed_date)
    if date_to:
        from django.utils.dateparse import parse_date
        parsed_date = parse_date(date_to)
        if parsed_date:
            from datetime import time
            evidence_items = evidence_items.filter(collected_date__lte=timezone.datetime.combine(parsed_date, time.max))
    
    # Sorting
    sort_by = request.GET.get('sort', '-collected_date')
    allowed_sorts = [
        'evidence_number', '-evidence_number',
        'item_name', '-item_name',
        'device_type', '-device_type',
        'status', '-status',
        'collected_date', '-collected_date',
        'case__case_number', '-case__case_number'
    ]
    if sort_by in allowed_sorts:
        evidence_items = evidence_items.order_by(sort_by)
    else:
        evidence_items = evidence_items.order_by('-collected_date')
    
    # Pagination
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except ValueError:
        per_page = 25
    
    paginator = Paginator(evidence_items, per_page)
    page = request.GET.get('page')
    try:
        evidence_items = paginator.page(page)
    except PageNotAnInteger:
        evidence_items = paginator.page(1)
    except EmptyPage:
        evidence_items = paginator.page(paginator.num_pages)
    
    context = {
        'evidence_items': evidence_items,
        'search': search,
        'ibs_filter': ibs_filter,
        'type_filter': device_type,
        'status_filter': status,
        'department_filter': department,
        'state_filter': state,
        'damages_filter': damages,
        'date_from': date_from,
        'date_to': date_to,
        'department_choices': Evidence.LOCATION_CHOICES,
        'state_choices': Evidence.STATE_CHOICES,
        'per_page': per_page,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Evidence', 'url': None},
        ],
    }
    return render(request, 'forensics/evidence_list.html', context)


@login_required
def evidence_create(request):
    """Create a new evidence item"""
    if request.method == 'POST':
        evidence_number = request.POST.get('evidence_number', '').strip()
        case_id = request.POST.get('case')
        
        # Auto-generate evidence number if not provided
        if not evidence_number:
            if case_id:
                # Get the case to extract case number
                try:
                    case = Case.objects.get(pk=case_id)
                except Case.DoesNotExist:
                    messages.error(request, f'Invalid case selected. Please choose a valid case from the dropdown.')
                    # Redirect back to form
                    cases = Case.objects.all().order_by('-date_opened')
                    persons = Person.objects.all().order_by('last_name', 'first_name')
                    context = {
                        'cases': cases,
                        'persons': persons,
                        'breadcrumbs': [
                            {'name': 'Dashboard', 'url': '/'},
                            {'name': 'Evidence', 'url': '/evidence/'},
                            {'name': 'Add Evidence', 'url': None},
                        ],
                    }
                    return render(request, 'forensics/evidence_form.html', context)
                
                # Get the highest evidence number for this case
                case_evidence = Evidence.objects.filter(
                    case=case,
                    evidence_number__startswith=case.case_number
                ).order_by('-evidence_number').first()
                
                if case_evidence:
                    # Extract the last number from the evidence number (e.g., 001 from 25-0001-001)
                    try:
                        last_num = int(case_evidence.evidence_number.split('-')[-1])
                        next_num = last_num + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1
                
                # Format: CASENUMBER-NNN (e.g., 25-0001-001)
                evidence_number = f"{case.case_number}-{next_num:03d}"
            else:
                # If no case, use generic numbering
                year = timezone.now().strftime('%y')
                unassigned_evidence = Evidence.objects.filter(
                    evidence_number__startswith=f"{year}-UNASSIGNED-"
                ).order_by('-evidence_number').first()
                
                if unassigned_evidence:
                    try:
                        last_num = int(unassigned_evidence.evidence_number.split('-')[-1])
                        next_num = last_num + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1
                    
                evidence_number = f"{year}-UNASSIGNED-{next_num:03d}"
        
        # Collect additional IMEIs
        additional_imeis = request.POST.getlist('additional_imei')
        # Filter out empty strings
        additional_imeis = [imei.strip() for imei in additional_imeis if imei.strip()]
        
        # Extract device-specific fields
        device_specific_data = _extract_device_specific_data(request.POST)
        
        # Auto-generate item_name from device type if not provided
        device_type = request.POST.get('device_type', 'other')
        item_name = request.POST.get('item_name', '').strip()
        if not item_name:
            # Use device type display name as default
            device_type_map = dict(Evidence.DEVICE_TYPE_CHOICES)
            item_name = device_type_map.get(device_type, 'Evidence Item')
        
        # Helper function to parse datetime fields
        from django.utils.dateparse import parse_datetime
        
        def parse_date_field(field_name):
            """Parse datetime field from POST data, return None if empty"""
            value = request.POST.get(field_name, '').strip()
            if value:
                return parse_datetime(value)
            return None
        
        # Parse datetime fields
        received_date = parse_date_field('received_date')
        seizure_date = parse_date_field('seizure_date')
        acquisition_date = parse_date_field('acquisition_date')
        
        # Auto-populate received_date if department assigned but no date
        current_department = request.POST.get('current_department', '')
        if not received_date and current_department:
            received_date = timezone.now()
        
        # Get person IDs
        owner_person_id = request.POST.get('owner_person') or None
        seized_from_person_id = request.POST.get('seized_from_person') or None
        custodian_person_id = request.POST.get('custodian_person') or None
        
        # Validate case_id if provided
        if case_id:
            if not Case.objects.filter(pk=case_id).exists():
                messages.error(request, 'Invalid case selected. Please choose a valid case from the dropdown.')
                cases = Case.objects.all().order_by('-date_opened')
                persons = Person.objects.all().order_by('last_name', 'first_name')
                context = {
                    'cases': cases,
                    'persons': persons,
                    'breadcrumbs': [
                        {'name': 'Dashboard', 'url': '/'},
                        {'name': 'Evidence', 'url': '/evidence/'},
                        {'name': 'Add Evidence', 'url': None},
                    ],
                }
                return render(request, 'forensics/evidence_form.html', context)
        
        try:
            evidence = Evidence.objects.create(
                evidence_number=evidence_number,
                ibs_number=request.POST.get('ibs_number', '').strip(),
                case_id=case_id if case_id else None,
            device_type=device_type,
            item_name=item_name,
            description=request.POST.get('description', ''),
            brand=request.POST.get('brand', ''),
            model=request.POST.get('model', ''),
            serial_number=request.POST.get('serial_number', ''),
            imei=request.POST.get('imei', ''),
            imei_numbers=additional_imeis,
            collected_by=request.POST.get('collected_by', ''),
            location_found=request.POST.get('location_found', ''),
            storage_location=request.POST.get('storage_location', ''),
            status=request.POST.get('status', 'collected'),
            notes=request.POST.get('notes', ''),
            device_specific_data=device_specific_data,
            current_department=request.POST.get('current_department', ''),
            received_by=request.POST.get('received_by', ''),
            received_date=received_date,
            seizure_date=seizure_date,
            acquisition_date=acquisition_date,
                owner_person_id=owner_person_id,
                seized_from_person_id=seized_from_person_id,
                custodian_person_id=custodian_person_id,
            )
        except Exception as e:
            messages.error(request, f'Error creating evidence: {str(e)}')
            cases = Case.objects.all().order_by('-date_opened')
            persons = Person.objects.all().order_by('last_name', 'first_name')
            context = {
                'cases': cases,
                'persons': persons,
                'breadcrumbs': [
                    {'name': 'Dashboard', 'url': '/'},
                    {'name': 'Evidence', 'url': '/evidence/'},
                    {'name': 'Add Evidence', 'url': None},
                ],
            }
            return render(request, 'forensics/evidence_form.html', context)
        
        # Log initial department assignment if set
        if evidence.current_department:
            EvidenceTransfer.objects.create(
                evidence=evidence,
                from_department='',
                to_department=evidence.current_department,
                received_by=evidence.received_by,
                notes='Initial evidence creation'
            )
        
        # Handle image uploads
        uploaded_images = request.FILES.getlist('evidence_images')
        for image_file in uploaded_images:
            EvidenceImage.objects.create(
                evidence=evidence,
                image=image_file,
                uploaded_by=request.POST.get('collected_by', '')
            )
        
        # Handle document uploads
        uploaded_documents = request.FILES.getlist('evidence_documents')
        for doc_file in uploaded_documents:
            Document.objects.create(
                evidence=evidence,
                document_type='other',
                title=doc_file.name,
                file_name=doc_file.name,
                file_path=doc_file,
                file_size=doc_file.size,
                file_type=doc_file.name.split('.')[-1] if '.' in doc_file.name else 'unknown'
            )
        
        messages.success(request, f'Evidence {evidence.evidence_number} added successfully!')
        
        # Redirect to case detail if evidence was added to a case
        if evidence.case:
            return redirect('case_detail', pk=evidence.case.pk)
        return redirect('evidence_list')
    
    # Get all cases for the dropdown
    cases = Case.objects.all().order_by('-date_opened')
    persons = Person.objects.all().order_by('last_name', 'first_name')
    case_id = request.GET.get('case')  # Pre-select case if coming from case detail
    
    breadcrumbs = [
        {'name': 'Dashboard', 'url': '/'},
        {'name': 'Evidence', 'url': '/evidence/'},
        {'name': 'Add Evidence', 'url': None},
    ]
    # If coming from case detail, add case to breadcrumb
    if case_id:
        try:
            case_obj = Case.objects.get(pk=case_id)
            breadcrumbs = [
                {'name': 'Dashboard', 'url': '/'},
                {'name': 'Cases', 'url': '/cases/'},
                {'name': case_obj.case_number, 'url': f'/cases/{case_obj.pk}/'},
                {'name': 'Add Evidence', 'url': None},
            ]
        except Case.DoesNotExist:
            pass
    
    context = {
        'cases': cases,
        'persons': persons,
        'selected_case_id': case_id,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'forensics/evidence_form.html', context)


@login_required
def evidence_update(request, pk):
    """Update an evidence item"""
    evidence = get_object_or_404(Evidence, pk=pk)
    
    if request.method == 'POST':
        # Collect additional IMEIs
        additional_imeis = request.POST.getlist('additional_imei')
        # Filter out empty strings
        additional_imeis = [imei.strip() for imei in additional_imeis if imei.strip()]
        
        # Extract device-specific fields
        device_specific_data = _extract_device_specific_data(request.POST)
        
        case_id = request.POST.get('case')
        # Validate case_id if provided
        if case_id:
            if not Case.objects.filter(pk=case_id).exists():
                messages.error(request, 'Invalid case selected. Please choose a valid case from the dropdown.')
                cases = Case.objects.all().order_by('-date_opened')
                persons = Person.objects.all().order_by('last_name', 'first_name')
                context = {
                    'evidence': evidence,
                    'cases': cases,
                    'persons': persons,
                    'breadcrumbs': [
                        {'name': 'Dashboard', 'url': '/'},
                        {'name': 'Evidence', 'url': '/evidence/'},
                        {'name': evidence.evidence_number, 'url': f'/evidence/{evidence.pk}/'},
                        {'name': 'Edit', 'url': None},
                    ],
                }
                return render(request, 'forensics/evidence_form.html', context)
        
        evidence.case_id = case_id if case_id else None
        evidence.ibs_number = request.POST.get('ibs_number', '').strip()
        evidence.evidence_number = request.POST.get('evidence_number', '').strip() or evidence.evidence_number
        device_type = request.POST.get('device_type')
        evidence.device_type = device_type
        
        # Auto-generate item_name from device type if not provided
        item_name = request.POST.get('item_name', '').strip()
        if not item_name:
            device_type_map = dict(Evidence.DEVICE_TYPE_CHOICES)
            item_name = device_type_map.get(device_type, 'Evidence Item')
        evidence.item_name = item_name
        evidence.description = request.POST.get('description', '')
        evidence.brand = request.POST.get('brand', '')
        evidence.model = request.POST.get('model', '')
        evidence.serial_number = request.POST.get('serial_number', '')
        evidence.imei = request.POST.get('imei', '')
        evidence.imei_numbers = additional_imeis
        evidence.collected_by = request.POST.get('collected_by', '')
        evidence.location_found = request.POST.get('location_found', '')
        evidence.storage_location = request.POST.get('storage_location', '')
        evidence.status = request.POST.get('status')
        evidence.notes = request.POST.get('notes', '')
        evidence.device_specific_data = device_specific_data
        
        # Helper function to parse datetime fields
        from django.utils.dateparse import parse_datetime
        
        def parse_date_field(field_name):
            """Parse datetime field from POST data, return None if empty"""
            value = request.POST.get(field_name, '').strip()
            if value:
                return parse_datetime(value)
            return None
        
        # Update department fields
        old_department = evidence.current_department
        new_department = request.POST.get('current_department', '')
        evidence.current_department = new_department
        evidence.received_by = request.POST.get('received_by', '')
        
        # Parse datetime fields
        received_date = parse_date_field('received_date')
        seizure_date = parse_date_field('seizure_date')
        acquisition_date = parse_date_field('acquisition_date')
        
        if received_date:
            evidence.received_date = received_date
        elif new_department and old_department != new_department:  # Auto-populate on department change
            evidence.received_date = timezone.now()
        elif not new_department:
            evidence.received_date = None
        
        # Update other datetime fields
        evidence.seizure_date = seizure_date
        evidence.acquisition_date = acquisition_date
        
        # Update person relationships
        owner_person_id = request.POST.get('owner_person') or None
        seized_from_person_id = request.POST.get('seized_from_person') or None
        custodian_person_id = request.POST.get('custodian_person') or None
        evidence.owner_person_id = owner_person_id
        evidence.seized_from_person_id = seized_from_person_id
        evidence.custodian_person_id = custodian_person_id
        
        evidence.save()
        
        # Log transfer if department changed
        if old_department != new_department:
            EvidenceTransfer.objects.create(
                evidence=evidence,
                from_department=old_department,
                to_department=new_department,
                received_by=evidence.received_by,
                notes='Evidence update'
            )
        
        # Handle image deletions
        images_to_delete = request.POST.getlist('delete_image')
        if images_to_delete:
            EvidenceImage.objects.filter(id__in=images_to_delete, evidence=evidence).delete()
        
        # Handle document deletions
        documents_to_delete = request.POST.getlist('delete_document')
        if documents_to_delete:
            Document.objects.filter(id__in=documents_to_delete, evidence=evidence).delete()
        
        # Handle new image uploads
        uploaded_images = request.FILES.getlist('evidence_images')
        for image_file in uploaded_images:
            EvidenceImage.objects.create(
                evidence=evidence,
                image=image_file,
                uploaded_by=request.POST.get('collected_by', '')
            )
        
        # Handle new document uploads
        uploaded_documents = request.FILES.getlist('evidence_documents')
        for doc_file in uploaded_documents:
            Document.objects.create(
                evidence=evidence,
                document_type='other',
                title=doc_file.name,
                file_name=doc_file.name,
                file_path=doc_file,
                file_size=doc_file.size,
                file_type=doc_file.name.split('.')[-1] if '.' in doc_file.name else 'unknown'
            )
        
        messages.success(request, 'Evidence updated successfully!')
        if evidence.case:
            return redirect('case_detail', pk=evidence.case.pk)
        return redirect('evidence_list')
    
    cases = Case.objects.all().order_by('-date_opened')
    persons = Person.objects.all().order_by('last_name', 'first_name')
    
    breadcrumbs = [
        {'name': 'Dashboard', 'url': '/'},
        {'name': 'Evidence', 'url': '/evidence/'},
        {'name': evidence.evidence_number, 'url': f'/evidence/{evidence.pk}/'},
        {'name': 'Edit', 'url': None},
    ]
    # If evidence has a case, adjust breadcrumb
    if evidence.case:
        breadcrumbs = [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': '/cases/'},
            {'name': evidence.case.case_number, 'url': f'/cases/{evidence.case.pk}/'},
            {'name': evidence.evidence_number, 'url': f'/evidence/{evidence.pk}/'},
            {'name': 'Edit', 'url': None},
        ]
    
    context = {
        'evidence': evidence,
        'cases': cases,
        'persons': persons,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'forensics/evidence_form.html', context)


@login_required
def evidence_detail(request, pk):
    """View evidence details"""
    evidence = get_object_or_404(Evidence, pk=pk)
    
    breadcrumbs = [
        {'name': 'Dashboard', 'url': '/'},
        {'name': 'Evidence', 'url': '/evidence/'},
        {'name': evidence.evidence_number, 'url': None},
    ]
    # If evidence has a case, adjust breadcrumb
    if evidence.case:
        breadcrumbs = [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': '/cases/'},
            {'name': evidence.case.case_number, 'url': f'/cases/{evidence.case.pk}/'},
            {'name': evidence.evidence_number, 'url': None},
        ]
    
    context = {
        'evidence': evidence,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'forensics/evidence_detail.html', context)


@login_required
def evidence_delete(request, pk):
    """Delete an evidence item"""
    evidence = get_object_or_404(Evidence, pk=pk)
    case = evidence.case
    
    if request.method == 'POST':
        evidence_number = evidence.evidence_number
        evidence.delete()
        messages.success(request, f'Evidence {evidence_number} deleted successfully!')
        
        if case:
            return redirect('case_detail', pk=case.pk)
        return redirect('evidence_list')
    
    context = {'evidence': evidence}
    return render(request, 'forensics/evidence_confirm_delete.html', context)


@login_required
def evidence_detail_export_print(request, pk):
    """Export evidence details to print-friendly HTML page"""
    evidence = get_object_or_404(Evidence, pk=pk)
    images = evidence.images.all()
    documents = evidence.documents.all()
    transfers = evidence.transfers.all().order_by('-transfer_date')
    
    context = {
        'evidence': evidence,
        'images': images,
        'documents': documents,
        'transfers': transfers,
    }
    return render(request, 'forensics/evidence_detail_print.html', context)


@login_required
def evidence_print_label(request, pk):
    """Generate printable label with QR code for evidence"""
    import qrcode
    import io
    import base64
    import json
    from django.contrib.sites.shortcuts import get_current_site
    
    evidence = get_object_or_404(Evidence, pk=pk)
    
    # Generate QR code with URL to evidence detail page
    current_site = get_current_site(request)
    evidence_url = f"http://{current_site.domain}/evidence/{evidence.pk}/"
    
    # Get label type from query parameter (default: 'offline')
    label_type = request.GET.get('type', 'offline')
    
    if label_type == 'offline':
        # Create offline-readable QR code with essential data only
        qr_data = {
            'evidence_number': evidence.evidence_number,
            'ibs_number': evidence.ibs_number or '',
            'item_name': evidence.item_name,
            'device_type': evidence.get_device_type_display(),
            'brand': evidence.brand or '',
            'model': evidence.model or '',
            'serial_number': evidence.serial_number or '',
            'imei': evidence.imei or '',
            'status': evidence.get_status_display(),
            'current_location': evidence.get_current_department_display() if evidence.current_department else '',
            'case_team': evidence.case.get_department_display() if evidence.case and evidence.case.department else '',
            'case_number': evidence.case.case_number if evidence.case else '',
            'case_name': evidence.case.case_name if evidence.case else '',
            'owner': f"{evidence.owner_person.first_name} {evidence.owner_person.last_name}" if evidence.owner_person else '',
            'owner_phone': evidence.owner_person.phone if evidence.owner_person else '',
        }
        qr_content = json.dumps(qr_data, ensure_ascii=False)
        qr_type_label = 'Offline Data'
    else:
        # Create online QR code with URL
        qr_content = evidence_url
        qr_type_label = 'Online Link'
    
    # Create QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    qr_code_data = f"data:image/png;base64,{img_str}"
    
    context = {
        'evidence': evidence,
        'qr_code_data': qr_code_data,
        'evidence_url': evidence_url,
        'label_type': label_type,
        'qr_type_label': qr_type_label,
    }
    return render(request, 'forensics/evidence_label_print.html', context)


@login_required
def evidence_export_csv(request):
    """Export evidence to CSV"""
    # Get filtered queryset
    evidence_items = Evidence.objects.select_related('case').all()
    
    # Apply same filters as list view
    search = request.GET.get('search')
    if search:
        evidence_items = evidence_items.filter(
            models.Q(evidence_number__icontains=search) |
            models.Q(ibs_number__icontains=search) |
            models.Q(item_name__icontains=search) |
            models.Q(brand__icontains=search) |
            models.Q(model__icontains=search)
        )
    
    department = request.GET.get('department')
    if department:
        evidence_items = evidence_items.filter(current_department=department)
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="evidence_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Evidence Number', 'IBS Number', 'Item Name', 'Device Type', 
        'Brand', 'Model', 'Serial Number', 'IMEI',
        'Department', 'Received By', 'Received Date',
        'Status', 'Case Number', 'Collected Date', 'Collected By'
    ])
    
    for item in evidence_items:
        writer.writerow([
            item.evidence_number,
            item.ibs_number,
            item.item_name,
            item.get_device_type_display(),
            item.brand,
            item.model,
            item.serial_number,
            item.imei,
            item.get_current_department_display() if item.current_department else '',
            item.received_by,
            item.received_date.strftime('%Y-%m-%d %H:%M') if item.received_date else '',
            item.get_status_display(),
            item.case.case_number if item.case else '',
            item.collected_date.strftime('%Y-%m-%d %H:%M'),
            item.collected_by,
        ])
    
    return response


@login_required
def case_export_csv(request):
    """Export cases to CSV"""
    cases = Case.objects.all()
    
    # Apply filters
    search = request.GET.get('search')
    if search:
        cases = cases.filter(
            models.Q(case_number__icontains=search) |
            models.Q(case_name__icontains=search) |
            models.Q(prosecutor__icontains=search)
        )
    
    status = request.GET.get('status')
    if status:
        cases = cases.filter(status=status)
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cases_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Case Number', 'Case Name', 'Status', 'Priority', 'Case Type',
        'Prosecutor', 'Date Opened', 'Date Closed', 'Description'
    ])
    
    for case in cases:
        writer.writerow([
            case.case_number,
            case.case_name,
            case.get_status_display(),
            case.get_priority_display(),
            case.get_case_type_display(),
            case.prosecutor,
            case.date_opened.strftime('%Y-%m-%d'),
            case.date_closed.strftime('%Y-%m-%d') if case.date_closed else '',
            case.description,
        ])
    
    return response


@login_required
def evidence_bulk_update(request):
    """Bulk update evidence items"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        evidence_ids = data.get('evidence_ids', [])
        action = data.get('action')
        value = data.get('value')
        
        updated_count = 0
        
        for evidence_id in evidence_ids:
            try:
                evidence = Evidence.objects.get(pk=evidence_id)
                old_department = evidence.current_department
                
                if action == 'department':
                    evidence.current_department = value
                    if not evidence.received_date:
                        evidence.received_date = timezone.now()
                    
                    # Log transfer
                    if old_department != value:
                        EvidenceTransfer.objects.create(
                            evidence=evidence,
                            from_department=old_department,
                            to_department=value,
                            received_by=evidence.received_by,
                            notes='Bulk department assignment'
                        )
                elif action == 'status':
                    evidence.status = value
                
                evidence.save()
                updated_count += 1
            except Evidence.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'updated': updated_count
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def analytics_dashboard(request):
    """Analytics dashboard with time period filtering"""
    import json
    from django.utils.safestring import mark_safe
    from django.utils.dateparse import parse_date
    from datetime import datetime, timedelta
    
    # Get filter parameters
    period = request.GET.get('period', 'all')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    case_status = request.GET.get('case_status', '')
    case_priority = request.GET.get('case_priority', '')
    case_department = request.GET.get('case_department', '')
    evidence_status = request.GET.get('evidence_status', '')
    evidence_device_type = request.GET.get('evidence_device_type', '')
    
    # Handle custom date range
    custom_range = False
    if start_date_str or end_date_str:
        period = 'custom'
        custom_range = True
    
    # Validate period
    valid_periods = ['1m', '3m', '6m', '1y', 'all', 'custom']
    if period not in valid_periods:
        period = 'all'
    
    # Parse custom dates
    parsed_start_date = None
    parsed_end_date = None
    if start_date_str:
        parsed_start_date = parse_date(start_date_str)
        if parsed_start_date:
            parsed_start_date = timezone.make_aware(datetime.combine(parsed_start_date, datetime.min.time()))
    if end_date_str:
        parsed_end_date = parse_date(end_date_str)
        if parsed_end_date:
            parsed_end_date = timezone.make_aware(datetime.combine(parsed_end_date, datetime.max.time()))
    
    # Get analytics data with all filters
    data = analytics.get_combined_analytics(
        period=period,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        case_status=case_status if case_status else None,
        case_priority=case_priority if case_priority else None,
        case_department=case_department if case_department else None,
        evidence_status=evidence_status if evidence_status else None,
        evidence_device_type=evidence_device_type if evidence_device_type else None
    )
    comparison = analytics.get_comparison_analytics()
    
    # Get team statistics
    team_stats = analytics.get_team_statistics(
        period=period,
        start_date=parsed_start_date,
        end_date=parsed_end_date
    )
    
    # Period labels for UI
    period_labels = {
        '1m': 'Last Month',
        '3m': 'Last 3 Months',
        '6m': 'Last 6 Months',
        '1y': 'Last Year',
        'all': 'All Time',
        'custom': 'Custom Range'
    }
    
    # Serialize data for JavaScript charts
    case_status_labels = [item['status'].title() for item in data['case_analytics']['status_distribution']]
    case_status_counts = [item['count'] for item in data['case_analytics']['status_distribution']]
    
    case_priority_labels = [item['priority'].title() for item in data['case_analytics']['priority_distribution']]
    case_priority_counts = [item['count'] for item in data['case_analytics']['priority_distribution']]
    
    # Get filter choices from models
    case_status_choices = Case.STATUS_CHOICES
    case_priority_choices = Case.PRIORITY_CHOICES
    case_department_choices = Case.DEPARTMENT_CHOICES
    evidence_status_choices = Evidence.STATUS_CHOICES
    evidence_device_type_choices = Evidence.DEVICE_TYPE_CHOICES
    
    context = {
        'period': period,
        'period_label': period_labels[period],
        'period_labels': period_labels,
        'analytics': data,
        'comparison': comparison,
        'team_stats': team_stats,
        # Current filters
        'start_date': start_date_str or '',
        'end_date': end_date_str or '',
        'case_status_filter': case_status,
        'case_priority_filter': case_priority,
        'case_department_filter': case_department,
        'evidence_status_filter': evidence_status,
        'evidence_device_type_filter': evidence_device_type,
        # Filter choices
        'case_status_choices': case_status_choices,
        'case_priority_choices': case_priority_choices,
        'case_department_choices': case_department_choices,
        'evidence_status_choices': evidence_status_choices,
        'evidence_device_type_choices': evidence_device_type_choices,
        # JSON serialized data for charts
        'case_status_labels_json': mark_safe(json.dumps(case_status_labels)),
        'case_status_counts_json': mark_safe(json.dumps(case_status_counts)),
        'case_priority_labels_json': mark_safe(json.dumps(case_priority_labels)),
        'case_priority_counts_json': mark_safe(json.dumps(case_priority_counts)),
        'case_type_distribution_json': mark_safe(json.dumps(data['case_analytics']['case_type_distribution'])),
        'case_department_distribution_json': mark_safe(json.dumps(data['case_analytics']['department_distribution'])),
        'evidence_device_distribution_json': mark_safe(json.dumps(data['evidence_analytics']['device_type_distribution'])),
        'evidence_status_distribution_json': mark_safe(json.dumps(data['evidence_analytics']['status_distribution'])),
        'evidence_department_distribution_json': mark_safe(json.dumps(data['evidence_analytics']['department_distribution'])),
        'monthly_trend_json': mark_safe(json.dumps(data['case_analytics']['monthly_trend'], default=str)),
        'team_stats_json': mark_safe(json.dumps(team_stats)),
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Analytics', 'url': None},
        ],
    }
    
    return render(request, 'forensics/analytics.html', context)


@login_required
def check_case_number(request):
    """Check if a case number already exists"""
    case_number = request.GET.get('case_number', '').strip()
    
    if not case_number:
        return JsonResponse({'exists': False})
    
    # Check if case number exists
    exists = Case.objects.filter(case_number=case_number).exists()
    
    return JsonResponse({'exists': exists})


@login_required
def check_case_name(request):
    """Check if a case name already exists and return matching cases"""
    case_name = request.GET.get('case_name', '').strip()
    
    if not case_name:
        return JsonResponse({'exists': False, 'cases': []})
    
    # Find cases with the same name
    matching_cases = Case.objects.filter(case_name__iexact=case_name).values(
        'case_number', 'case_name', 'status'
    )[:5]  # Limit to 5 results
    
    exists = len(matching_cases) > 0
    
    return JsonResponse({
        'exists': exists,
        'cases': list(matching_cases)
    })


# Document Views
@login_required
def document_upload(request, case_pk):
    """Upload a document to a case"""
    from .forms import DocumentForm
    case = get_object_or_404(Case, pk=case_pk)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, case=case)
        if form.is_valid():
            document = form.save(commit=False)
            document.case = case
            
            # Set file metadata
            if document.file_path:
                document.file_name = document.file_path.name
                document.file_size = document.file_path.size
                # Extract file extension (e.g., 'pdf' from 'document.pdf')
                import os
                file_extension = os.path.splitext(document.file_path.name)[1].lstrip('.').lower()
                document.file_type = file_extension if file_extension else 'unknown'
            
            document.save()
            messages.success(request, f'Document "{document.title}" uploaded successfully.')
            return redirect('case_detail', pk=case.pk)
    else:
        form = DocumentForm(case=case)
    
    context = {
        'form': form,
        'case': case,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': '/cases/'},
            {'name': case.case_number, 'url': f'/cases/{case.pk}/'},
            {'name': 'Upload Document', 'url': None},
        ],
    }
    return render(request, 'forensics/document_upload.html', context)


@login_required
def document_delete(request, pk):
    """Delete a document"""
    document = get_object_or_404(Document, pk=pk)
    case = document.case
    
    if request.method == 'POST':
        document_title = document.title
        
        # Delete the file from filesystem
        if document.file_path:
            try:
                document.file_path.delete()
            except Exception as e:
                messages.warning(request, f'Document deleted from database but file could not be removed: {str(e)}')
        
        document.delete()
        messages.success(request, f'Document "{document_title}" deleted successfully.')
        return redirect('case_detail', pk=case.pk)
    
    context = {
        'document': document,
        'case': case,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Cases', 'url': '/cases/'},
            {'name': case.case_number, 'url': f'/cases/{case.pk}/'},
            {'name': 'Delete Document', 'url': None},
        ],
    }
    return render(request, 'forensics/document_confirm_delete.html', context)
