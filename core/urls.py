from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # User Profile
    path('profile/', views.user_profile, name='user_profile'),
    
    # Donor Routes
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('add-medicine/', views.add_medicine, name='add_medicine'),
    path('medicine/<int:med_id>/edit/', views.edit_medicine, name='edit_medicine'),
    path('medicine/<int:med_id>/delete/', views.delete_medicine, name='delete_medicine'),
    
    # Medicine Routes
    path('medicine/<int:med_id>/', views.medicine_detail, name='medicine_detail'),
    path('medicine/<int:med_id>/rate/', views.rate_medicine, name='rate_medicine'),
    path('search/', views.search_medicines, name='search_medicines'),
    path('medicines-map/', views.medicines_map, name='medicines_map'),
    
    # NGO Routes
    path('ngo/dashboard/', views.ngo_dashboard, name='ngo_dashboard'),
    path('medicine/<int:med_id>/request/', views.request_medicine, name='request_medicine'),
    
    # Donation Request Routes
    path('request/<int:req_id>/', views.donation_request_detail, name='donation_request_detail'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Admin Routes
    # NOTE: Do not place custom views under the `admin/` prefix because it is
    # handled by Django admin (see `medshare/urls.py`).
    path('reports/', views.admin_reports, name='admin_reports'),
]
