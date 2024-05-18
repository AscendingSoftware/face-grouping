from django.dispatch import receiver
from django.db.models.signals import post_save
from datetime import datetime
# from django.contrib.auth.models import User
from django.db import models
import uuid
import os
from django.utils import timezone
from datetime import timedelta
    
class Plan(models.Model):
    plan_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    max_admins = models.IntegerField(default=1, null=False, blank=False)
    max_users = models.IntegerField(default=10, null=False, blank=False)
    max_events = models.IntegerField(default=10, null=False, blank=False)
    max_storage = models.CharField(help_text="max_storage in MB", max_length=100, null=False, blank=False)  # In MB
    validity_period = models.CharField(help_text="Validity period in months", max_length=100,null=False, blank=False)

    def __str__(self):
        return self.plan_name

class AdminRegistration(models.Model):
    plan_id = models.IntegerField(unique=True, null=False, blank=False)
    role = models.CharField(max_length=255, unique=True, null=False, blank=False)
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    email = models.EmailField(max_length=254, unique=True, null=False, blank=False)
    password = models.CharField(max_length=128, null=False, blank=False)
    contact_number = models.CharField(max_length=15, unique=True, null=False, blank=False)
    address = models.CharField(max_length=255, unique=True,null=False, blank=False)
    company_name = models.CharField(unique=True, null=False, blank=False,max_length=255)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='admin_registrations', null=True, blank=True)
    logo = models.ImageField(upload_to='company_logo/', null=True, blank=True)
    status = models.BooleanField(default=False)

class Organization(models.Model):
    status = models.OneToOneField(AdminRegistration, on_delete=models.CASCADE, related_name='organizations_status')
    admin = models.ForeignKey(AdminRegistration, on_delete=models.CASCADE, related_name='organizations_admin')
    plan_id = models.OneToOneField(AdminRegistration, on_delete=models.CASCADE, related_name='organizations_plan')
    company_name = models.OneToOneField(AdminRegistration, on_delete=models.CASCADE, related_name='organization_company_name')
    subscription_date = models.DateTimeField(null=False, blank=False)
    plan_expired_date = models.DateTimeField(null=False, blank=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # Check if it's a new instance
            last_organization = Organization.objects.order_by('-id').first()
            if last_organization:
                last_id = int(last_organization.id[1:])  # Get the numeric part of the last ID
                new_id = 'o{:06d}'.format(last_id + 1)  # Increment the numeric part and format as string
            else:
                new_id = 'o000001'  # If no existing organization, start with 'o000001'
            self.pk = new_id
        
        # Retrieve plan_expired_date based on subscription_date and plan validity
        if not self.plan_expired_date:
            validity_period = timedelta(days=self.plan.validity_period)
            self.plan_expired_date = self.subscription_date + validity_period

        super().save(*args, **kwargs)   

class Event(models.Model):
    created_by = models.OneToOneField(Organization, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=255, null=False, blank=False)
    venue = models.CharField(max_length=255, null=False, blank=False)
    start_date = models.DateTimeField( null=False, blank=False)
    end_date = models.DateTimeField( null=False, blank=False)
    duration = models.IntegerField(blank=True, null=True)
    unique_code = models.CharField(default=uuid.uuid4().hex[:6], editable=False, unique=True, max_length=6)

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            # Calculate duration in hours
            self.duration = (self.end_date - self.start_date).total_seconds() // 3600
        if not self.pk:  # Check if the primary key is not set
            # If primary key is not set, it's a new record, so generate unique_code
            self.unique_code = uuid.uuid4().hex[:6]
        super(Event, self).save(*args, **kwargs)   

def event_image_path(instance, filename):
    return os.path.join("event_images", filename)

class EventImage(models.Model):
    image = models.ImageField(upload_to='event_images/')
    admin = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    event = models.ForeignKey('Event', related_name='images', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # is_new = models.BooleanField(default=True)

#     def save(self, *args, **kwargs):
#         if not self.uploaded_at:  # Check if uploaded_at is not set
#             self.uploaded_at = timezone.now()  # Set uploaded_at to current time if not set
#         if self.uploaded_at >= timezone.now() - timezone.timedelta(days=7):
#             self.is_new = True
#         else:
#             self.is_new = False
#         super().save(*args, **kwargs)

# class SubscriptionPlan(models.Model):  
#     created_by = models.OneToOneField(Organization, on_delete=models.CASCADE)
#     plan_id = models.IntegerField(default=1, null=False, blank=False)
#     plan_name = models.CharField(max_length=50, null=False, blank=False)
#     price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
#     subscription_date = models.DateTimeField(default=None, null=False, blank=False)         
#     subscription_status = models.BooleanField(default=False, null=False, blank=False)
#     payment_information = models.TextField(default=None, null=False, blank=False) 
#     expired_date = models.DateTimeField(null=True, blank=True)  

#     def set_expired_date(self):
#         # Fetch the Plan object based on plan_id
#         plan = Plan.objects.get(plan_id=self.plan_id)

#         # Calculate the expired date by adding validity_period to the subscription_date
#         expired_date = self.subscription_date + timedelta(days=plan.validity_period)

#         # Set the expired date with time
#         self.expired_date = expired_date
#         self.save()
   



 

# # class FaceEncoding(models.Model):
# #     image = models.ForeignKey(EventImage, on_delete=models.CASCADE)
# #     encoding = models.BinaryField() 

# # class ClusteredFaces(models.Model):
# #     face_encoding = models.ForeignKey(FaceEncoding, on_delete=models.CASCADE)
# #     clustered_faces = models.JSONField()
 





