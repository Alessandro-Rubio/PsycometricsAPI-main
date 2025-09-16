from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..serializers import ResultSerializer
from ..db.mongo import result_collection, candidate_collection
from ..utils.objectIdConversion import convert_objectid
from datetime import datetime
import pytz
import requests

@api_view(["GET", "POST"])
def result_list(request):
    if request.method == "GET":
        # Extract hr_id from JWT (SimpleJWT puts it in request.user or request.auth['hr'])
        hr_id = None
        if hasattr(request, 'auth') and request.auth and 'hr' in request.auth:
            hr_id = request.auth['hr']
        elif hasattr(request.user, 'id'):
            hr_id = str(request.user.id)
        if not hr_id:
            return Response({"error": "HR id not found in token"}, status=401)

        results = list(result_collection.find({"hr": ObjectId(hr_id)}))
        results = [convert_objectid(r) for r in results]
        return Response(results)

    elif request.method == "POST":
        serializer = ResultSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data

            # Check if candidate_id already exists in the results
            existing = result_collection.find_one({
                "candidate_id": ObjectId(validated["candidate_id"])
            })
            if existing:
                return Response(
                    {"error": "Candidate has already submitted a test"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch the candidate's email from the database
            candidate = candidate_collection.find_one({"_id": ObjectId(validated["candidate_id"])})
            if not candidate:
                return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

            candidate_email = candidate.get("email", "")

            completed_at = datetime.now(pytz.UTC)

            result_doc = {
                "test_id": ObjectId(validated["test_id"]),
                "candidate_id": ObjectId(validated["candidate_id"]),
                "hr_id": ObjectId(validated["hr_id"]),
                "completed_at": completed_at,
                "responses": validated["responses"],
            }

            # Insert the result into the database
            result = result_collection.insert_one(result_doc)

            # Trigger the webhook
            webhook_url = "https://roberto-pruebas.app.n8n.cloud/webhook/test-completed"
            webhook_payload = {
                "result_id": str(result.inserted_id),
                "test_id": str(result_doc["test_id"]),
                "candidate_id": str(result_doc["candidate_id"]),
                "candidate_email": candidate_email,
                "hr_id": str(result_doc["hr_id"]),
                "completed_at": completed_at.isoformat(),
                "responses": validated["responses"]
            }
            try:
                webhook_response = requests.post(webhook_url, json=webhook_payload, timeout=60)
                if webhook_response.status_code != 200:
                    print(f"Webhook failed with status code {webhook_response.status_code}: {webhook_response.text}")
            except Exception as e:
                print(f"Failed to send webhook: {str(e)}")

            return Response({"result_id": str(result.inserted_id)}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "DELETE"])
def result_detail(request, id):
    try:
        _id = ObjectId(id)
        result = result_collection.find_one({"_id": _id})
        if not result:
            return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "GET":
            result = convert_objectid(result)
            return Response(result)

        elif request.method == "DELETE":
            result_collection.delete_one({"_id": _id})
            return Response(status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
