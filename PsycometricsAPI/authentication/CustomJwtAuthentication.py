from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from bson import ObjectId
from PsycometricsAPI.authentication.CustomUser import CustomUser

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # Extract the user_id from the token
        user_id = validated_token.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Token contained no recognizable user identification")

        # Return a CustomUser object
        return CustomUser(user_id=ObjectId(user_id))