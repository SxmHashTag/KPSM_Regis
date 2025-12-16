from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import datetime, timedelta
from .journal_models import DailyJournal, JournalComment
from django.contrib.auth.models import User


@login_required
def journal_list(request):
    """View all journal entries with filtering"""
    # Get filter parameters
    user_filter = request.GET.get('user')
    date_filter = request.GET.get('date')
    search_query = request.GET.get('search')
    tag_filter = request.GET.get('tag')
    
    # Base queryset
    journals = DailyJournal.objects.select_related('user').prefetch_related('comments')
    
    # Apply filters
    if user_filter:
        journals = journals.filter(user_id=user_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            journals = journals.filter(date=filter_date)
        except ValueError:
            pass
    
    if search_query:
        journals = journals.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    if tag_filter:
        journals = journals.filter(tags__contains=[tag_filter])
    
    # Get all users for filter dropdown
    users = User.objects.filter(journal_entries__isnull=False).distinct()
    
    # Get all unique tags
    all_journals = DailyJournal.objects.all()
    all_tags = set()
    for journal in all_journals:
        if journal.tags:
            all_tags.update(journal.tags)
    all_tags = sorted(list(all_tags))
    
    context = {
        'journals': journals,
        'users': users,
        'all_tags': all_tags,
        'selected_user': user_filter,
        'selected_date': date_filter,
        'search_query': search_query,
        'selected_tag': tag_filter,
    }
    
    return render(request, 'forensics/journal_list.html', context)


@login_required
def journal_detail(request, pk):
    """View a specific journal entry"""
    journal = get_object_or_404(DailyJournal.objects.prefetch_related('comments__user'), pk=pk)
    
    # Handle comment submission
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            JournalComment.objects.create(
                journal=journal,
                user=request.user,
                comment=comment_text
            )
            messages.success(request, 'Comment added successfully.')
            return redirect('journal_detail', pk=pk)
    
    context = {
        'journal': journal,
        'is_owner': journal.user == request.user,
    }
    
    return render(request, 'forensics/journal_detail.html', context)


@login_required
def journal_create(request):
    """Create a new journal entry"""
    # Check if user already has an entry for today
    today = timezone.now().date()
    existing_entry = DailyJournal.objects.filter(user=request.user, date=today).first()
    
    if existing_entry:
        messages.warning(request, 'You already have a journal entry for today. Editing instead.')
        return redirect('journal_edit', pk=existing_entry.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        date_str = request.POST.get('date')
        tags_str = request.POST.get('tags', '').strip()
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Parse date
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
        except ValueError:
            entry_date = today
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            # Check for existing entry on the selected date
            existing = DailyJournal.objects.filter(user=request.user, date=entry_date).first()
            if existing:
                messages.error(request, f'You already have a journal entry for {entry_date}.')
            else:
                journal = DailyJournal.objects.create(
                    user=request.user,
                    date=entry_date,
                    title=title,
                    content=content,
                    tags=tags,
                    is_pinned=is_pinned
                )
                messages.success(request, 'Journal entry created successfully.')
                return redirect('journal_detail', pk=journal.pk)
    
    context = {
        'today': today.isoformat(),
    }
    
    return render(request, 'forensics/journal_form.html', context)


@login_required
def journal_edit(request, pk):
    """Edit an existing journal entry"""
    journal = get_object_or_404(DailyJournal, pk=pk)
    
    # Only the owner can edit
    if journal.user != request.user:
        messages.error(request, 'You can only edit your own journal entries.')
        return redirect('journal_detail', pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        date_str = request.POST.get('date')
        tags_str = request.POST.get('tags', '').strip()
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Parse date
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else journal.date
        except ValueError:
            entry_date = journal.date
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            # Check for conflicts with other entries
            if entry_date != journal.date:
                existing = DailyJournal.objects.filter(
                    user=request.user, 
                    date=entry_date
                ).exclude(pk=journal.pk).first()
                if existing:
                    messages.error(request, f'You already have a journal entry for {entry_date}.')
                    return render(request, 'forensics/journal_form.html', {
                        'journal': journal,
                        'is_edit': True,
                    })
            
            journal.title = title
            journal.content = content
            journal.date = entry_date
            journal.tags = tags
            journal.is_pinned = is_pinned
            journal.save()
            
            messages.success(request, 'Journal entry updated successfully.')
            return redirect('journal_detail', pk=journal.pk)
    
    context = {
        'journal': journal,
        'is_edit': True,
        'tags_string': ', '.join(journal.tags) if journal.tags else '',
    }
    
    return render(request, 'forensics/journal_form.html', context)


@login_required
def journal_delete(request, pk):
    """Delete a journal entry"""
    journal = get_object_or_404(DailyJournal, pk=pk)
    
    # Only the owner can delete
    if journal.user != request.user:
        return HttpResponseForbidden('You can only delete your own journal entries.')
    
    if request.method == 'POST':
        journal.delete()
        messages.success(request, 'Journal entry deleted successfully.')
        return redirect('journal_list')
    
    return render(request, 'forensics/journal_confirm_delete.html', {'journal': journal})


@login_required
def comment_delete(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(JournalComment, pk=pk)
    journal_pk = comment.journal.pk
    
    # Only the comment owner can delete
    if comment.user != request.user:
        return HttpResponseForbidden('You can only delete your own comments.')
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
    
    return redirect('journal_detail', pk=journal_pk)


@login_required
def my_journals(request):
    """View current user's journal entries"""
    journals = DailyJournal.objects.filter(user=request.user).prefetch_related('comments')
    
    context = {
        'journals': journals,
        'is_my_journals': True,
    }
    
    return render(request, 'forensics/journal_list.html', context)
