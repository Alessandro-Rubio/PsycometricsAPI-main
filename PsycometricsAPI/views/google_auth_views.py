from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from ..db.mongo import hr_collection
import requests

@api_view(["POST"])
@permission_classes([AllowAny])
def google_auth(request):
    id_token = request.data.get('id_token')
    email = request.data.get('email')

    if not id_token or not email:
        return Response({
            "status": "error",
            "code": "MISSING_FIELDS",
            "message": "id_token, email are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify the id_token with Google
    verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    try:
        verify_response = requests.get(verify_url)
        verify_response.raise_for_status()
        token_info = verify_response.json()
        if token_info.get('email') != email:
            return Response({
                "status": "error",
                "code": "EMAIL_MISMATCH",
                "message": "Email does not match token"
            }, status=status.HTTP_400_BAD_REQUEST)
    except requests.exceptions.RequestException:
        return Response({
            "status": "error",
            "code": "INVALID_ID_TOKEN",
            "message": "Invalid Google ID token"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Get or create HR in MongoDB
    hr = hr_collection.find_one({"email": email})
    if not hr:
        hr_doc = {
            "first_name": '',
            "last_name": '',
            "email": email,
        }
        inserted_hr = hr_collection.insert_one(hr_doc)
        hr_id = str(inserted_hr.inserted_id)
    else:
        hr_id = str(hr["_id"])

    # Generate JWT containing MongoDB HR ID as user_id
    refresh = RefreshToken()
    refresh["user_id"] = str(hr_id)  # Use HR's MongoDB _id as user_id

    return Response({
        "status": "success",
        "data": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)