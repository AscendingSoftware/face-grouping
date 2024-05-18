from rest_framework import serializers
from .models import *

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class AdminRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminRegistration
        fields = '__all__'     

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'    

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class EventImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()  # Define image field as ImageField

    class Meta:
        model = EventImage
        fields = '__all__'

# class ImageDetailsSerializer(serializers.ModelSerializer):
#     # Define fields according to your requirements
#     image_id = serializers.IntegerField(source='id')  # Assuming id field is image_id
#     organization_id = serializers.IntegerField(source='admin.id')  # Assuming admin field is ForeignKey to Organization
#     event_id = serializers.IntegerField(source='event.id')  # Assuming event field is ForeignKey to Event
#     uploaded_date = serializers.DateTimeField(source='uploaded_at')  # Assuming uploaded_at is the datetime field
#     is_new = serializers.BooleanField()

#     class Meta:
#         model = EventImage
#         fields = ['image_id', 'organization_id', 'event_id', 'uploaded_date', 'is_new']

# class AccountSerializer(serializers.ModelSerializer):
#      class Meta:
#          model = Account
#          fields = '__all__'       

         


       





# # class FaceEncodingSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = FaceEncoding
# #         fields = '__all__'  # Add more fields as needed  

# # class ClusteredFaceSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = ClusteredFaces
# #         fields = '__all__'  # Add more fields as needed                      