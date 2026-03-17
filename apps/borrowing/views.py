"""Views for the borrowing app."""

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.utils import log_activity
from apps.borrowing.forms import BorrowRequestForm, ReturnForm
from apps.borrowing.models import BorrowRequest
from apps.notifications.utils import notify
from apps.reservations.models import WaitlistEntry


def _is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'


@login_required
def borrow_list_view(request):
    """Paginated list of borrow requests.

    Members see only their own requests; admins see all.
    Supports optional ?status= filter.
    """
    status_filter = request.GET.get('status', '')

    if _is_admin(request.user):
        qs = BorrowRequest.objects.select_related(
            'borrower', 'equipment', 'kit', 'project', 'approved_by'
        )
    else:
        qs = BorrowRequest.objects.filter(borrower=request.user).select_related(
            'equipment', 'kit', 'project', 'approved_by'
        )

    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'borrowing/borrow_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': BorrowRequest.STATUS_CHOICES,
    })


@login_required
def borrow_request_create_view(request):
    """Create a new borrow request.

    If ?equipment_id= is supplied in the GET params the form is pre-populated.
    """
    initial = {}
    equipment_id = request.GET.get('equipment_id')
    if equipment_id:
        from apps.equipment.models import Equipment
        try:
            initial['equipment'] = Equipment.objects.get(pk=equipment_id)
        except Equipment.DoesNotExist:
            pass

    if request.method == 'POST':
        form = BorrowRequestForm(request.POST)
        if form.is_valid():
            borrow = form.save(commit=False)
            borrow.borrower = request.user
            borrow.status = 'PENDING'
            borrow.save()

            log_activity(
                actor=request.user,
                action='BORROW_REQUESTED',
                description=(
                    f'{request.user.username} requested to borrow '
                    f'{borrow.item} (due {borrow.due_date})'
                ),
                content_type_label='borrowrequest',
                object_id=borrow.pk,
                object_repr=str(borrow),
                request=request,
            )

            messages.success(request, 'Borrow request submitted successfully.')
            return redirect('borrowing:detail', pk=borrow.pk)
    else:
        form = BorrowRequestForm(initial=initial)

    return render(request, 'borrowing/borrow_request_form.html', {'form': form})


@login_required
def borrow_detail_view(request, pk):
    """Show full details of a single borrow request."""
    borrow = get_object_or_404(
        BorrowRequest.objects.select_related(
            'borrower', 'equipment', 'kit', 'project', 'approved_by'
        ),
        pk=pk,
    )

    # Members can only see their own requests.
    if not _is_admin(request.user) and borrow.borrower != request.user:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('borrowing:list')

    return render(request, 'borrowing/borrow_detail.html', {'borrow': borrow})


@login_required
def borrow_approve_view(request, pk):
    """Admin only: approve a PENDING borrow request."""
    if not _is_admin(request.user):
        messages.error(request, 'Only admins can approve borrow requests.')
        return redirect('borrowing:list')

    borrow = get_object_or_404(BorrowRequest, pk=pk, status='PENDING')

    if request.method == 'POST':
        borrow.status = 'APPROVED'
        borrow.approved_by = request.user
        borrow.approved_date = timezone.now()

        # Mark equipment as BORROWED.
        if borrow.equipment:
            borrow.equipment.status = 'BORROWED'
            borrow.equipment.save(update_fields=['status'])

        # Mark all kit equipment as BORROWED.
        if borrow.kit:
            for item in borrow.kit.items.select_related('equipment'):
                item.equipment.status = 'BORROWED'
                item.equipment.save(update_fields=['status'])

        borrow.save()

        notify(
            recipient=borrow.borrower,
            title='Borrow Request Approved',
            message=(
                f'Your request to borrow {borrow.item} has been approved. '
                f'Please pick it up before {borrow.due_date}.'
            ),
            level='success',
        )

        log_activity(
            actor=request.user,
            action='BORROW_APPROVED',
            description=f'{request.user.username} approved borrow request #{borrow.pk}',
            content_type_label='borrowrequest',
            object_id=borrow.pk,
            object_repr=str(borrow),
            request=request,
        )

        messages.success(request, 'Borrow request approved.')
        return redirect('borrowing:detail', pk=borrow.pk)

    return render(request, 'borrowing/borrow_confirm_approve.html', {'borrow': borrow})


