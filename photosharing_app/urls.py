from django.urls import path
from . import views
# from .views import admin_login
# from photosharing_app import views

# Define your app-level URLs
urlpatterns = [
    path('plans/', views.post_plan, name='post_plan'),
    path('admin-registration/', views.admin_registration, name='admin_registration'),
    path('organization/<int:admin_id>/', views.create_organization_and_link_admin, name='organization'),
    path('event/', views.create_event, name='create_event'),
    path('upload_event_images/', views.upload_event_images, name='upload_event_images'),
    # path('subscription/', views.plan_subscription, name='plan_subscription'),
    # path('admin/login/', views.admin_login, name='admin_login'),
    
    # path('events/<int:event_id>/upload-images/', views.upload_event_images, name='upload_event_images'),


    # path('admin-registration/<str:plan_name>/', views.admin_registration, name='admin_registration'),
    # path('subscription/<int:created_by>/', views.plan_subscription, name='plan_subscription'),
    # path('event/<int:created_by>/', views.create_event, name='create_event'),
    # Add other URL patterns as needed
]