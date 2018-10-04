from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from backend.serializers import UserSerializer, UserEditSerializer, UserSingleSerializer, PublicUserSerializer

User = get_user_model()


class UserData(APIView):
    """
    API endpoint allowing a user to get their data\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: When not authenticated
        - HTTP 405: On POST/PUT/DELETE requests
    :return:\n
        - id: user ID
        - first_name: user first name
        - last_name: user last name
        - email: user email
        - phone: user phone number
        - last_login: date and time of last login
        - first_login: whether this user logged in before
        - is_staff: whether this user is an administrator
        - is_superuser: whether this user is the superuser
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Return user data
        user = self.request.user
        user = User.objects.get(pk=user.id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)


class UserView(viewsets.ModelViewSet):
    """
    API endpoint allowing to get a user\n
    Allowed methods: POST\n
    Fields:\n
        - id: ID of requested user
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: When POST data is invalid
        - HTTP 401: When not authenticated
        - HTTP 404: When the requested user is not in the database
        - HTTP 405: On GET/PUT/DELETE requests
    :return:\n
        - id: requested user ID
        - first_name: requested user first name
        - last_name: requested user last name
        - email: requested user email
        - phone: requested user phone
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserSingleSerializer
    http_method_names = "post"

    def create(self, request, *args, **kwargs):

        # Get the POSTed data
        serializer = UserSingleSerializer(data=request.data)

        # If the data is valid
        if serializer.is_valid():

            # Get the requested user ID
            u_id = serializer.data.get("id")
            user = User.objects.filter(pk=u_id)

            # If the user exists
            if user:
                # Get user data and return it
                user = User.objects.get(pk=u_id)
                serializer = PublicUserSerializer(user)
                return Response(serializer.data)
            else:
                # No user found with this ID, return 404
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            # Data provided not valid, return 400
            return Response(status=HTTP_400_BAD_REQUEST)


class UserEdit(viewsets.ModelViewSet):
    """
    API endpoint allowing a user to change their data (password/phone number, notification preferences)\n
    Allowed methods: POST\n
    Fields: NOTE: old_password, new_password and new_password_confirmation must all be filled when changing password\n
        - old_password: user's old password (not required)
        - new_password: user's new password (not required)
        - new_password_confirmation: user's new password confirmation (not required)
        - phone: user's phone number (not required unless phone number is to be changed)
    Possible HTTP responses:\n
        - HTTP 200 on correct change
        - HTTP 400 if:
            - passwords are different
            - old password is wrong
            - phone number is invalid
            - new password or new password confirmation is missing (when changing password)
        - HTTP 401: When unauthenticated
        - HTTP 405: On GET/PUT/DELETE requests
    :return: Nothing
    """

    serializer_class = UserEditSerializer
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        serializer = UserEditSerializer(data=request.data)

        # If input is valid
        if serializer.is_valid():
            user = User.objects.get(pk=user.id)

            # Get data (may be blank)
            phone = serializer.data.get("phone")
            old_password = serializer.data.get("old_password")
            new_password = serializer.data.get("new_password")
            new_password_confirmation = serializer.data.get("new_password_confirmation")

            # Handle phone number change
            if phone:
                user.phone = phone
                user.save()
                return Response(status=HTTP_200_OK)

            # Handle password change
            elif old_password:
                # Check if new password and new password confirmation have been supplied
                if new_password and new_password_confirmation:
                    # Check if old password is valid
                    if user.check_password(old_password):
                        if new_password == new_password_confirmation:
                            user.set_password(new_password)
                            first_login = serializer.data.get("first_login")
                            if first_login:
                                user.first_login = False
                            user.save()
                            return Response(status=HTTP_200_OK)
                        else:
                            # Different passwords
                            return Response(status=HTTP_400_BAD_REQUEST)
                    else:
                        # Old password not valid
                        return Response(status=HTTP_400_BAD_REQUEST)
                else:
                    # Missing information
                    return Response(status=HTTP_400_BAD_REQUEST)
            # No input provided
            else:
                return Response(status=HTTP_400_BAD_REQUEST)
        else:
            # Phone number invalid
            return Response(status=HTTP_400_BAD_REQUEST)

    http_method_names = ("post",)
