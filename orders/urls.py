from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_form, name='order_form'),
    path('success/', views.order_success, name='order_success'),
] 