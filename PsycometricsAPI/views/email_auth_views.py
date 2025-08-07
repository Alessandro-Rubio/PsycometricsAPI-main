from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..db.mongo import hr_collection
import bcrypt

@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    data = request.data

    # Validate required fields
    required_fields = ["email", "password", "confirmPassword"]
    for field in required_fields:
        if field not in data or not data[field]:
            return Response({
                "status": "error",
                "code": "MISSING_FIELD",
                "message": f"{field} is required"
            }, status=status.HTTP_400_BAD_REQUEST)

    # Validate email format
    try:
        validate_email(data['email'])
    except ValidationError:
        return Response({
            "status": "error",
            "code": "INVALID_EMAIL",
            "message": "Invalid email address"
        }, status=status.HTTP_400_BAD_REQUEST)

    if hr_collection.find_one({"email": data['email']}):
        return Response({
            "status": "error",
            "code": "EMAIL_EXISTS",
            "message": "Email already registered"
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(data['password']) < 8 or len(data['confirmPassword']) < 8:
        return Response({
            "status": "error",
            "code": "PASSWORD_TOO_SHORT",
            "message": "Password must be at least 8 characters long"
        }, status=status.HTTP_400_BAD_REQUEST)

    if data['password'] != data['confirmPassword']:
        return Response({
            "status": "error",
            "code": "PASSWORDS_DONT_MATCH",
            "message": "Passwords do not match"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Hash password with bcrypt
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create HR in MongoDB
    hr_doc = {
        "first_name": "",
        "last_name": "",
        "age": "",
        "gender": "",
        "company": "",
        "email": data["email"],
        "phone": "",
        "password": hashed_pw,
    }

    inserted_hr = hr_collection.insert_one(hr_doc)
    hr_id = str(inserted_hr.inserted_id)

    # Generate JWT tokens manually
    refresh = RefreshToken()
    refresh["user_id"] = hr_id  # Set the user_id claim to the HR's MongoDB _id
    access = refresh.access_token

    return Response({
        "status": "success",
        "data": {
            "refresh": str(refresh),
            "access": str(access),
        }
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({
            "status": "error",
            "code": "MISSING_CREDENTIALS",
            "message": "Email and password are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Fetch HR in MongoDB
    hr = hr_collection.find_one({"email": email})
    if not hr or not bcrypt.checkpw(password.encode('utf-8'), hr["password"].encode('utf-8')):
        return Response({
            "status": "error",
            "code": "INVALID_CREDENTIALS",
            "message": "The email or password you entered is incorrect"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Generate JWT tokens manually
    refresh = RefreshToken()
    refresh["user_id"] = str(hr["_id"])  # Set the user_id claim to the HR's MongoDB _id
    access = refresh.access_token

    return Response({
        "status": "success",
        "data": {
            "refresh": str(refresh),
            "access": str(access),
        }
    }, status=status.HTTP_200_OK)
