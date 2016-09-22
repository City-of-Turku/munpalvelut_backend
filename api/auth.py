from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

from api.models import ApiKey, AuthToken

class TokenAndKeyAuthentication(TokenAuthentication):
    """A custom token authetication backend that checks the an API key as well.
    
    Additionally, the the user account must be active and verified.
    """
    
    model = AuthToken
    
    def authenticate(self, request):
        apikey = request.META.get('X_API_KEY', '')
        
        # Currently we accept requests without API keys, but
        # if an API key is specified, it must be correct
        if apikey and not ApiKey.objects.filter(key=apikey, active=True).exists():
            raise exceptions.AuthenticationFailed('Invalid API key')
        
        auth = super(TokenAndKeyAuthentication, self).authenticate(request)
        if auth is None:
            return None
        
        if not auth[0].is_verified:
            raise exceptions.AuthenticationFailed('Email address is not yet verified!')

        if not auth[0].is_active:
            raise exceptions.AuthenticationFailed('User account is inactive!')
        
        return auth
