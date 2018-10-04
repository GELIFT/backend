""" Unit tests for the location REST API (backend) """
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_401_UNAUTHORIZED, \
    HTTP_400_BAD_REQUEST, HTTP_417_EXPECTATION_FAILED

from webapp.models import Location, Event, Team, UserTeam, TeamLocation, Score

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class LocationTests(TestCase):
    password = '123456abc'
    dummy_data = {'latitude': 3, 'longitude': 3}

    # URLs
    login_url = 'api_login'
    logout_url = 'api_logout'
    location_view_url = 'api_my_team_location'
    timer_start_url = '/api/teams/my/start/'
    timer_stop_url = '/api/teams/my/stop/'
    route_url = 'api_my_team_route'

    """
    Database set-up for unit tests
    """

    def setUp(self):
        # Create users
        self.team_user = User.objects.create(
            first_name='Test',
            last_name='User in team',
            is_superuser=False,
            email='user@test.com',
            is_active=True,
            is_staff=True,
            phone='0123456789',
            first_login=False,
            password='pbkdf2_sha256$100000$Wxbl16Sprv4g$h4v5hURFNJY0/cpm/yeA1OKDGrX09O5Kb3Ghap4UJcg='
        )

        self.user = User.objects.create(
            first_name='Test',
            last_name='User',
            is_superuser=False,
            email='user2@test.com',
            is_active=True,
            is_staff=False,
            phone='0123456789',
            first_login=False,
            password='pbkdf2_sha256$100000$Wxbl16Sprv4g$h4v5hURFNJY0/cpm/yeA1OKDGrX09O5Kb3Ghap4UJcg='
        )

        # Create start and end locations
        self.start_location = Location.objects.create(latitude=0, longitude=0)
        self.end_location = Location.objects.create(latitude=1, longitude=1)

        # Create location for team
        self.location = Location.objects.create(latitude=2, longitude=2)

        # Create an event
        self.event = Event.objects.create(
            title='Event',
            start_date=now(),
            end_date=now(),
            start_city='Eindhoven',
            end_city='Amsterdam',
            start_location_id=self.start_location.pk,
            end_location_id=self.end_location.pk,
            winner_photo='',
            is_active=False,
            emergency_contact='0123456789')

        # Create a team
        self.team = Team.objects.create(
            is_disqualified=False,
            is_winner=False,
            timer_started=False,
            event_id=self.event.pk
        )

        # Associate user to team
        self.team_member = UserTeam.objects.create(
            team_id=self.team.pk,
            user_id=self.team_user.pk
        )

        # Create location for team
        self.team_location = TeamLocation.objects.create(
            segment=1,
            datetime=now(),
            location_id=self.location.pk,
            team_id=self.team.pk
        )

    """
    Unit tests for LocationView view
    """

    def test_location_view(self):
        print(separator)
        print("Testing /api/teams/my/location/")
        print(separator)

        """
        POST request, non authenticated (expected HTTP 401)
        """
        print("POST request, non authenticated")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as a user not in a team
        request = client.post(reverse(self.login_url), {"username": self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as a user (expected HTTP 405)
        """
        print("GET request, as a user")
        print(small_separator)
        api_response = client.get(reverse(self.location_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, invalid data (expected HTTP 400)
        """
        print("POST request, invalid data")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, no active event (expected HTTP 404)
        """
        print("POST request, no active event")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url), data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        POST request, active event, user not in a team (expected HTTP 404)
        """
        print("POST request, active event, user not in a team")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url), data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Log in as a user in a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        POST request, timer not started (expected HTTP 417)
        """
        print("POST request, timer not started")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url), data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_417_EXPECTATION_FAILED)
        print("Got HTTP 417")
        print(separator)

        # Mark timer as started
        self.team.timer_started = True
        self.team.save()

        """
        POST request, valid data (expected HTTP 200, valid data)
        """
        print("POST request, valid data")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url), data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        last_location = TeamLocation.objects.latest('datetime')
        location = Location.objects.get(pk=last_location.location_id)

        self.assertEqual(last_location.segment, self.team_location.segment)
        print("Matching segment")
        self.assertEqual(self.dummy_data['latitude'], location.latitude)
        print("Matching latitude")
        self.assertEqual(self.dummy_data['longitude'], location.longitude)
        print("Matching longitude")
        self.assertEqual(self.team.pk, last_location.team_id)
        print("Matching team ID")
        print(separator)

        # Delete known locations
        TeamLocation.objects.all().delete()

        """
        POST request, no last known location (expected HTTP 417)
        """
        print("POST request, no last known location")
        print(small_separator)
        api_response = client.post(reverse(self.location_view_url), data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_417_EXPECTATION_FAILED)
        print("Got HTTP 417")
        print(separator)

    """
    Unit tests for TeamLocationStart view
    """
    def test_team_location_start(self):
        print(separator)
        print("Testing /api/teams/my/start/")
        print(separator)

        """
        POST request, non authenticated (expected HTTP 401)
        """
        print("POST request, non authenticated")
        print(small_separator)
        api_response = client.post(self.timer_start_url)
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as a user not in a team
        request = client.post(reverse(self.login_url), {"username": self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as a user (expected HTTP 405)
        """
        print("GET request, as a user")
        print(small_separator)
        api_response = client.get(self.timer_start_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, invalid data (expected HTTP 400)
        """
        print("POST request, invalid data")
        print(small_separator)
        api_response = client.post(self.timer_start_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, no active event (expected HTTP 404)
        """
        print("POST request, no active event")
        print(small_separator)
        api_response = client.post(self.timer_start_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        POST request, active event, user not in a team (expected HTTP 404)
        """
        print("POST request, active event, user not in a team")
        print(small_separator)
        api_response = client.post(self.timer_start_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Log in as a user in a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        # Remove last known location
        TeamLocation.objects.all().delete()

        """
        POST request, valid data, no last known location (expected HTTP 200, valid data)
        """
        print("POST request, valid data, no last known location")
        print(small_separator)
        api_response = client.post(self.timer_start_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        team = Team.objects.get(pk=self.team.pk)
        team_location = TeamLocation.objects.latest('datetime')
        location = Location.objects.latest('pk')

        self.assertEqual(team.timer_started, True)
        print("Timer started successfully")
        self.assertEqual(team_location.segment, 1)
        print("Segment OK")
        self.assertEqual(team_location.team_id, self.team.pk)
        print("Matching team ID")
        self.assertEqual(team_location.location_id, location.pk)
        print("Matching location ID")
        self.assertEqual(location.latitude, self.dummy_data['latitude'])
        print("Matching latitude")
        self.assertEqual(location.longitude, self.dummy_data['longitude'])
        print("Matching longitude")
        print(separator)

        # Mark timer as not started
        self.team.timer_started = False
        self.team.save()

        """
        POST request, valid data, known last location (expected HTTP 200, valid data)
        """
        print("POST request, valid data, known last location")
        print(small_separator)
        api_response = client.post(self.timer_start_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        team = Team.objects.get(pk=self.team.pk)
        team_location = TeamLocation.objects.latest('datetime')
        location = Location.objects.latest('pk')

        self.assertEqual(team.timer_started, True)
        print("Timer started successfully")
        self.assertEqual(team_location.segment, 2)
        print("Segment OK")
        self.assertEqual(team_location.team_id, self.team.pk)
        print("Matching team ID")
        self.assertEqual(team_location.location_id, location.pk)
        print("Matching location ID")
        self.assertEqual(location.latitude, self.dummy_data['latitude'])
        print("Matching latitude")
        self.assertEqual(location.longitude, self.dummy_data['longitude'])
        print("Matching longitude")
        print(separator)

        """
        POST request, timer already started (expected HTTP 418)
        """
        print("POST request, timer already started")
        print(small_separator)
        api_response = client.post(self.timer_start_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, 418)
        print("Got HTTP 418")
        print(separator)

    """
    Unit tests for TeamLocationStop view
    """
    def test_team_location_stop(self):
        # Add field to dummy data
        self.dummy_data["location_id"] = 99

        print(separator)
        print("Testing /api/my/team/stop/")
        print(separator)

        """
        POST request, unauthenticated (expected HTTP 401)
        """
        print("POST request, unauthenticated")
        print(small_separator)
        api_response = client.post(self.timer_stop_url)
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as user
        request = client.post(reverse(self.login_url), {"username": self.user.email, "password": self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as user (expected HTTP 405)
        """
        print("GET request, as user")
        print(small_separator)
        api_response = client.get(self.timer_stop_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, invalid data (expected HTTP 400)
        """
        print("POST request, invalid data")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, inactive event (expected HTTP 404)
        """
        print("POST request, inactive event")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        POST request, active event, user not in a team (expected HTTP 404)
        """
        print("POST request, active event, user not in a team")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Login as a user that has a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {"username": self.team_user.email, "password": self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        POST request, team timer not started (expected HTTP 418)
        """
        print("POST request, team timer not started")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, 418)
        print("Got HTTP 418")
        print(separator)

        # Mark timer as started
        self.team.timer_started = True
        self.team.save()

        """
        POST request, provided location does not exist (expected HTTP 417)
        """
        print("POST request, provided location does not exist")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_417_EXPECTATION_FAILED)
        print("Got HTTP 418")
        print(separator)

        # Change dummy data
        self.dummy_data["location_id"] = self.location.pk

        """
        POST request, provided location (expected HTTP 200, valid data)
        """
        print("POST request, provided location")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Check against database
        team_location = TeamLocation.objects.latest('datetime')
        location = Location.objects.get(pk=team_location.location_id)
        team = Team.objects.get(pk=self.team.pk)
        self.assertEqual(team_location.segment, self.team_location.segment)
        print("Matching segment")
        self.assertEqual(team_location.location_id, self.dummy_data["location_id"])
        print("Matching location (team location)")
        self.assertEqual(location.pk, self.dummy_data["location_id"])
        print("Matching location (location)")
        self.assertEqual(team_location.team_id, self.team.pk)
        print("Matching team ID (team location)")
        self.assertEqual(location.latitude, self.location.latitude)
        print("Matching latitude")
        self.assertEqual(location.longitude, self.location.longitude)
        print("Matching longitude")
        self.assertEqual(team.timer_started, False)
        print("Successfully stopped timer")

        # Get score
        score = Score.objects.latest("pk")
        self.assertEqual(score.team_id, self.team.pk)
        print("Matching team ID (score)")
        self.assertEqual(score.start_location_id, self.event.start_location_id)
        print("Matching start location")
        self.assertEqual(score.end_location_id, self.location.pk)
        print("Matching end location")
        self.assertGreaterEqual(score.time, timedelta())
        print("Time >=0 (score)")
        print(separator)

        # Change dummy data
        self.dummy_data["location_id"] = -1

        # Mark timer as started
        self.team.timer_started = True
        self.team.save()

        """
        POST request, no provided location (expected HTTP 200, valid data)
        """
        print("POST request, no provided location")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Check against database
        team_location = TeamLocation.objects.latest('pk')
        location = Location.objects.latest('pk')
        team = Team.objects.get(pk=self.team.pk)

        self.assertEqual(team_location.segment, self.team_location.segment)
        print("Matching segment")
        self.assertEqual(team_location.location_id, location.pk)
        print("Matching location")
        self.assertEqual(team_location.team_id, self.team.pk)
        print("Matching team ID")
        self.assertEqual(location.latitude, self.dummy_data['latitude'])
        print("Matching latitude")
        self.assertEqual(location.longitude, self.dummy_data['longitude'])
        print("Matching longitude")
        self.assertEqual(team.timer_started, False)
        print("Successfully stopped timer")
        print(separator)

        # Delete team locations
        TeamLocation.objects.all().delete()
        # Mark timer as started
        self.team.timer_started = True
        self.team.save()

        """
        POST request, timer started, no last known location (expected HTTP 417)
        """
        print("POST request, team timer not started")
        print(small_separator)
        api_response = client.post(self.timer_stop_url, data=self.dummy_data, **headers)
        self.assertEqual(api_response.status_code, HTTP_417_EXPECTATION_FAILED)
        print("Got HTTP 417")
        print(separator)

    """
    Unit tests for TeamRoute view
    """
    def test_team_route(self):
        print(separator)
        print("Testing /api/teams/my/route")
        print(separator)

        """
        GET request, unauthorised (expected HTTP 401)
        """
        print("GET request, unauthorised")
        print(small_separator)
        api_response = client.get(reverse(self.route_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as user
        request = client.post(reverse(self.login_url), {"username": self.user.email, "password": self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        POST request, as user (expected HTTP 405)
        """
        print("POST request, as user")
        print(small_separator)
        api_response = client.post(reverse(self.route_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, no active event (expected HTTP 404)
        """
        print("GET request, no active event")
        print(small_separator)
        api_response = client.get(reverse(self.route_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        GET request, active event, user not in team (expected HTTP 404)
        """
        print("GET request, active event, user not in team")
        print(small_separator)
        api_response = client.get(reverse(self.route_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Login as a user that has a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {"username": self.team_user.email, "password": self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        GET request, valid, existing data (expected HTTP 200)
        """
        print("GET request, valid, existing data")
        print(small_separator)
        api_response = client.get(reverse(self.route_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check return data
        api_response = api_response.data[0]
        self.assertEqual(api_response['segment'], self.team_location.segment)
        print("Matching segment")
        api_response = api_response['locations'][0]
        self.assertEqual(api_response['id'], self.team_location.location_id)
        print("Matching location ID")
        self.assertEqual(api_response['latitude'], self.location.latitude)
        print("Matching latitude")
        self.assertEqual(api_response['longitude'], self.location.longitude)
        print("Matching longitude")
        self.assertEqual(api_response['datetime'], self.team_location.datetime)
        print("Matching datetime")
        print(separator)

        # Remove team locations
        TeamLocation.objects.all().delete()

        """
        GET request, valid, non-existing data (expected HTTP 200)
        """
        print("GET request, valid, non-existing data")
        print(small_separator)
        api_response = client.get(reverse(self.route_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check return data
        assert not api_response.data
        print("Empty list")
        print(separator)
