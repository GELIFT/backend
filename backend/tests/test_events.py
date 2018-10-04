""" Unit tests for the events REST API (backend) """

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
# APIClient
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_401_UNAUTHORIZED, \
    HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from webapp.models import Location, Event, SubLocation

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class EventTests(TestCase):
    admin = None
    user = None
    event = None
    sub_dest_1 = None
    sub_dest_2 = None
    sub_loc_1 = None
    sub_loc_2 = None
    start_location = None
    end_location = None

    password = '123456abc'

    # URLs
    login_url = 'api_login'
    logout_url = 'api_logout'
    active_event_view_url = 'api_active_event'
    emergency_contact_url = 'api_edit_emergency_contact'

    """
    Database set-up for unit tests
    """

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
        # Create administrator
        self.admin = User.objects.create(
            first_name='Test',
            last_name='Admin',
            is_superuser=False,
            email='admin@test.com',
            is_active=True,
            is_staff=True,
            phone='0123456789',
            first_login=False,
            password='pbkdf2_sha256$100000$Wxbl16Sprv4g$h4v5hURFNJY0/cpm/yeA1OKDGrX09O5Kb3Ghap4UJcg='
        )

        # Create start, end and two other locations
        self.start_location = Location.objects.create(latitude=0, longitude=0)
        self.end_location = Location.objects.create(latitude=1, longitude=1)
        self.sub_loc_1 = Location.objects.create(latitude=2, longitude=2)
        self.sub_loc_2 = Location.objects.create(latitude=3, longitude=3)

        # Create an event
        self.event = Event.objects.create(
            title='active event',
            start_date=now(),
            end_date=now(),
            start_city='Eindhoven',
            end_city='Amsterdam',
            start_location_id=self.start_location.pk,
            end_location_id=self.end_location.pk,
            winner_photo='',
            is_active=False,
            emergency_contact='0123456789')

        # Create two sub-destinations
        self.sub_dest_1 = SubLocation.objects.create(
            event_id=self.event.pk,
            location_id=self.sub_loc_1.pk,
            city='Den Bosch',
            order=1)

        self.sub_dest_2 = SubLocation.objects.create(
            event_id=self.event.pk,
            location_id=self.sub_loc_2.pk,
            city='Utrecht',
            order=2)

    """ 
    Unit tests for view ActiveEventView 
    """

    def test_active_event_view(self):
        print(separator)
        print("Testing /api/events/active/")
        print(separator)

        """
        POST request (expected HTTP 405)
        """
        print("Trying a POST request")
        print(small_separator)
        api_response = client.post(reverse(self.active_event_view_url))
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, no active event (expected HTTP 404)
        """
        print("GET request (no active event)")
        print(small_separator)
        # GET API response
        api_response = client.get(reverse(self.active_event_view_url))
        # Check response code (should be 404 as there is no active event)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        GET request, active event (expected HTTP 200 and API response matching database contents)
        """
        print("GET request with an active event")
        print(small_separator)

        # Get API response
        api_response = client.get(reverse(self.active_event_view_url))
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Validate against database entry
        self.assertEqual(self.event.pk, api_response.data['id'])
        print("Event ID matching")
        self.assertEqual(self.event.title, api_response.data['title'])
        print("Title matching")
        self.assertEqual(self.event.start_date, api_response.data['start_date'])
        print("Matching start date")
        self.assertEqual(self.event.end_date, api_response.data['end_date'])
        print("Matching end date")
        self.assertEqual(self.event.emergency_contact, api_response.data['emergency_contact'])
        print("Matching emergency contact")

        # Create sub-destinations list
        dest_1 = dict(order=self.sub_dest_1.order, name=self.sub_dest_1.city, id=self.sub_loc_1.pk,
                      latitude=self.sub_loc_1.latitude, longitude=self.sub_loc_1.longitude)

        dest_2 = dict(order=self.sub_dest_2.order, name=self.sub_dest_2.city, id=self.sub_loc_2.pk,
                      latitude=self.sub_loc_2.latitude, longitude=self.sub_loc_2.longitude)

        sub_destinations = [dest_1, dest_2]

        self.assertEqual(sub_destinations, api_response.data['sub_destinations'])
        print("Matching sub-destinations")

        # Start location
        start_location = dict(name=self.event.start_city, id=self.start_location.pk,
                              latitude=self.start_location.latitude, longitude=self.start_location.longitude)
        self.assertEqual(start_location, api_response.data['start_location'])
        print("Start location matching")

        # End location
        end_location = dict(name=self.event.end_city, id=self.end_location.pk,
                            latitude=self.end_location.latitude, longitude=self.end_location.longitude)
        self.assertEqual(end_location, api_response.data['end_location'])
        print("End location matching")
        print(separator)

    """ 
    Unit tests for view EmergencyContactView 
    """

    def test_emergency_contact_view(self):
        print(separator)
        print("Testing /api/event/emergency")
        print(separator)

        """ 
        GET request, no login (expected HTTP 401)
        """
        print("Test request without login")
        print(small_separator)
        api_response = client.get(reverse(self.emergency_contact_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Login as user
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """ 
        GET request, logged in as user (expected HTTP 405)
        """
        print("Test GET request")
        print(small_separator)
        api_response = client.get(reverse(self.emergency_contact_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """ 
        POST request, as user (expected HTTP 403)
        """
        print("Test unauthorized user")
        print(small_separator)
        api_response = client.post(reverse(self.emergency_contact_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_403_FORBIDDEN)
        print("Got HTTP 403")
        print(separator)

        # Login as admin
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.admin.email, 'password': self.password})
        token = request.data["token"]
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """ 
        POST request, as admin, no active event (expected HTTP 404)
        """
        print("Test request with no active event")
        print(small_separator)
        api_response = client.post(reverse(self.emergency_contact_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event active
        self.event.is_active = True
        self.event.save()

        """ 
        POST request, as admin, active event, no data (expected HTTP 400)
        """
        print("Test POST request with no data")
        print(small_separator)
        api_response = client.post(reverse(self.emergency_contact_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """ 
        POST request, as admin, active event, valid data (expected HTTP 200 and saved data)
        """
        print("Test POST request with valid data")
        print(small_separator)

        emergency_contact = '123456789'

        api_response = client.post(reverse(self.emergency_contact_url), {'emergency_contact': emergency_contact},
                                   **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check if the new emergency contact was saved correctly
        event = Event.objects.get(is_active=True)
        self.assertEqual(event.emergency_contact, emergency_contact)
        print("Matching emergency contact")
        print(separator)
