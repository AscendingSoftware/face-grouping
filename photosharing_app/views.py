from django.http import JsonResponse
from django.http import HttpRequest
from rest_framework import status as http_status
from rest_framework.decorators import api_view
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
import base64
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
import json
from django.core.files.base import ContentFile
from django.db import transaction
import cv2
import numpy as np
import face_recognition
from sklearn.cluster import DBSCAN
import logging
from django.core.mail import send_mail
from .utils import send_notification  # Import the send_notification function
import smtplib
from django.views.decorators.csrf import csrf_exempt
# from .signals import admin_added

@api_view(['POST'])
def post_plan(request):
    if request.method == 'POST':
        data = request.data
        try:
            plan = Plan.objects.create(
                plan_name=data.get('plan_name'),
                description=data.get('description'),
                price=data.get('price'),
                max_admins=data.get('max_admins'),
                max_users=data.get('max_users'),
                max_events=data.get('max_events'),
                max_storage=data.get('max_storage'),
                validity_period=data.get('validity_period')
            )
            return Response({'message': 'Plan created successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def admin_registration(request):
    if request.method == 'POST':
        serializer = AdminRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            admin_data = serializer.validated_data
            plan_id = admin_data.get('plan_id')
            if not plan_id:
                # Admin has not chosen a plan, return a page to choose a plan
                plans = Plan.objects.all()
                plan_serializer = PlanSerializer(plans, many=True)
                return Response({'message': 'Choose a plan', 'plans': plan_serializer.data}, status=status.HTTP_200_OK)
            else:
                # Admin has chosen a plan, proceed with registration
                admin_instance = serializer.save()
                return Response({'message': 'Admin registered successfully', 'admin_id': admin_instance.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_organization_and_link_admin(request, admin_id):
    admin_status = request.data.get('status', 'False')  # Default to 'False' if not provided
    
    # Convert admin_status to a boolean for internal logic
    is_admin_active = admin_status.lower() == 'true'
    
    if is_admin_active:
        admin = AdminRegistration.objects.filter(id=admin_id, status=True).first()
        if not admin:
            return Response({'error': 'Admin not found or status is false'}, status=http_status.HTTP_404_NOT_FOUND)
        
        organization_data = {
            'admin': admin.id,
            'plan_id': admin.plan_id,
            'company_name': admin.company_name,
            'status': True
        }
        organization_serializer = OrganizationSerializer(data=organization_data)
        
        if organization_serializer.is_valid():
            organization = organization_serializer.save()
            admin.organization = organization
            admin.save()
            return Response({'message': 'Organization created and admin updated successfully'}, status=http_status.HTTP_201_CREATED)
        else:
            return Response(organization_serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)
    
    else:  # When admin_status is 'False'
        organization_serializer = OrganizationSerializer(data=request.data)
        
        if organization_serializer.is_valid():
            organization = organization_serializer.save()
            try:
                admin_instance = AdminRegistration.objects.get(id=admin_id)
                admin_instance.organization = organization
                admin_instance.save()
                return Response({'message': 'Organization created and admin updated successfully'}, status=http_status.HTTP_201_CREATED)
            except AdminRegistration.DoesNotExist:
                return Response({'error': 'Admin registration not found'}, status=http_status.HTTP_404_NOT_FOUND)
        else:
            return Response(organization_serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


# def create_organization(request):
#     if request.method == 'POST':
#         json_data = json.loads(request.body)
        
#         # Ensure status is True to allow organization creation
#         status_value = json_data.get('status')
#         if status_value is not True:
#             return JsonResponse({'error': 'Status must be True to create an organization'}, status=status.HTTP_400_BAD_REQUEST)

#         logo_data = json_data.get('logo', '')
#         if logo_data:
#             try:
#                 if logo_data.startswith('data:image'):
#                     format, imgstr = logo_data.split(';base64,')
#                     ext = format.split('/')[-1]
#                     logo_data = ContentFile(base64.b64decode(imgstr), name=f'logo.{ext}')
#                 else:
#                     raise ValueError
#             except (ValueError, TypeError):
#                 return JsonResponse({'error': 'Invalid logo data format'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             admin_id = json_data.get('admin_id', '')
#             if not admin_id:
#                 raise ValidationError("Admin ID cannot be empty")
#             admin_instance = get_object_or_404(AdminRegistration, pk=admin_id)

#             # Parse plan_subscription_date as datetime object
#             plan_subscription_date = json_data.get('plan_subscription_date')
#             if plan_subscription_date:
#                 plan_subscription_date = timezone.make_aware(datetime.strptime(plan_subscription_date, '%Y-%m-%dT%H:%M:%S'))

#             # Check for empty or whitespace-only company name
#             company_name = json_data.get('company_name', '').strip()
#             if not company_name:
#                 raise ValidationError("Company name cannot be empty")

#             # Check for existing organization with the same company name
#             if Organization.objects.filter(company_name__iexact=company_name).exists():
#                 raise ValidationError("Company name already exists")

#             organization = Organization.objects.create(
#                 admin=admin_instance,
#                 plan_id=json_data.get('plan_id', ''),
#                 company_name=company_name,
#                 plan_subscription_date=plan_subscription_date,
#                 plan_expired_date=json_data.get('plan_expired_date', ''),
#                 status=json_data.get('status', ''),  # Ensure that status is either True or False
#                 logo=logo_data  
                
#             )
#             return JsonResponse({'message': 'Organization created successfully'}, status=status.HTTP_201_CREATED)
#         except ValidationError as ve:
#             return JsonResponse({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
def create_event(request):
    try:
        if request.method == 'POST':
            serializer = EventSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Event created successfully'}, status=status.HTTP_201_CREATED)
        try:
          if request.method == 'POST':
            admin_id = request.data.get('created_by')
            admin = Organization.objects.get(pk=admin_id)
            max_events_allowed = admin.plan.max_events
            current_events_count = Event.objects.filter(created_by=admin).count()

            if current_events_count < max_events_allowed:
                serializer = EventSerializer(data=request.data)
                if serializer.is_valid():
                    # Debugging statement
                    print("Event data to be saved:", serializer.validated_data)
                    event = serializer.save(created_by=admin)
                    # Debugging statement
                    print("Event saved successfully:", event)
                    send_notification(admin.admin.email, 'You created another event successfully')
                    return Response({'message': 'Event created successfully'}, status=status.HTTP_201_CREATED)
                else:
                    # Debugging statement
                    print("Serializer errors:", serializer.errors)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                send_notification(admin.admin.email, 'Upgrade your plan to add more events')
                return Response({'message': 'Upgrade your plan to add more events'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
          return Response({'message': 'Some required object does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
# @csrf_exempt 
@api_view(['POST'])
def upload_event_images(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'message': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        admin_id = request.data.get('created_by')
        if not admin_id:
            return JsonResponse({'message': 'Admin ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Identify Admin, Event, and Organization
        try:
            admin = AdminRegistration.objects.get(admin_id=admin_id)
            organization = Organization.objects.get(admin=admin)
        except ObjectDoesNotExist:
            return JsonResponse({'message': 'Admin or Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        event_id = request.data.get('event')
        print(event_id)
        if not event_id:
            return JsonResponse({'message': 'Event ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(pk=event_id)
            print(event)
        except Event.DoesNotExist:
            # Handle case where the event with the provided ID does not exist
            return JsonResponse({'message': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        # except Exception as e:
        #    # Handle other exceptions, such as database errors
        #    return JsonResponse({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 2: Get Storage Limit from Organization's Plan
        plan_storage_limit_mb = organization.plan.max_storage
        print(plan_storage_limit_mb)

        # Step 3: Calculate Current Storage Usage from Database
        current_table_size_mb = get_folder_size(event.event_name, event.id)
        print(current_table_size_mb)

        # Step 4: Calculate Total Size of Uploaded Images
        uploaded_images = request.FILES.getlist('images')
        total_uploaded_size_mb = sum(image.size for image in uploaded_images) / (1024 * 1024)
        print(total_uploaded_size_mb)

        # Step 5: Compare Remaining Storage with Uploaded Images
        remaining_space_mb = plan_storage_limit_mb - current_table_size_mb
        print(remaining_space_mb)
        if remaining_space_mb >= total_uploaded_size_mb:
            # Generate a unique folder name using UUID
            folder_name = f"{event.event_name}_{event.id}"
            print(folder_name)
            # Store uploaded images in the local folder path
            for img in uploaded_images:
                try:
                    # Log the image name and size for debugging
                    print(f"Processing image: {img.name}, size: {img.size} bytes")

                    # Create the EventImage object
                    event_image = EventImage(event=event, image=img)
                    event_image.admin = organization  # Assign the correct organization object
                    event_image.uploaded_at = timezone.now()
                    event_image.save()

                    # Log the event_image object for debugging
                    print(f"EventImage saved: {event_image}")

                    # Save the image to the local folder
                    save_image_to_folder(img, folder_name)
                    print(f"Image {img.name} saved to folder {folder_name}")

                except Exception as e:
                    print(f"Error saving image {img.name}: {str(e)}")
                    return JsonResponse({'message': f"Error saving image {img.name}: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            send_notification(admin.email, 'Event Images Uploaded Successfully')
            return JsonResponse({'message': 'Event images uploaded successfully'}, status=status.HTTP_201_CREATED)
        else:
            images_possible = remaining_space_mb / (total_uploaded_size_mb / len(uploaded_images))
            send_notification(admin.email, f'Upgrade Your Plan. Insufficient storage space to upload all images. Only {images_possible:.2f} images could be uploaded.')
            return JsonResponse({'message': 'Insufficient storage space. Upgrade your plan.'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    except Exception as e:
        print(f"General error: {str(e)}")
        return JsonResponse({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def save_image_to_folder(image, folder_name):
    folder_path = f"./{folder_name}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(os.path.join(folder_path, image.name), 'wb+') as destination:
        for chunk in image.chunks():
            destination.write(chunk)

def get_folder_size(event_name, event_id):
    total_size = 0
    folder_path = f"./{event_name}_{event_id}"
    print(folder_path)
    if os.path.exists(folder_path):
        # Walk through all the files in the given folder
        for _, _, filenames in os.walk(folder_path):
            for filename in filenames:
                # Get the size of each file and add it to the total size
                file_path = os.path.join(folder_path, filename)
                total_size += os.path.getsize(file_path)
    # Convert total_size to megabytes
    total_size_mb = total_size / (1024 * 1024)
    return total_size_mb   

# @api_view(['POST'])
# def admin_login(request):
#     if request.method == 'POST':
#         email = request.data.get('email')
#         password = request.data.get('password')
#         # print("Received email:", email)
#         # print("Received password:", password)
        
#         # Check if the email exists in AdminRegistration
#         admin = get_object_or_404(AdminRegistration, email=email)
#         # Verify the password
#         if admin.password == password:
#            try:
#               # Retrieve admin details
#               admin = AdminRegistration.objects.get(email=email, password=password)
#               admin_serializer = AdminRegistrationSerializer(admin)
#               print("Admin Details Serialized:", admin_serializer.data)

#               # Retrieve subscription plan details
#               subscription_plan = SubscriptionPlan.objects.all()
#               subscription_plan_serializer = SubscriptionPlanSerializer(subscription_plan, many=True)
#               print("Subscription Plan Serialized:", subscription_plan_serializer.data)

#               # Retrieve event details
#               event = Event.objects.all()
#               event_serializer = EventSerializer(event, many=True)
#               print("Event Serialized:", event_serializer.data)

#               response_data = {
#                  'admin_details': admin_serializer.data,
#                  'plan_details': subscription_plan_serializer.data,
#                  'event_details': event_serializer.data,
#               }
#               return JsonResponse(response_data)
#            except AdminRegistration.DoesNotExist:
#             return JsonResponse({'error': 'Invalid credentials'}, status=400)
#     else:
#         return JsonResponse({'error': 'Method not allowed'}, status=405)        

# def get_total_image_size(table_name, column_name):
#     try:
#         conn = mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="3333",
#             database="photo_sharing"
#         )
#         cursor = conn.cursor()

#         query = "SELECT image FROM EventImage;"
#         cursor.execute(query)
#         results = cursor.fetchall()

#         total_size_mb = 0
#         for result in results:
#             image_size = result[0].strip().upper()

#             if image_size.isdigit():
#                 # Size is in bytes, convert to MB
#                 image_size_mb = int(image_size) / (1024 * 1024)
#             elif image_size.endswith('KB'):
#                 # Size is in kilobytes, convert to MB
#                 image_size_mb = float(image_size[:-2]) / 1024
#             elif image_size.endswith('MB'):
#                 # Size is already in megabytes
#                 image_size_mb = float(image_size[:-2])
#             else:
#                 # Handle invalid format or units
#                 print(f"Skipping invalid image size format: {image_size}")
#                 continue
            
#             total_size_mb += image_size_mb

#         cursor.close()
#         conn.close()

#         return total_size_mb
#     except mysql.connector.Error as err:
#         print(f"Database error: {err}")
#         return 0

# # Usage
# table_name = "photosharing_app_eventimage"
# column_name = "image"  # Ensure this column contains the image sizes
# total_size_mb = get_total_image_size(table_name, column_name)
# if total_size_mb is not None:
#     print(f"The total size of all images in table {table_name} is: {total_size_mb:.2f} MB")
# else:
#     print(f"Error occurred while calculating total image size.")


# @api_view(['POST'])
# def images_details(request):
#     print("images_details function called")  # Check if the function is being called

#     # Convert DRF Request object to Django HttpRequest object
#     django_request = request._request if hasattr(request, '_request') else request

#     # Access the request data based on the type of request object
#     if isinstance(django_request, HttpRequest):
#         # Django HttpRequest object
#         request_data = django_request.POST  # Assuming form data is being sent
#     else:
#         # WSGIRequest object (Django's default request object)
#         request_data = django_request.data

#     print("Request data:", request_data)  # Check the request data being processed

#     # Assuming ImageDetailsSerializer is defined correctly
#     serializer = ImageDetailsSerializer(data=request_data)
#     if serializer.is_valid():
#         serializer.save()
#         return JsonResponse({'message': 'Image details saved successfully'}, status=status.HTTP_201_CREATED)
#     return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  

# @api_view(['POST'])
# def subscribe(request):
#     if request.method == 'POST':
#         # Deserialize request data using serializers
#         plan_serializer = PlanSerializer(data=request.data)
#         if plan_serializer.is_valid():
#             # Retrieve the selected plan
#             selected_plan = plan_serializer.validated_data['plan_id']

#             # Assuming you also pass pay_amount in the request data
#             pay_amount = request.data.get('pay_amount')

#             # Create an account for the admin with the selected plan and payment details
#             account_data = {'created_by': selected_plan, 'pay': pay_amount}
#             account_serializer = AccountSerializer(data=account_data)
#             if account_serializer.is_valid():
#                 account_serializer.save()
#                 return Response({'message': 'Subscription successful'}, status=201)
#             else:
#                 return Response(account_serializer.errors, status=400)
#         else:
#             return Response(plan_serializer.errors, status=400)
        



# @api_view(['POST'])
# def plan_subscription(request):
#     if request.method == 'POST':
#         serializer = SubscriptionPlanSerializer(data=request.data)
#         if serializer.is_valid():
#             payment_information = serializer.validated_data.get('payment_information')
#             if SubscriptionPlan.objects.filter(payment_information=payment_information).exists():
#                 return Response({'message': 'Plan subscription failed. Admin has already paid for this plan.'}, status=status.HTTP_400_BAD_REQUEST)
            
#             with transaction.atomic():
#                 serializer.save()
                
#             return Response({"message": "Plan subscription successful"}, status=status.HTTP_201_CREATED)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     return Response({'success': False, 'message': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)


# # logger = logging.getLogger(__name__)

# @api_view(['POST'])
# def upload_event_images(request, event_id):  
#     try:
#         if request.method == 'POST':
#             admin_id = request.data.get('admin_id')

#             try:
#                 admin = AdminRegistration.objects.get(admin_id=admin_id)

#                 try:
#                     event = Event.objects.get(event_id=event_id)  

#                     # Retrieve uploaded images and calculate total size
#                     event_images = request.FILES.getlist('images')
#                     total_size_kb = sum(image.size for image in event_images) / 1024  # Convert to KB

#                     # Check if event already has uploaded images
#                     existing_images = EventImage.objects.filter(event=event)
#                     existing_total_size_kb = sum(image.image.size for image in existing_images) / 1024   # Convert to KB

#                     # Check subscription plan details
#                     plan_subscription = SubscriptionPlan.objects.get(created_by=admin)
#                     plan = Plan.objects.get(plan_id=plan_subscription.plan_id)

#                     # Calculate total size including existing images
#                     total_size_with_existing_kb = total_size_kb + existing_total_size_kb

#                     # Check Maximum Storage
#                     if total_size_with_existing_kb <= plan.max_storage:
#                         # Handle Successful Upload
#                         remaining_storage_kb = plan.max_storage - total_size_with_existing_kb

#                         # Save the uploaded images
#                         for image in event_images:
#                             EventImage.objects.create(event=event, image=image)

#                         # Send email notification
#                         if send_notification(admin.email, "Event"):
#                             send_mail(
#                                 'Event Images Uploaded Successfully',
#                                 f'You have successfully uploaded event images. Remaining storage: {remaining_storage_kb} KB',
#                                 'your@example.com',
#                                 [admin.email],  # Here, we access the admin's email directly
#                                 fail_silently=False,
#                             )
#                         return Response({"success": True, "message": "Event images uploaded successfully.", "remaining_storage": remaining_storage_kb}, status=status.HTTP_200_OK)
#                     else:
#                         # Handle Storage Exceeded
#                         # Send email notification for storage limit exceeded
#                         if send_notification(admin.email, "Storage Limit Exceeded"):
#                             send_mail(
#                                 'Storage Limit Exceeded',
#                                 'Your event images could not be uploaded because storage limit exceeded. Please upgrade your plan.',
#                                 'your@example.com',
#                                 [admin.email],  # Access the admin's email directly
#                                 fail_silently=False,
#                             )
#                         return Response({"success": False, "message": "Storage limit exceeded. Please upgrade your plan."}, status=status.HTTP_400_BAD_REQUEST)
#                 except Event.DoesNotExist:
#                     return Response({"success": False, "message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
#             except AdminRegistration.DoesNotExist:
#                 return Response({"success": False, "message": "Admin not found."}, status=status.HTTP_404_NOT_FOUND)

#     except smtplib.SMTPConnectError as e:
#         # Handle SMTP connection error
#         return Response({"success": False, "message": f"An error occurred: SMTP connection error - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     # except Exception as e:
#     #     return Response({"success": False, "message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     return Response({"success": False, "message": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)





 # # Encode faces and perform clustering for each uploaded image
    # for image_instance in uploaded_images:
    #     encode_faces(image_instance)
   

# def encode_faces(image_instance):
#     try:
#         with transaction.atomic():
#             # Load the image
#             image_data = image_instance.image.read()
#             if not image_data:
#                 logger.error("Empty image data received")
#                 return

#             image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
#             if image is None:
#                 logger.error("Failed to decode the image")
#                 return

#             # Convert the image to RGB format
#             rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

#             # Detect faces in the image
#             face_locations = face_recognition.face_locations(rgb_image)
#             # print(face_locations)

#             if not face_locations:
#                 logger.warning("No faces detected in the image")
#                 return

#             # Encode faces
#             face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
#             # print(face_encodings)

#             # Save the encodings to the database
#             save_encodings(image_instance, face_encodings)

#             # Perform clustering on the encodings
#             perform_clustering()

#     except Exception as e:
#         logger.exception("Error occurred while encoding faces")

# def save_encodings(image_instance, encodings):
#     with transaction.atomic():
#         for encoding in encodings:
#             # Ensure encoding is not a scalar or function reference
#             if isinstance(encoding, np.ndarray):
#                 # Convert encoding to a list
#                 encoding_list = encoding.tolist()
#                 # Convert the list to a string representation
#                 encoding_str = ','.join(map(str, encoding_list))
#                 if encoding_str:  # Check if the encoding string is not empty
#                     # Serialize the list to JSON
#                     encoding_json = json.dumps(encoding_list)
#                     # Encode the string before saving
#                     encoding_bytes = encoding_json.encode('utf-8')
#                     # Save the face encoding to the database
#                     FaceEncoding.objects.create(image=image_instance, encoding=encoding_bytes)
#                 else:
#                     logger.warning("Empty encoding detected, skipping saving to database")
#             else:
#                 logger.warning("Invalid encoding detected: {}".format(encoding))

# def perform_clustering():
#     # Retrieve all face encodings from the database
#     encodings = list(FaceEncoding.objects.all())

#     if not encodings:
#        print("No face encodings found in the database.")
#        return

#     # Extract encodings and convert them to numpy array
#     encodings_list = []
#     for encoding in encodings:
#         encoding_str = encoding.encoding.decode('utf-8')
#         print("Encoding string:", encoding_str)  # Print encoding string for debugging
#         # Remove square brackets, split the string, strip whitespace, and convert each value to float
#         encoding_values = [float(value.strip()) for value in encoding_str.strip('[]').split(',')]
#         encodings_list.append(encoding_values)
#     encodings_array = np.array(encodings_list)

#     # Cluster the embeddings
#     print("[INFO] Clustering...")
#     clt = DBSCAN(metric="euclidean", n_jobs=-1)
#     clt.fit(encodings_array)

#     # Create a dictionary to store clustered faces
#     clustered_faces = {}

#     # Loop over the unique face integers
#     for labelID in np.unique(clt.labels_):
#         # Skip unknown faces
#         if labelID == -1:
#             continue

#         # Find all indexes into the `encodings_array` that belong to the current label ID
#         idxs = np.where(clt.labels_ == labelID)[0]

#         # Initialize list to store faces for the current cluster
#         cluster_faces = []

#         # Loop over the sampled indexes
#         for i in idxs:
#             cluster_faces.append({"image_instance": encodings[i].image})

#         # Store the faces for the current cluster
#         clustered_faces[labelID] = cluster_faces

#     # Save the clustered faces to the database
#     save_clustered_faces_to_db(clustered_faces)

#     print("[INFO] Clustered faces saved to the database.")

# def save_clustered_faces_to_db(clustered_faces):
#     for labelID, cluster_faces in clustered_faces.items():
#         # Convert labelID to Python integer
#         labelID = int(labelID)
#         for face_data in cluster_faces:
#             image_instance = face_data["image_instance"]
            
#             # Retrieve the associated FaceEncoding instance
#             face_encoding_instance = get_face_encoding_instance(image_instance)
            
#             # Save the clustered face to the database
#             if face_encoding_instance:
#                 ClusteredFaces.objects.create(face_encoding=face_encoding_instance, clustered_faces=labelID)
#             else:
#                 print(f"No FaceEncoding found for EventImage: {image_instance}")

# def get_face_encoding_instance(image_instance):
#     # Here, implement the logic to retrieve the associated FaceEncoding instance
#     # This could involve querying the database or using any other method you have in your application
#     # For example:
#     try:
#         return FaceEncoding.objects.get(image=image_instance)
#     except FaceEncoding.DoesNotExist:
#         return None
    


# # Call this function before saving each event image
# def save_event_image(event_image, admin):
#     check_storage_and_notify(admin)
#     event_image.save()