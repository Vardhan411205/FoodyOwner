from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import FoodItem
from django.contrib.auth.hashers import check_password
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.db import connections
import json

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')  # Form field is named username but contains email
        password = request.POST.get('password')
        
        try:
            # Get the user by email
            user = User.objects.get(email=email)
            # Try to authenticate with username (which we set to email during registration)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'login.html')

@login_required
def index(request):
    return render(request, 'index.html')

@login_required
def quick_bite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')

        if action == 'add':
            try:
                food_item = FoodItem.objects.create(
                    name=data.get('name'),
                    price=data.get('price'),
                    category=data.get('category'),
                    image_url=data.get('image_url'),
                    rating=data.get('rating', 0.0),
                    description=data.get('description', '')
                )
                return JsonResponse({'status': 'success', 'message': 'Food item added successfully'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif action == 'edit':
            try:
                food_item = FoodItem.objects.get(id=data.get('item_id'))
                food_item.name = data.get('name')
                food_item.price = data.get('price')
                food_item.category = data.get('category')
                food_item.image_url = data.get('image')
                food_item.description = data.get('description', food_item.description)
                food_item.save()
                return JsonResponse({'status': 'success', 'message': 'Food item updated successfully'})
            except FoodItem.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Food item not found'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        elif action == 'delete':
            try:
                food_item = FoodItem.objects.get(id=data.get('item_id'))
                food_item.delete()
                return JsonResponse({'status': 'success', 'message': 'Food item deleted successfully'})
            except FoodItem.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Food item not found'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

    food_items = FoodItem.objects.all().values(
        'id', 'name', 'category', 'price', 'rating', 'image_url'
    )
    context = {
        'food_items': list(food_items),
        'food_item': FoodItem  # For accessing CATEGORY_CHOICES in template
    }
    return render(request, 'quick_bite.html', context)

def get_all_tables(database):
    with connections[database].cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        return [row[0] for row in cursor.fetchall()]

def get_table_data(database, table_name):
    with connections[database].cursor() as cursor:
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s
        """, [table_name])
        columns = [row[0] for row in cursor.fetchall()]
        
        # Get table data
        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = cursor.fetchall()
        
        return {
            'columns': columns,
            'rows': rows
        }

@login_required
def all_tables(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        db = data.get('db')
        table = data.get('table')
        
        try:
            with connections[db].cursor() as cursor:
                if action == 'delete_record':
                    # Delete a single record
                    record_id = data.get('record_id')
                    cursor.execute(f'DELETE FROM "{table}" WHERE id = %s', [record_id])
                    return JsonResponse({'status': 'success', 'message': f'Record deleted successfully from {table}'})
                
                elif action == 'delete_all':
                    # Delete all records from a table
                    cursor.execute(f'DELETE FROM "{table}"')
                    return JsonResponse({'status': 'success', 'message': f'All records deleted from {table}'})
                
                elif action == 'update':
                    # Update a record
                    record_id = data.get('record_id')
                    updates = data.get('updates', {})
                    if not updates:
                        return JsonResponse({'status': 'error', 'message': 'No updates provided'})
                    
                    set_clause = ', '.join([f'"{key}" = %s' for key in updates.keys()])
                    values = list(updates.values())
                    values.append(record_id)
                    
                    cursor.execute(f'UPDATE "{table}" SET {set_clause} WHERE id = %s', values)
                    return JsonResponse({'status': 'success', 'message': f'Record updated successfully in {table}'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Get all tables and their data
    databases = ['default', 'partner', 'user']
    all_data = {}
    
    for db in databases:
        tables = get_all_tables(db)
        db_data = {}
        for table in tables:
            table_data = get_table_data(db, table)
            db_data[table] = table_data
        all_data[db] = db_data

    context = {
        'databases': all_data
    }
    return render(request, 'all_tables.html', context)

@login_required
def edit_profile(request):
    # Get all users if superuser, otherwise just the current user
    users = User.objects.all() if request.user.is_superuser else User.objects.filter(id=request.user.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Only superusers can edit other users, regular users can only edit themselves
            if not request.user.is_superuser and target_user.id != request.user.id:
                messages.error(request, 'Permission denied.')
                return redirect('edit_profile')
            
            if action == 'update_profile':
                # Basic info update
                email = request.POST.get('email')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                
                if email and email != target_user.email:
                    if not User.objects.filter(email=email).exclude(id=target_user.id).exists():
                        target_user.email = email
                        target_user.username = email
                    else:
                        messages.error(request, 'Email already exists.')
                        return redirect('edit_profile')
                
                target_user.first_name = first_name
                target_user.last_name = last_name
                
                # Superuser specific updates
                if request.user.is_superuser:
                    is_active = request.POST.get('is_active') == 'on'
                    is_staff = request.POST.get('is_staff') == 'on'
                    is_superuser = request.POST.get('is_superuser') == 'on'
                    
                    target_user.is_active = is_active
                    target_user.is_staff = is_staff
                    target_user.is_superuser = is_superuser
                
                target_user.save()
                messages.success(request, 'Profile updated successfully.')
            
            elif action == 'change_password':
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # If superuser, don't require current password
                if request.user.is_superuser and request.user.id != target_user.id:
                    if new_password and new_password == confirm_password:
                        target_user.set_password(new_password)
                        target_user.save()
                        messages.success(request, f'Password updated for {target_user.email}')
                    else:
                        messages.error(request, 'New passwords do not match.')
                else:
                    # Regular password change flow
                    if check_password(current_password, target_user.password):
                        if new_password == confirm_password:
                            target_user.set_password(new_password)
                            target_user.save()
                            if target_user.id == request.user.id:
                                update_session_auth_hash(request, target_user)
                            messages.success(request, 'Password updated successfully.')
                        else:
                            messages.error(request, 'New passwords do not match.')
                    else:
                        messages.error(request, 'Current password is incorrect.')
            
            elif action == 'delete_user' and request.user.is_superuser:
                if target_user.id != request.user.id:
                    target_user.delete()
                    messages.success(request, f'User {target_user.email} deleted successfully.')
                else:
                    messages.error(request, 'Cannot delete your own account.')
        
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        
        return redirect('edit_profile')
    
    context = {
        'users': users,
        'session_data': dict(request.session.items())
    }
    return render(request, 'edit_profile.html', context)
