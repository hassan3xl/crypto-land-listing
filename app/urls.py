from django.urls import path
from app import views

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Land Catalogue & Management
    path('api/lgas/', views.get_lgas_api, name='get_lgas_api'),
    path('api/exchange-rates/', views.get_exchange_rates_api, name='get_exchange_rates_api'),
    path('lands/', views.land_list, name='land_list'),
    path('lands/create/', views.create_land, name='create_land'),
    path('lands/<slug:slug>/', views.land_detail, name='land_detail'),
    path('lands/<slug:slug>/edit/', views.edit_land, name='edit_land'),
    path('lands/<slug:slug>/delete/', views.delete_land, name='delete_land'),
    path('lands/<slug:slug>/offer/', views.submit_offer, name='submit_offer'),
    path('lands/<int:land_id>/save/', views.toggle_save_land, name='toggle_save_land'),
    
    # Offer & Payment Processing
    path('offers/<uuid:transaction_id>/respond/', views.respond_to_offer, name='respond_to_offer'),
    path('offers/<uuid:transaction_id>/pay/', views.submit_payment_hash, name='submit_payment_hash'),
    
    # User Dashboards
    path('buyer/dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Admin Panel
    path('platform-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('platform-admin/approve/<int:land_id>/', views.approve_land_listing, name='approve_land_listing'),
    path('platform-admin/confirm-escrow/<uuid:transaction_id>/', views.confirm_escrow_payment, name='confirm_escrow_payment'),
    path('platform-admin/user-verify/<int:user_id>/', views.toggle_user_verification, name='toggle_user_verification'),
]
