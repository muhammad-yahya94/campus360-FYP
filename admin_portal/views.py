from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from users.models import CustomUser, Role
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import logout
from django.db.models import Q


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

# ------------------- Admin Login -------------------
def admin_login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)
        print(f'this is user--- {user}')
        if user is not None:
            if user.is_superuser:
                print(f'inside the superuer block')
                login(request, user)
                print('after applying login function.....')
                return redirect('staff')
            else:
                return render(request, 'admin_login.html', {'error': 'Access denied. Only superusers allowed.'})
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid credentials'})

    return render(request, 'admin_login.html')


# # ------------------- Dashboard -------------------
# def dashboard(request):
#     if not request.user.is_superuser:
#         return redirect('admin-login')
#     return render(request, "admin_dashboard.html", {'page_title': 'Dashboard'})


# # ------------------- Staff Management -------------------
# def admin_staff(request):
#     if not request.user.is_superuser:
#         return redirect('admin-login')
#     if request.method == 'POST':
#         first_name = request.POST.get('firstName')
#         last_name = request.POST.get('lastName')
#         email = request.POST.get('email')
#         phone = request.POST.get('phone')
#         role = request.POST.get('role')
#         print(f'this is role ....  {role}')
#         description = request.POST.get('description')
#         photo = request.FILES.get('photo')

#         if CustomUser.objects.filter(email=email).exists():
#             messages.error(request, "A user with this email already exists.")
#             return redirect('admin-staff')

#         user = CustomUser.objects.create(
#             email=email,
#             first_name=first_name,
#             last_name=last_name,
#             phone=phone,
#             profile_picture=photo,
#             info=description,
#             is_active=False,
#             is_staff=True
#         )
#         user.set_unusable_password()
#         user.save()
        
#         # Assign role
#         Role.objects.create(
#             user=user,
#             admin_role_choices=role,
#             desc=description
#         )

#         # Send verification email
#         token = default_token_generator.make_token(user)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         verification_link = request.build_absolute_uri(
#             reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
#         )

#         if role == 'HOD':
#             send_mail(
#                 subject="Verify your staff account",
#                 message=(
#                     f"Hello {user.first_name},\n\n"
#                     f"Click the link below to verify your account and set your password:\n{verification_link}"
#                 ),
#                 from_email="admin@gmail.com",
#                 recipient_list=[user.email],
#             )

#             messages.success(request, f"Staff member added and verification email sent to {user.email}.")
#             return redirect('admin-staff')
        
#     staff_members = CustomUser.objects.filter(is_staff=True).select_related('role')   #.order_by('-created_at')
#     admin_assign_role = Role.ROLE_CHOICES_Admin
    
#     # --- Filters & Sorting ---
#     search_query = request.GET.get('search', '')
#     role_filter = request.GET.get('role', '')
#     sort_by_date = request.GET.get('sort', '')

#     # staff_members = CustomUser.objects.filter(is_staff=True).select_related('role')

#     # Search logic
#     if search_query:
#         staff_members = staff_members.filter(
#             Q(first_name__icontains=search_query) |
#             Q(last_name__icontains=search_query) |
#             Q(email__icontains=search_query) |
#             Q(phone__icontains=search_query)
#         )

#     # Filter by Role
#     if role_filter and role_filter != 'All':
#         staff_members = staff_members.filter(role__admin_role_choices=role_filter)

#     # Sort by role's created_at
#     if sort_by_date == 'newest':
#         staff_members = staff_members.order_by('-role__created_at')
#     elif sort_by_date == 'oldest':
#         staff_members = staff_members.order_by('role__created_at')

#     # Pagination
#     current_page = request.GET.get('page', 1)
#     paginator = Paginator(staff_members, 2)
#     try:
#         paginated_queries = paginator.page(current_page)
#     except PageNotAnInteger:
#         paginated_queries = paginator.page(1)
#     except EmptyPage:
#         paginated_queries = paginator.page(paginator.num_pages)

#     context = {
#          'page_title': 'Staff Management',
#         "staff_members": paginated_queries,
#         "search_query": search_query,
#         "role_filter": role_filter,
#         "sort_by_date": sort_by_date,
#         "admin_assign_role": admin_assign_role,  
#     }

#     return render(request, "admin_staff.html", context)



# '''update data'''

#   # Adjust if your model is named differently

# 
# def update_staff(request, id):
#     user = get_object_or_404(CustomUser, id=id)

#     if request.method == 'POST':
#         first_name = request.POST.get('firstName')
#         last_name = request.POST.get('lastName')
#         desc = request.POST.get('Description')
#         profile_photo = request.FILES.get('profilePhoto')

  
#         user.first_name = first_name
#         user.last_name = last_name
#         if profile_photo:
#             user.profile_picture = profile_photo
#         user.save()

  
#         if hasattr(user, 'role'):
#             user.role.desc = desc
#             user.role.save()
#         else:
#             messages.error(request, 'No role associated with this user.')

#         messages.success(request, 'Profile updated successfully!')
#         return redirect('admin-staff')

#     return render(request, 'admin_staff_update.html', {'user': user})


# ''' delete '''

# 
# def delete_staff(request, id):
#     user = get_object_or_404(CustomUser, id=id)
  
#     print(f'this is user and request user --- {request.user} -- {user}')
 
#     if request.user == user:
#         messages.error(request, "You can't delete your own account.")
#         return redirect('admin-staff')

#     if request.method == 'POST':
#         user.delete()  
#         messages.success(request, "Staff member deleted successfully.")
#         return redirect('admin-staff')


#     return redirect('admin-staff')



# # ------------------- Email Verification -------------------
# def verify_email(request, uidb64, token):
#     try:
#         uid = urlsafe_base64_decode(uidb64).decode()
#         user = CustomUser.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
#         user = None

#     if user and default_token_generator.check_token(user, token):
#         user.is_active = True
#         user.save()
#         login(request, user)
#         return redirect('set_password')
#     else:
#         return render(request, 'invalid_link.html')














from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def dashboard(request):
    return render(request, 'dashboard.html', {'page_title':'Dashboard'})


def departments(request):
    return render(request, 'department.html', {'page_title':'Departments'})


def events(request):
    return render(request, 'events.html', {'page_title':'Events'})


def faculties(request):
    return render(request, 'faculty.html', {'page_title':'Faculties'})


def news(request):
    return render(request, 'news.html', {'page_title':'News'})


def roles(request):
    return render(request, 'roles.html', {'page_title':'Roles'})



def slider(request):
    return render(request, 'slider.html', {'page_title':'Slider'})

# 
def staff(request):
    return render(request, 'staff.html', {'page_title':'Staff Management'})



def invalid_link(request):
    return render(request, 'invalid_link.html', {'page_title':'Change Password'})


def update_profile(request):
    return render(request, 'updateprofile.html', {'page_title':'Update Profile'})


def change_password(request):
    return render(request, 'changepassword.html' , {'page_title':'Change Password'})



from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('core:login')