"""
URL configuration for auth_integration app.
"""
from django.urls import path
from . import api_views, views

app_name = 'auth_integration'

urlpatterns = [
    # VPN authentication endpoints
    path('vpn/auth/', api_views.vpn_auth_view, name='vpn_auth'),
    path('vpn/status/', api_views.vpn_status_view, name='vpn_status'),
    path('vpn/refresh/', api_views.vpn_refresh_view, name='vpn_refresh'),
    path('vpn/clear-cache/', api_views.vpn_clear_cache_view, name='vpn_clear_cache'),
    
    # Token management endpoint
    path('vpn/token/', api_views.VPNTokenView.as_view(), name='vpn_token'),
    
    # User authentication views
    path('login/', views.jwt_login_view, name='jwt_login'),
    path('logout/', views.jwt_logout_view, name='jwt_logout'),
    path('callback/', views.jwt_callback_view, name='jwt_callback'),
    path('status/', views.auth_status_view, name='auth_status'),
    path('instructions/', views.auth_instructions_view, name='auth_instructions'),
    path('generate-token/', views.generate_user_token_view, name='generate_token'),
    path('jwt-token-async/', views.jwt_token_async_view, name='jwt_token_async'),
]

