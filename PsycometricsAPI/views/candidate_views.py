from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..db.mongo import candidate_collection, result_collection
from ..serializers import CandidateSerializer
from ..utils.objectIdConversion import convert_objectid
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from rest_framework.parsers import MultiPartParser
import uuid
from azure.core.exceptions import ResourceExistsError
import requests
import random
import string

@api_view(["GET", "POST"])
def candidate_list(request):
    if request.method == "GET":
        candidates = list(candidate_collection.find())
        candidates = [convert_objectid(c) for c in candidates]
        return Response(candidates)

    elif request.method == "POST":
        data = request.data
        required_fields = ["email", "first_name", "last_name", "age", "gender", "phone"]
        for field in required_fields:
            if field not in data or not data[field]:
                return Response(
                    {"error": f"{field} is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if email already exists
        if candidate_collection.find_one({"email": data["email"]}):
            return Response(
                {"error": "A candidate with this email already exists."},
                status=status.HTTP_409_CONFLICT
            )

        # Generate a unique 6-character code
        def generate_unique_code():
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not candidate_collection.find_one({"code": code}):
                    return code

        unique_code = generate_unique_code()

        # Validate and upload CV
        cv_file = request.FILES.get("cv")
        if not cv_file:
            return Response(
                {"error": "CV file is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not cv_file.name.endswith(".pdf"):
            return Response(
                {"error": "CV must be a PDF file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate a unique file name
        unique_file_name = f"{uuid.uuid4()}_{cv_file.name}"

        # Upload CV to Azure Blob Storage
        try:
            blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            container_name = settings.AZURE_STORAGE_CONTAINER_NAME
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=unique_file_name)

            # Check if the blob already exists
            if blob_client.exists():
                return Response(
                    {"error": f"A file with the name '{unique_file_name}' already exists in the storage."},
                    status=status.HTTP_409_CONFLICT
                )

            # Upload the file
            blob_client.upload_blob(cv_file, overwrite=False)
            cv_url = blob_client.url
        except ResourceExistsError:
            return Response(
                {"error": f"A file with the name '{unique_file_name}' already exists in the storage."},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to upload CV: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Set hr ObjectId (hardcoded as requested)
        hr_object_id = ObjectId("68634fee4a86e24702186e63")

        candidate_doc = {
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "age": data["age"],
            "gender": data["gender"],
            "phone": data["phone"],
            "hr": hr_object_id,
            "cv": cv_url,
            "candidate_evaluation": "pending",
            "code": unique_code
        }

        result = candidate_collection.insert_one(candidate_doc)

        response_data = {
            "id": str(result.inserted_id),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "age": data["age"],
            "gender": data["gender"],
            "email": data["email"],
            "phone": data["phone"],
            "hr_id": str(hr_object_id),
            "cv": candidate_doc["cv"],
            "candidate_evaluation": candidate_doc["candidate_evaluation"],
            "code": candidate_doc["code"]
        }

        # Trigger the webhook
        webhook_url = "https://gilrubio.app.n8n.cloud/webhook/candidate-registered"
        webhook_payload = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data["email"],
            "code": candidate_doc["code"],
        }
        try:
            webhook_response = requests.post(webhook_url, json=webhook_payload, timeout=5)
            if webhook_response.status_code != 200:
                print(f"Webhook failed with status code {webhook_response.status_code}: {webhook_response.text}")
        except Exception as e:
            print(f"Failed to send webhook: {str(e)}")

        return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE", "PUT"])
def candidate_detail(request, id):
    try:
        # Convert the id string to an ObjectId
        candidate_id = ObjectId(id)
        candidate = candidate_collection.find_one({"_id": candidate_id})
        if not candidate:
            return Response({"error": "Candidate not found"}, status=404)
    except Exception:
        return Response({"error": "Invalid candidate ID"}, status=400)

    if request.method == "GET":
        candidate = convert_objectid(candidate)
        return Response(candidate)

    elif request.method == "DELETE":
        _id = candidate["_id"]
        result_collection.delete_many({"candidate": _id})
        candidate_collection.delete_one({"_id": _id})
        return Response(status=status.HTTP_204_NO_CONTENT)

    elif request.method == "PUT":
        data = request.data
        required_fields = ["first_name", "last_name", "age", "gender", "email", "phone"]
        if not all(field in data and data[field] for field in required_fields):
            return Response(
                {"error": "All fields (first_name, last_name, age, gender, email, phone) are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        update_data = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "age": data["age"],
            "gender": data["gender"],
            "email": data["email"],
            "phone": data["phone"]
        }
        candidate_collection.update_one({"_id": candidate_id}, {"$set": update_data})
        candidate = candidate_collection.find_one({"_id": candidate_id})
        candidate = convert_objectid(candidate)
        return Response(candidate)


@api_view(["POST"])
def verify_candidate_code(request):
    code = request.data.get("code")
    if not code:
        return Response({
            "status": "error",
            "code": "MISSING_CODE",
            "message": "Code is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    candidate = candidate_collection.find_one({"code": code})
    if candidate:
        candidate = convert_objectid(candidate)
        return Response({
            "status": "success",
            "candidate": candidate
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": "error",
            "code": "INVALID_CODE",
            "message": "Code not found"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def verify_completed_test(request):
    candidate_id = request.data.get("candidate_id")
    if not candidate_id:
        return Response({
            "status": "error",
            "code": "MISSING_CANDIDATE_ID",
            "message": "Candidate ID is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        candidate_obj_id = ObjectId(candidate_id)
    except Exception:
        return Response({
            "status": "error",
            "code": "INVALID_CANDIDATE_ID",
            "message": "Invalid candidate ID"
        }, status=status.HTTP_400_BAD_REQUEST)

    result = result_collection.find_one({"candidate_id": candidate_obj_id})
    if result:
        return Response({
            "status": "exists",
            "message": "Candidate has already submitted a test"
        }, status=status.HTTP_409_CONFLICT)
    else:
        return Response({
            "status": "not_found",
            "message": "No result found for this candidate"
        }, status=status.HTTP_200_OK)
