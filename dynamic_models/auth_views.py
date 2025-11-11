from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate

class CustomAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
        })

class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out'})
        except (AttributeError, Token.DoesNotExist):
            return Response({'message': 'Already logged out'})