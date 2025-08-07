from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId
from ..db.mongo import hr_collection, candidate_collection, result_collection
from ..serializers import HRSerializer
from ..utils.objectIdConversion import convert_objectid
from rest_framework_simplejwt.authentication import JWTAuthentication
import random
import string
import requests


@api_view(["GET", "POST"])
def hr_list(request):
    if request.method == "GET":
        hrs = list(hr_collection.find())
        hrs = [convert_objectid(c) for c in hrs]
        return Response(hrs)

    elif request.method == "POST":
        serializer = HRSerializer(data=request.data)
        if serializer.is_valid():
            hr_collection.insert_one(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def hr_detail(request, id):
    try:
        _id = ObjectId(id)
    except:
        return Response({"error": "Invalid HR ID"}, status=status.HTTP_400_BAD_REQUEST)

    hr = hr_collection.find_one({"_id": _id})
    if not hr:
        return Response({"error": "HR not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        hr["id"] = str(hr["_id"])
        del hr["_id"]
        return Response(hr)

    if request.method == "PUT":
        serializer = HRSerializer(data=request.data)
        if serializer.is_valid():
            update_data = serializer.validated_data
            hr_collection.update_one({"_id": _id}, {"$set": update_data})
            return Response({"message": "HR updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        try:
            _id = ObjectId(id)
            hr = hr_collection.find_one({"_id": _id})
            if not hr:
                return Response({"error": "HR not found"}, status=404)
        except:
            return Response({"error": "Invalid ID"}, status=400)

        # Delete related candidates
        candidate_collection.delete_many({"hr": _id})

        # Delete related results
        result_collection.delete_many({"hr": _id})

        # Finally delete the HR
        hr_collection.delete_one({"_id": _id})

        return Response(status=204)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hr_candidates(request):
    try:
        # Extract HR ID from the authenticated user
        hr_id = request.user.user_id
        if not hr_id:
            return Response({"error": "HR ID not found in token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Convert HR ID to ObjectId
        hr_object_id = ObjectId(hr_id)
    except Exception:
        return Response({"error": "Invalid HR ID in token"}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch all candidates associated with the HR
    candidates = list(candidate_collection.find({"hr": hr_object_id}))
    if not candidates:
        return Response({"message": "No candidates found"}, status=status.HTTP_404_NOT_FOUND)

    # Convert ObjectId fields to strings
    candidates = [convert_objectid(candidate) for candidate in candidates]

    return Response(candidates, status=status.HTTP_200_OK)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def candidate_evaluation(request, id):  # Change user_id to id
    try:
        # Convert the id string to an ObjectId
        candidate_id = ObjectId(id)
    except Exception:
        return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch the candidate by ID
    candidate = candidate_collection.find_one({"_id": candidate_id})
    if not candidate:
        return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

    # Validate the candidate_evaluation field
    candidate_evaluation = request.data.get("candidate_evaluation")
    if candidate_evaluation not in ["pending", "approved", "rejected"]:
        return Response(
            {"error": "Invalid candidate_evaluation value. Must be 'pending', 'approved', or 'rejected'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update the candidate_evaluation field in the database
    candidate_collection.update_one(
        {"_id": candidate_id},
        {"$set": {"candidate_evaluation": candidate_evaluation}}
    )

    # Trigger the webhook
    webhook_url = "https://roberto-pruebas.app.n8n.cloud/webhook/candidate-evaluation"
    webhook_payload = {
        "first_name": candidate.get("first_name"),
        "last_name": candidate.get("last_name"),
        "email": candidate.get("email"),
        "candidate_evaluation": candidate_evaluation
    }
    try:
        webhook_response = requests.post(webhook_url, json=webhook_payload, timeout=5)
        if webhook_response.status_code != 200:
            print(f"Webhook failed with status code {webhook_response.status_code}: {webhook_response.text}")
    except Exception as e:
        print(f"Failed to send webhook: {str(e)}")

    return Response({"message": "Candidate evaluation updated successfully"}, status=status.HTTP_200_OK)
