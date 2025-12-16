from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from .access_models import AccessRequest
import secrets
import string


def access_request_create(request):
    """Public view for users to request access"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        badge_number = request.POST.get('badge_number', '').strip()
        department = request.POST.get('department', '').strip()
        phone_extension = request.POST.get('phone_extension', '').strip()
        requested_username = request.POST.get('requested_username', '').strip()
        reason = request.POST.get('reason', '').strip()
        
        # Validation
        if not all([full_name, badge_number, department, requested_username, reason]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'forensics/access_request_form.html')
        
        # Check if username already exists
        if User.objects.filter(username=requested_username).exists():
            messages.error(request, f'Username "{requested_username}" is already taken. Please choose another.')
            return render(request, 'forensics/access_request_form.html')
        
        # Check if there's already a pending request from this person
        existing = AccessRequest.objects.filter(
            badge_number=badge_number,
            status='pending'
        ).first()
        
        if existing:
            messages.warning(request, 'You already have a pending access request. Please wait for admin approval.')
            return redirect('login')
        
        # Create the request
        AccessRequest.objects.create(
            full_name=full_name,
            badge_number=badge_number,
            department=department,
            phone_extension=phone_extension,
            requested_username=requested_username,
            reason=reason
        )
        
        messages.success(request, 'Access request submitted successfully! An administrator will review your request.')
        return redirect('login')
    
    return render(request, 'forensics/access_request_form.html')


@login_required
@user_passes_test(lambda u: u.is_staff)
def access_request_list(request):
    """Admin view to list all access requests"""
    status_filter = request.GET.get('status', 'pending')
    
    requests_qs = AccessRequest.objects.all()
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    
    pending_count = AccessRequest.objects.filter(status='pending').count()
    
    context = {
        'access_requests': requests_qs,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Access Requests', 'url': None},
        ],
    }
    return render(request, 'forensics/access_request_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def access_request_review(request, pk):
    """Admin view to approve or reject an access request"""
    access_request = get_object_or_404(AccessRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '').strip()
        
        if action == 'approve':
            # Generate a temporary password
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            
            # Create the user account
            try:
                user = User.objects.create_user(
                    username=access_request.requested_username,
                    password=temp_password
                )
                user.first_name = access_request.full_name.split()[0] if access_request.full_name else ''
                user.last_name = ' '.join(access_request.full_name.split()[1:]) if len(access_request.full_name.split()) > 1 else ''
                user.is_active = True
                user.save()
                
                # Update the request
                access_request.status = 'approved'
                access_request.reviewed_at = timezone.now()
                access_request.reviewed_by = request.user.username
                access_request.review_notes = review_notes
                access_request.temp_password = temp_password
                access_request.save()
                
                messages.success(request, f'Access approved! Username: {user.username}, Temporary Password: {temp_password}')
                messages.info(request, 'Please write down this password and provide it to the user in person. It will not be shown again.')
                
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
                return redirect('access_request_review', pk=pk)
        
        elif action == 'reject':
            access_request.status = 'rejected'
            access_request.reviewed_at = timezone.now()
            access_request.reviewed_by = request.user.username
            access_request.review_notes = review_notes
            access_request.save()
            
            messages.success(request, 'Access request rejected.')
        
        return redirect('access_request_list')
    
    context = {
        'access_request': access_request,
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/'},
            {'name': 'Access Requests', 'url': '/access-requests/'},
            {'name': 'Review Request', 'url': None},
        ],
    }
    return render(request, 'forensics/access_request_review.html', context)
