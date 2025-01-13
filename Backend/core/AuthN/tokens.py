import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from django.db.models import Q
from .models import SystemOwner, Organization, Admin, Supervisor, Employee

# A mapping of model names to model classes
MODEL_MAPPING = {
    'SystemOwner': SystemOwner,
    'Organization': Organization,
    'Admin': Admin,
    'Supervisor': Supervisor,
    'Employee': Employee,
}

def decode_jwt_token(auth_header, models):
    """
    Decodes a JWT token and returns the user object (based on the provided models).
    Raises AuthenticationFailed if the token is invalid or expired.
    """
    try:
        token = auth_header[7:]  # Remove "Bearer " from the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        # Extract the user_id from the decoded payload
        user_id = payload.get('user_id')
        if not user_id:
            raise AuthenticationFailed("User ID not found in token payload.")

        # Retrieve the model dynamically from the MODEL_MAPPING
        user_models = [MODEL_MAPPING.get(model) for model in models if MODEL_MAPPING.get(model)]
        
        if not user_models:
            raise AuthenticationFailed("No valid models provided.")

        # Using Q objects to optimize the lookup across multiple models
        filters = Q(id=user_id)
        user = None
        
        for user_model in user_models:
            # Find the user from the corresponding models in a single query
            user = user_model.objects.filter(filters).first()
            if user:
                break
        
        if not user:
            raise AuthenticationFailed("User not found or invalid user type.")

        return user

    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired.")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token.")
    except Exception as e:
        raise AuthenticationFailed(f"Error during token decoding: {str(e)}")
