""" Unit tests for the authentication REST API (backend) """

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
# APIClient
from django.urls import reverse
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_400_BAD_REQUEST

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class AuthenticationTests(TestCase):
    user = None

    password = '123456abc'

    # URLs
    logout_url = 'api_logout'
    login_url = 'api_login'
    password_reset_url = 'api_password_reset'

    def setUp(self):
        # Create user
        self.user = User.objects.create(
            first_name='Test',
            last_name='User',
            is_superuser=False,
            email='user@test.com',
            is_active=True,
            is_staff=False,
            phone='0123456789',
            first_login=False,
            password='pbkdf2_sha256$100000$Wxbl16Sprv4g$h4v5hURFNJY0/cpm/yeA1OKDGrX09O5Kb3Ghap4UJcg='
        )

    """
    Unit tests for view PasswordReset
    """

    def test_password_reset_view(self):
        print(separator)
        print("Testing /api/user/password_reset")
        print(separator)

        """
        GET request (expected HTTP 405)
        """
        print("GET request")
        print(small_separator)
        api_response = client.get(reverse(self.password_reset_url))
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, invalid data (expected HTTP 400)
        """
        print("POST request, invalid data")
        print(small_separator)
        api_response = client.post(reverse(self.password_reset_url))
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, valid data (expected HTTP 200)
        """
        print("POST request, valid data")
        print(small_separator)
        api_response = client.post(reverse(self.password_reset_url), {'email': self.user.email})
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(separator)

    """ 
    Unit tests for view Logout 
    """

    def test_logout_view(self):
        print(separator)
        print("Testing /api/user/logout")
        print(separator)

        """
        POST request (expected HTTP 405)
        """
        print("POST request")
        print(small_separator)
        api_response = client.post(reverse(self.logout_url))
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """ 
        GET request, non authenticated user (expected 400)
        """
        print("GET request, non authenticated user")
        print(small_separator)
        api_response = client.get(reverse(self.logout_url))
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        # Login
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, authenticated user (expected HTTP 200)
        """
        print("GET request, as user")
        print(small_separator)
        api_response = client.get(reverse(self.logout_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(separator)
