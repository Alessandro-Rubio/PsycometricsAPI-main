from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.hashers import make_password
from PsycometricsAPI.db.mongo import hr_collection

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Create HR in MongoDB if not exists
        email = user.email
        if not hr_collection.find_one({"email": email}):
            hr_doc = {
                "first_name": "",
                "last_name": "",
                "age": "",
                "gender": "",
                "company": "",
                "email": email,
                "phone": "",
                "password": make_password("sociallogin"),  # Placeholder
            }
            hr_collection.insert_one(hr_doc)
        return user