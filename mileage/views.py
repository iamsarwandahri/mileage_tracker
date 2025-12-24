from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from datetime import date

from .forms import MileageForm
from .models import MileageRecord, MileageImage
from accounts.utils import is_trainer
from .utils import is_supervisor

from accounts.utils import is_admin
from accounts.models import TrainerProfile


from django.contrib.auth.models import User
from django import forms
from django.contrib import messages


@login_required
def submit_mileage(request):
    today = date.today()
    
    # Check if there's an existing draft for today
    existing_draft = MileageRecord.objects.filter(
        trainer=request.user,
        date=today,
        submission_status='DRAFT'
    ).first()
    
    # Check if there's already a submitted record for today
    existing_submitted = MileageRecord.objects.filter(
        trainer=request.user,
        date=today,
        submission_status='SUBMITTED'
    ).first()
    
    if existing_submitted:
        return render(request, 'mileage/already_submitted.html', {
            'latest_submission': existing_submitted
        })

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')
        # Don't use instance for POST requests since we handle data manually
        form = MileageForm(request.POST, request.FILES)
        
        if action == 'save':
            # For Save: start_km and start_photo required; optionally save end_km and end_photo if provided
            start_km = request.POST.get('start_km')
            end_km = request.POST.get('end_km')
            start_photo = request.FILES.get('start_photo') if 'start_photo' in request.FILES else (existing_draft.start_photo if existing_draft else None)
            end_photo = request.FILES.get('end_photo') if 'end_photo' in request.FILES else (existing_draft.end_photo if existing_draft else None)
            
            # Validate save requirements
            errors = []
            if not start_km:
                errors.append('Start KM is required.')
            else:
                try:
                    start_km_value = int(float(start_km))
                    if start_km_value < 0:
                        errors.append('Start KM cannot be negative.')
                except ValueError:
                    errors.append('Start KM must be a valid number.')
            
            if not start_photo:
                errors.append('Start Photo is required.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'mileage/submit.html', {'form': form})
            
            # Save as draft (include optional end_km/end_photo if provided)
            if existing_draft:
                # Update existing draft
                existing_draft.start_km = int(float(start_km))
                if end_km:
                    try:
                        existing_draft.end_km = int(float(end_km))
                    except ValueError:
                        pass
                if 'start_photo' in request.FILES:
                    existing_draft.start_photo = start_photo
                if 'end_photo' in request.FILES:
                    existing_draft.end_photo = end_photo
                existing_draft.submission_status = 'DRAFT'
                existing_draft.save()
                record = existing_draft
            else:
                # Create new draft
                kwargs = {
                    'trainer': request.user,
                    'date': today,
                    'start_km': int(float(start_km)),
                    'start_photo': start_photo,
                    'submission_status': 'DRAFT'
                }
                if end_km:
                    try:
                        kwargs['end_km'] = int(float(end_km))
                    except ValueError:
                        pass
                if end_photo:
                    kwargs['end_photo'] = end_photo

                record = MileageRecord.objects.create(**kwargs)

            # Handle additional images (multiple)
            images = request.FILES.getlist('images') if 'images' in request.FILES else []
            for img in images:
                # Basic validation
                if not img.content_type.startswith('image/'):
                    continue
                if img.size > 5 * 1024 * 1024:
                    continue
                MileageImage.objects.create(record=record, image=img)
            
            messages.success(request, 'Mileage saved successfully. You can complete it later.')
            return render(request, 'mileage/save_success.html', {'record': record})
            
        elif action == 'submit':
            # For Submit: all four fields required
            start_km = request.POST.get('start_km')
            end_km = request.POST.get('end_km')
            start_photo = request.FILES.get('start_photo') if 'start_photo' in request.FILES else (existing_draft.start_photo if existing_draft else None)
            end_photo = request.FILES.get('end_photo') if 'end_photo' in request.FILES else (existing_draft.end_photo if existing_draft else None)
            
            # Validate all required fields for submit
            errors = []
            
            if not start_km:
                errors.append('Start KM is required for submission.')
            else:
                try:
                    start_km_value = int(float(start_km))
                    if start_km_value < 0:
                        errors.append('Start KM cannot be negative.')
                except ValueError:
                    errors.append('Start KM must be a valid number.')
            
            if not end_km:
                errors.append('End KM is required for submission.')
            else:
                try:
                    end_km_value = int(float(end_km))
                    if end_km_value < 0:
                        errors.append('End KM cannot be negative.')
                except ValueError:
                    errors.append('End KM must be a valid number.')
            
            if not start_photo:
                errors.append('Start Photo is required for submission.')
            
            if not end_photo:
                errors.append('End Photo is required for submission.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'mileage/submit.html', {'form': form})
            
            # All validations passed, create or update the record
            try:
                start_km_value = int(float(start_km))
                end_km_value = int(float(end_km))
                
                if end_km_value <= start_km_value:
                    messages.error(request, 'End KM must be greater than Start KM.')
                    return render(request, 'mileage/submit.html', {'form': form})
                
                if existing_draft:
                    # Update existing draft to submitted
                    existing_draft.start_km = start_km_value
                    existing_draft.end_km = end_km_value
                    if 'start_photo' in request.FILES:
                        existing_draft.start_photo = start_photo
                    if 'end_photo' in request.FILES:
                        existing_draft.end_photo = end_photo
                    existing_draft.submission_status = 'SUBMITTED'
                    existing_draft.save()
                    record = existing_draft
                else:
                    # Create new submitted record
                    record = MileageRecord.objects.create(
                        trainer=request.user,
                        date=today,
                        start_km=start_km_value,
                        end_km=end_km_value,
                        start_photo=start_photo,
                        end_photo=end_photo,
                        submission_status='SUBMITTED'
                    )
                
                messages.success(request, 'Mileage submitted successfully!')
                # Save any additional images uploaded with submission
                images = request.FILES.getlist('images') if 'images' in request.FILES else []
                for img in images:
                    if not img.content_type.startswith('image/'):
                        continue
                    if img.size > 5 * 1024 * 1024:
                        continue
                    MileageImage.objects.create(record=record, image=img)

                return render(request, 'mileage/success.html', {'record': record})
                
            except Exception as e:
                messages.error(request, f'Error saving record: {str(e)}')
                return render(request, 'mileage/submit.html', {'form': form})
    else:
        if existing_draft:
            form = MileageForm(instance=existing_draft)
        else:
            form = MileageForm()

    return render(request, 'mileage/submit.html', {'form': form})



@login_required
def dashboard(request):
    is_admin_user = is_admin(request.user)
    is_supervisor_user = request.user.groups.filter(name='Supervisor').exists()
    is_staff_user = is_admin_user or is_supervisor_user

    # Filters from GET (only for staff users)
    trainer_id = request.GET.get('trainer') if is_staff_user else None
    date_filter = request.GET.get('date') if is_staff_user else None

    # Base queryset based on user permissions
    if is_staff_user:
        # Staff users see all records (with supervisor restrictions if applicable)
        if is_supervisor_user:
            # Only trainers assigned to this supervisor
            records = MileageRecord.objects.filter(
                trainer__trainerprofile__supervisor=request.user
            ).order_by('-date')
        else:
            records = MileageRecord.objects.all().order_by('-date')

        # Apply filters for staff users
        if trainer_id:
            records = records.filter(trainer__id=trainer_id)
        if date_filter:
            records = records.filter(date=date_filter)

        # Trainers for filter dropdown (only for staff users)
        if is_supervisor_user:
            trainers = TrainerProfile.objects.filter(supervisor=request.user)
        else:
            trainers = TrainerProfile.objects.all()

        context = {
            'records': records,
            'trainers': trainers,
            'is_supervisor': is_supervisor_user,
            'is_staff': True,
            'is_admin': is_admin_user,
        }
    else:
        # Regular users only see their own records
        records = MileageRecord.objects.filter(
            trainer=request.user
        ).order_by('-date')

        context = {
            'records': records,
            'is_staff': False,
            'is_admin': is_admin_user,
        }

    return render(request, 'mileage/dashboard.html', context)


@login_required
def edit_mileage(request, record_id):
    try:
        record = MileageRecord.objects.get(id=record_id)
    except MileageRecord.DoesNotExist:
        messages.error(request, 'Record not found.')
        return redirect('dashboard')

    # Check permissions
    if record.trainer != request.user:
        messages.error(request, 'You can only edit your own records.')
        return redirect('dashboard')

    if record.submission_status != 'SUBMITTED':
        messages.error(request, 'You can only edit submitted records.')
        return redirect('dashboard')

    if record.edit_count >= 2:
        messages.error(request, 'You have reached the maximum edit limit for this record.')
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')

        if action == 'submit':
            # For editing: all four fields required
            start_km = request.POST.get('start_km')
            end_km = request.POST.get('end_km')
            start_photo = request.FILES.get('start_photo') if 'start_photo' in request.FILES else record.start_photo
            end_photo = request.FILES.get('end_photo') if 'end_photo' in request.FILES else record.end_photo

            # Validate all required fields for submit
            errors = []

            if not start_km:
                errors.append('Start KM is required.')
            else:
                try:
                    start_km_value = int(float(start_km))
                    if start_km_value < 0:
                        errors.append('Start KM cannot be negative.')
                except ValueError:
                    errors.append('Start KM must be a valid number.')

            if not end_km:
                errors.append('End KM is required.')
            else:
                try:
                    end_km_value = int(float(end_km))
                    if end_km_value < 0:
                        errors.append('End KM cannot be negative.')
                except ValueError:
                    errors.append('End KM must be a valid number.')

            if not start_photo:
                errors.append('Start Photo is required.')

            if not end_photo:
                errors.append('End Photo is required.')

            if errors:
                for error in errors:
                    messages.error(request, error)
                form = MileageForm(instance=record)
                return render(request, 'mileage/edit.html', {'form': form, 'record': record})

            # All validations passed, update the record
            try:
                start_km_value = int(float(start_km))
                end_km_value = int(float(end_km))

                if end_km_value <= start_km_value:
                    messages.error(request, 'End KM must be greater than Start KM.')
                    form = MileageForm(instance=record)
                    return render(request, 'mileage/edit.html', {'form': form, 'record': record})

                # Update the record
                record.start_km = start_km_value
                record.end_km = end_km_value
                if 'start_photo' in request.FILES:
                    record.start_photo = start_photo
                if 'end_photo' in request.FILES:
                    record.end_photo = end_photo
                record.edit_count += 1
                record.save()

                # Save any additional images added during edit
                images = request.FILES.getlist('images') if 'images' in request.FILES else []
                for img in images:
                    if not img.content_type.startswith('image/'):
                        continue
                    if img.size > 5 * 1024 * 1024:
                        continue
                    MileageImage.objects.create(record=record, image=img)

                messages.success(request, f'Mileage updated successfully! You have {2 - record.edit_count} edit(s) remaining.')
                return redirect('dashboard')

            except Exception as e:
                messages.error(request, f'Error updating record: {str(e)}')
                form = MileageForm(instance=record)
                return render(request, 'mileage/edit.html', {'form': form, 'record': record})
    else:
        form = MileageForm(instance=record)

    return render(request, 'mileage/edit.html', {'form': form, 'record': record})


@login_required
def change_status(request, record_id):
    # Only admins may change the status
    if not is_admin(request.user):
        return HttpResponseForbidden('Not allowed')

    try:
        record = MileageRecord.objects.get(id=record_id)
    except MileageRecord.DoesNotExist:
        messages.error(request, 'Record not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(MileageRecord.STATUS_CHOICES).keys():
            record.status = new_status
            record.save()
            messages.success(request, f'Status updated to {new_status} for record {record.id}.')
        else:
            messages.error(request, 'Invalid status selected.')

    return redirect('dashboard')
