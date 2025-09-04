from django.urls import path
from . import views
app_name = 'orders'

urlpatterns = [
    path('', views.order_form, name='order_form'),
    path('processpaymentsuccess', views.process_payment_success, name='process_payment_success'),
    path('configure/<uuid:token>/', views.configure_instance, name='configure_instance'),
    path('success/', views.order_success, name='order_success'),
   
    

] 