from django.urls import path
from . import views
from . import chatbot_views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
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
    path('expiry-tracker/', views.expiry_tracker, name='expiry_tracker'),
    
    # Medicine Categories
    path('categories/', views.medicine_categories, name='medicine_categories'),
    path('category/<int:category_id>/', views.category_medicines, name='category_medicines'),
    
    # NGO Routes
    path('ngo/dashboard/', views.ngo_dashboard, name='ngo_dashboard'),
    path('medicine/<int:med_id>/request/', views.request_medicine, name='request_medicine'),
    
    # Emergency Alerts
    path('emergency-alerts/', views.emergency_alerts, name='emergency_alerts'),
    path('create-emergency-alert/', views.create_emergency_alert, name='create_emergency_alert'),
    path('emergency-alert/<int:alert_id>/resolve/', views.resolve_emergency_alert, name='resolve_emergency_alert'),
    path('emergency-alert/<int:alert_id>/respond/', views.respond_emergency_alert, name='respond_emergency_alert'),
    path('emergency-response/<int:response_id>/accept/', views.accept_emergency_response, name='accept_emergency_response'),
    
    # Bulk Donation Requests
    path('bulk-requests/', views.bulk_requests, name='bulk_requests'),
    path('create-bulk-request/', views.create_bulk_request, name='create_bulk_request'),
    path('bulk-request/<int:request_id>/edit/', views.edit_bulk_request, name='edit_bulk_request'),
    path('bulk-request/<int:request_id>/matches/', views.bulk_request_matches, name='bulk_request_matches'),
    
    # NGO Inventory
    path('inventory/', views.ngo_inventory, name='ngo_inventory'),
    path('inventory/<int:inventory_id>/update/', views.update_inventory, name='update_inventory'),
    
    # Donation Request Routes
    path('request/<int:req_id>/', views.donation_request_detail, name='donation_request_detail'),
    
    # Delivery-related internal routes removed (porter flow in use)
    path('admin/porter/requests/', views.admin_delivery_requests, name='admin_delivery_requests'),
    
    # Live-tracking APIs removed; external partner tracking used instead
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Messaging
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/<int:conv_id>/', views.message_detail, name='message_detail'),
    path('medicine/<int:med_id>/contact-donor/', views.start_conversation, name='start_conversation'),
    
    # Admin Routes
    path('reports/', views.admin_reports, name='admin_reports'),
    path('reports-advanced/', views.admin_reports_advanced, name='admin_reports_advanced'),
    path('reports/export-csv/', views.export_reports_csv, name='export_reports_csv'),
    
    # Medicine Verification (Admin)
    path('verifications/', views.medicine_verifications, name='medicine_verifications'),
    path('verify-medicine/<int:verification_id>/', views.verify_medicine, name='verify_medicine'),
    
    # AI-Powered Chatbot Routes
    path('chatbot/', chatbot_views.medicine_chatbot, name='medicine_chatbot'),
    path('chat-history/', chatbot_views.chat_history, name='chat_history'),
    
    # API Endpoints
    path('api/medicine-search/', views.api_medicine_search, name='api_medicine_search'),
    path('api/emergency-alerts/', views.api_emergency_alerts, name='api_emergency_alerts'),
    path('api/subcategories/', views.api_subcategories, name='api_subcategories'),
    
    # Chatbot APIs
    path('api/chat/message/', chatbot_views.chat_message_api, name='chat_message'),
    path('api/chat/history/', chatbot_views.chat_history_api, name='chat_history_api'),
    path('api/chat/clear/', chatbot_views.clear_chat_history, name='clear_chat_history'),
    path('api/quick-qa/', chatbot_views.quick_medicine_answer, name='quick_qa'),
    
    # Static Pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('add-testimonial/', views.add_testimonial, name='add_testimonial'),
    path('testimonials/', views.testimonials, name='testimonials'),
]