@login_required
def borrow_reject_view(request, pk):
    """Admin only: reject a PENDING borrow request."""
    if not _is_admin(request.user):
        messages.error(request, 'Only admins can reject borrow requests.')
        return redirect('borrowing:list')

    borrow = get_object_or_404(BorrowRequest, pk=pk, status='PENDING')

    if request.method == 'POST':
        borrow.status = 'REJECTED'
        borrow.save()

        notify(
            recipient=borrow.borrower,
            title='Borrow Request Rejected',
            message=f'Your request to borrow {borrow.item} has been rejected.',
            level='warning',
        )

        log_activity(
            actor=request.user,
            action='BORROW_REJECTED',
            description=f'{request.user.username} rejected borrow request #{borrow.pk}',
            content_type_label='borrowrequest',
            object_id=borrow.pk,
            object_repr=str(borrow),
            request=request,
        )

        messages.success(request, 'Borrow request rejected.')
        return redirect('borrowing:detail', pk=borrow.pk)

    return render(request, 'borrowing/borrow_confirm_reject.html', {'borrow': borrow})


@login_required
def borrow_return_view(request, pk):
    """Record the return of a borrowed item.

    Accessible by the original borrower or an admin.
    After processing the return, checks the waitlist and notifies the next person.
    """
    borrow = get_object_or_404(
        BorrowRequest.objects.select_related('borrower', 'equipment', 'kit'),
        pk=pk,
    )

    # Permission check.
    if not _is_admin(request.user) and borrow.borrower != request.user:
        messages.error(request, 'You do not have permission to return this item.')
        return redirect('borrowing:list')

    # Only APPROVED or ACTIVE borrows can be returned.
    if borrow.status not in ('APPROVED', 'ACTIVE'):
        messages.error(request, 'This borrow request cannot be returned in its current state.')
        return redirect('borrowing:detail', pk=borrow.pk)

    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            borrow.status = 'RETURNED'
            borrow.returned_date = timezone.now()
            borrow.return_condition = form.cleaned_data['return_condition']
            borrow.notes = form.cleaned_data.get('notes', '')
            borrow.save()

            # Mark equipment as AVAILABLE again.
            if borrow.equipment:
                borrow.equipment.status = 'AVAILABLE'
                borrow.equipment.save(update_fields=['status'])

            if borrow.kit:
                for item in borrow.kit.items.select_related('equipment'):
                    item.equipment.status = 'AVAILABLE'
                    item.equipment.save(update_fields=['status'])

            notify(
                recipient=borrow.borrower,
                title='Item Returned Successfully',
                message=f'Your return of {borrow.item} has been recorded. Thank you!',
                level='info',
            )

            log_activity(
                actor=request.user,
                action='BORROW_RETURNED',
                description=(
                    f'{request.user.username} returned {borrow.item} '
                    f'(condition: {borrow.return_condition})'
                ),
                content_type_label='borrowrequest',
                object_id=borrow.pk,
                object_repr=str(borrow),
                request=request,
            )

            # Notify next person on the waitlist (if any).
            waitlist_qs = None
            if borrow.equipment:
                waitlist_qs = WaitlistEntry.objects.filter(
                    equipment=borrow.equipment, notified=False
                ).order_by('position', 'created_at')
            elif borrow.kit:
                waitlist_qs = WaitlistEntry.objects.filter(
                    kit=borrow.kit, notified=False
                ).order_by('position', 'created_at')

            if waitlist_qs is not None:
                next_entry = waitlist_qs.first()
                if next_entry:
                    notify(
                        recipient=next_entry.user,
                        title='Item Now Available',
                        message=(
                            f'{borrow.item} is now available. '
                            'You are next on the waitlist — act quickly!'
                        ),
                        level='success',
                    )
                    next_entry.notified = True
                    next_entry.save(update_fields=['notified'])

            messages.success(request, 'Return recorded successfully.')
            return redirect('borrowing:detail', pk=borrow.pk)
    else:
        form = ReturnForm()

    return render(request, 'borrowing/borrow_return_form.html', {
        'form': form,
        'borrow': borrow,
    })


@login_required
def overdue_list_view(request):
    """Admin only: list borrow requests that are overdue."""
    if not _is_admin(request.user):
        messages.error(request, 'Only admins can view the overdue list.')
        return redirect('borrowing:list')

    overdue_borrows = BorrowRequest.objects.filter(
        due_date__lt=date.today(),
        status__in=['APPROVED', 'ACTIVE'],
    ).select_related('borrower', 'equipment', 'kit', 'project')

    return render(request, 'borrowing/overdue_list.html', {
        'overdue_borrows': overdue_borrows,
    })


@login_required
def approval_queue_view(request):
    """Admin only: list all PENDING borrow requests awaiting approval."""
    if not _is_admin(request.user):
        messages.error(request, 'Only admins can view the approval queue.')
        return redirect('borrowing:list')

    pending_borrows = BorrowRequest.objects.filter(status='PENDING').select_related(
        'borrower', 'equipment', 'kit', 'project'
    )

    return render(request, 'borrowing/approval_queue.html', {
        'pending_borrows': pending_borrows,
    })
