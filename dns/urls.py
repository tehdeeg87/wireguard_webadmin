from django.urls import path
from . import api_views, views

app_name = 'dns'

urlpatterns = [
    path('coredns/', views.view_coredns_management, name='coredns_management'),
    path('coredns/status/', views.view_coredns_status, name='coredns_status'),
    path('api/update-zones/', api_views.update_coredns_zones, name='update_zones'),
    path('api/status/', api_views.coredns_status, name='coredns_status'),
]
