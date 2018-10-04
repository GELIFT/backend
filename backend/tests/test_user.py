""" Unit tests for the user REST API (backend) """

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_401_UNAUTHORIZED, \
    HTTP_400_BAD_REQUEST

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class TeamsTests(TestCase):
    password = '123456abc'

    # URLs
    login_url = 'api_login'
    logout_url = 'api_logout'
    user_data_url = 'api_user_data'
    user_url = '/api/user/single/'
    user_edit_url = '/api/user/edit/'

    """
    Database set-up for unit tests
    """

    def setUp(self):
        # Create user
        self.user_1 = User.objects.create(
            first_name='Test',
            last_name='User',
            is_superuser=False,
            email='user@test.com',
            is_active=True,
            is_staff=True,
            phone='0123456789',
            first_login=False,
            password='pbkdf2_sha256$100000$Wxbl16Sprv4g$h4v5hURFNJY0/cpm/yeA1OKDGrX09O5Kb3Ghap4UJcg='
        )

        self.user_2 = User.objects.create(
            first_name='Test',
            last_name='User',
            is_superuser=False,
            email='user2@test.com',
            is_active=True,
            is_staff=True,
            phone='0123456789',
            first_login=False,
            password='pbkdf2_sha256$100000$Wxbl16Sprv4g$h4v5hURFNJY0/cpm/yeA1OKDGrX09O5Kb3Ghap4UJcg='
        )

    """
    Unit tests for UserData view
    """

    def test_user_data_view(self):
        print(separator)
        print("Testing /api/user/")
        print(separator)

        """
        GET request, non authenticated (expected HTTP 401)
        """
        print("GET request, non authenticated")
        print(small_separator)
        api_response = client.get(reverse(self.user_data_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in
        request = client.post(reverse(self.login_url), {'username': self.user_1.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        POST request, as user (expected HTTP 405)
        """
        print("POST request, as user")
        print(small_separator)
        api_response = client.post(reverse(self.user_data_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(small_separator)

        """
        GET request, as user (expected HTTP 200, valid data)
        """
        print("GET request, as user")
        print(small_separator)
        api_response = client.get(reverse(self.user_data_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        api_response = api_response.data
        self.assertEqual(api_response['id'], self.user_1.pk)
        print("Matching user ID")
        self.assertEqual(api_response['first_name'], self.user_1.first_name)
        print("Matching first name")
        self.assertEqual(api_response['last_name'], self.user_1.last_name)
        print("Matching last name")
        self.assertEqual(api_response['email'], self.user_1.email)
        print("Matching email")
        self.assertEqual(api_response['phone'], self.user_1.phone)
        print("Matching phone")
        self.assertEqual(api_response['last_login'], self.user_1.last_login)
        print("Matching last login")
        self.assertEqual(api_response['first_login'], self.user_1.first_login)
        print("Matching first login status")
        self.assertEqual(api_response['is_staff'], self.user_1.is_staff)
        print("Matching administrator status")
        self.assertEqual(api_response['is_superuser'], self.user_1.is_superuser)
        print("Matching superuser status")
        print(separator)

    """
    Unit tests for UserView view
    """

    def test_user_view(self):
        print(separator)
        print("Testing /api/user/single/")
        print(separator)

        """
        POST request, unauthenticated (expected HTTP 401)
        """
        print("POST request, unauthenticated")
        print(small_separator)
        api_response = client.post(self.user_url)
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in
        request = client.post(reverse(self.login_url), {'username': self.user_1.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as user (expected HTTP 405)
        """
        print("GET request, as user")
        print(small_separator)
        api_response = client.get(self.user_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, as user, invalid data (expected HTTP 400)
        """
        print("POST request, as user, invalid data")
        print(small_separator)
        api_response = client.post(self.user_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, as user, user ID not in database (expected HTTP 404)
        """
        print("POST request, as user, user ID not in database")
        print(small_separator)
        api_response = client.post(self.user_url, {'id': 99}, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        """
        POST request, as user, valid data (expected HTTP 200, valid data)
        """
        print("POST request, as user, valid data")
        print(small_separator)
        api_response = client.post(self.user_url, {'id': self.user_2.pk}, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        api_response = api_response.data
        self.assertEqual(api_response['id'], self.user_2.pk)
        print("Matching user ID")
        self.assertEqual(api_response['first_name'], self.user_2.first_name)
        print("Matching first name")
        self.assertEqual(api_response['last_name'], self.user_2.last_name)
        print("Matching last name")
        self.assertEqual(api_response['email'], self.user_2.email)
        print("Matching email")
        self.assertEqual(api_response['phone'], self.user_2.phone)
        print("Matching phone")
        print(separator)

    """ 
    Unit tests for UserEdit view
    """

    def test_user_edit_view(self):
        print(separator)
        print("Testing /api/user/edit/")
        print(separator)

        """
        POST request, unauthenticated (expected HTTP 401)
        """
        print("POST request, unauthenticated")
        print(small_separator)
        api_response = client.post(self.user_edit_url)
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in
        request = client.post(reverse(self.login_url), {'username': self.user_1.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as user (expected HTTP 405)
        """
        print("GET request, as user")
        print(small_separator)
        api_response = client.get(self.user_edit_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, as user, no data (expected HTTP 400)
        """
        print("POST request, as user, no data")
        print(small_separator)
        api_response = client.post(self.user_edit_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, missing old password (expected HTTP 400)
        """
        print("POST request, missing old password")
        print(small_separator)
        data = {'new_password': '123456abcd', 'new_password_confirmation': '123456abcd'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, missing new password (expected HTTP 400)
        """
        print("POST request, missing new password")
        print(small_separator)
        data = {'old_password': self.password, 'new_password_confirmation': '123456abcd'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, missing new password confirmation (expected HTTP 400)
        """
        print("POST request, missing new password confirmation")
        print(small_separator)
        data = {'old_password': self.password, 'new_password': '123456abcd'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, wrong old password (expected HTTP 400)
        """
        print("POST request, missing old password")
        print(small_separator)
        data = {'old_password': '1234', 'new_password': '123456abcd', 'new_password_confirmation': '123456abcd'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, new password != new password confirmation (expected HTTP 400)
        """
        print("POST request, new password != new password confirmation")
        print(small_separator)
        data = {'old_password': self.password, 'new_password': '123456abcd', 'new_password_confirmation': '123456abc'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, invalid phone number (too short) (expected HTTP 400)
        """
        print("POST request, invalid phone number (too short)")
        print(small_separator)
        data = {'phone': '000'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, invalid phone number (too long) (expected HTTP 400)
        """
        print("POST request, invalid phone number (too long)")
        print(small_separator)
        data = {'phone': '12345678910111213'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, valid password change (expected HTTP 200, valid data)
        """
        print("POST request, valid password change")
        print(small_separator)
        data = {'old_password': self.password, 'new_password': '123456abcd', 'new_password_confirmation': '123456abcd'}
        api_response = client.post(self.user_edit_url, data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Check password change
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.user_1.email, 'password': '123456abcd'})
        self.assertEqual(request.status_code, HTTP_200_OK)
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token
        print("Password changed successfully")
        print(separator)

        """
        POST request, valid phone number change (expected HTTP 200, valid data)
        """
        print("POST request, valid phone number change")
        print(small_separator)
        api_response = client.post(self.user_edit_url, {'phone': '1234567890'}, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Check against database
        user = User.objects.get(pk=self.user_1.pk)
        self.assertEqual('1234567890', user.phone)
        print("Phone number changed successfully")
        print(separator)
