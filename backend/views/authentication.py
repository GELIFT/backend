from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from GELIFT import settings
from backend.serializers import PasswordResetSerializer

User = get_user_model()


class PasswordReset(APIView):
    """
    API endpoint allowing a user to request an email to reset his password
    Links to reset passwords are of the form user/reset/<uidb64>/<token>/
    Where uidb64 is a base64 encoded string based on user ID and token
    is a randomly generated string\n
    Allowed methods: POST\n
    Fields:\n
        - email: email of the account the password reset is asked for
    Possible HTTP responses:\n
        - HTTP 200: When the request is valid and the email is in the database
        - HTTP 400: When the POST data is invalid
        - HTTP 405: On GET/PUT/DELETE request
    :return: Nothing
    """

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.data.get("email")
            check = User.objects.filter(email=email)

            # If the email is in the database
            if check:
                # Retrieve user from database
                user = User.objects.get(email=email)
                # Generate a token using django's integrated functions
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)

                # Generate base64 encoded string based on user's private key (user ID)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Send email containing link to reset password
                subject = 'Password reset'
                message = 'You are receiving this email because you requested a password reset on lifTUe.\n\n' \
                          'Please go to the following page and choose a new password:\n\n' \
                          + settings.URL + 'user/password/reset/' + uid.decode() + '/' + token + '\n\n' \
                                                                                                 'Thanks!\n\nlifTUe'

                send_mail(subject, message, 'noreply@gelift.win.tue.nl', (user.email,))
                return Response(status=HTTP_200_OK)

        # If the request is invalid
        else:
            return Response(status=HTTP_400_BAD_REQUEST)


class Logout(APIView):
    """
    API endpoint allowing a user to log out\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: If not authenticated
        - HTTP 405: On POST/PUT/DELETE requests
    :return: Nothing
    """
    permissions_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        token = self.request.auth
        check = Token.objects.filter(key=token)
        if check:
            Token.objects.filter(key=token).delete()
            return Response(status=HTTP_200_OK)
        else:
            return Response(status=HTTP_400_BAD_REQUEST)
