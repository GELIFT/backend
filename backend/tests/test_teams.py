""" Unit tests for the teams REST API (backend) """

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_401_UNAUTHORIZED

from webapp.models import Location, Event, Team, UserTeam, TeamLocation

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class TeamsTests(TestCase):
    password = '123456abc'

    # URLs
    login_url = 'api_login'
    teams_url = 'api_teams'
    my_team_url = 'api_my_team'

    """
    Database set-up for unit tests
    """

    def setUp(self):
        # Create users
        self.user_1 = User.objects.create(
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

        self.user_2 = User.objects.create(
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

        # Create team location
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

        # Create teams
        self.team_1 = Team.objects.create(
            is_disqualified=False,
            is_winner=False,
            timer_started=False,
            event_id=self.event.pk
        )

        self.team_2 = Team.objects.create(
            is_disqualified=False,
            is_winner=False,
            timer_started=False,
            event_id=self.event.pk
        )

        # Associate users to teams
        self.team_member_1 = UserTeam.objects.create(
            team_id=self.team_1.pk,
            user_id=self.user_1.pk
        )
        self.team_member_2 = UserTeam.objects.create(
            team_id=self.team_2.pk,
            user_id=self.user_2.pk
        )

        # Create a TeamLocation object
        self.team_location = TeamLocation.objects.create(
            segment=1,
            datetime=now(),
            location_id=self.location.pk,
            team_id=self.team_2.pk
        )

    """
    Unit tests for TeamView view
    """

    def test_team_view(self):
        print(separator)
        print("Testing /api/teams/")
        print(separator)

        """
        GET request, unauthenticated (expected HTTP 401)        
        """
        print("GET request, unauthenticated")
        print(small_separator)
        api_response = client.get(reverse(self.teams_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as user
        request = client.post(reverse(self.login_url), {'username': self.user_1.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        POST request, as user (expected HTTP 405)
        """
        print("POST request, as user")
        print(small_separator)
        api_response = client.post(reverse(self.teams_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, no active event (expected HTTP 404)
        """
        print("GET request, no active event")
        print(small_separator)
        api_response = client.get(reverse(self.teams_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        GET request, active event with teams (expected HTTP 200, valid data)
        """
        print("GET request, active event with teams")
        print(small_separator)
        api_response = client.get(reverse(self.teams_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        # Check against database
        team_1 = api_response.data[0]
        team_2 = api_response.data[1]

        # Check team 1
        self.assertEqual(team_1['id'], self.team_1.pk)
        print("Team 1 - Matching team ID")
        self.assertEqual(team_1['is_disqualified'], self.team_1.is_disqualified)
        print("Team 1 - Matching disqualification status")
        self.assertEqual(team_1['is_winner'], self.team_1.is_winner)
        print("Team 1 - Matching winner status")
        self.assertEqual(team_1['last_location'], {})
        print("Team 1 - Matching empty last location")
        team_1 = team_1['members'][0]
        self.assertEqual(team_1['id'], self.user_1.pk)
        print("Team 1 - Matching member user ID")
        self.assertEqual(team_1['first_name'], self.user_1.first_name)
        print("Team 1 - Matching member first name")
        self.assertEqual(team_1['last_name'], self.user_1.last_name)
        print("Team 1 - Matching member last name")

        # Check team 2
        self.assertEqual(team_2['id'], self.team_2.pk)
        print("Team 2 - Matching team ID")
        self.assertEqual(team_2['is_disqualified'], self.team_2.is_disqualified)
        print("Team 2 - Matching disqualification status")
        self.assertEqual(team_2['is_winner'], self.team_2.is_winner)
        print("Team 2 - Matching winner status")
        last_location = team_2['last_location']
        self.assertEqual(last_location['latitude'], self.location.latitude)
        print("Team 2 - Matching last location latitude")
        self.assertEqual(last_location['longitude'], self.location.longitude)
        print("Team 2 - Matching last location longitude")
        self.assertEqual(last_location['datetime'], self.team_location.datetime)
        print("Team 2 - Matching last location datetime")
        team_2 = team_2['members'][0]
        self.assertEqual(team_2['id'], self.user_2.pk)
        print("Team 2 - Matching member user ID")
        self.assertEqual(team_2['first_name'], self.user_2.first_name)
        print("Team 2 - Matching member first name")
        self.assertEqual(team_2['last_name'], self.user_2.last_name)
        print("Team 2 - Matching member last name")
        print(separator)

        # Remove teams
        UserTeam.objects.all().delete()
        Team.objects.all().delete()
        """
        GET request, active event, no teams (expected HTTP 404)
        """
        print("GET request, active event, no teams")
        print(small_separator)
        api_response = client.get(reverse(self.teams_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

    """
    Unit tests for MyTeamView view
    """

    def test_my_team_view(self):
        print(separator)
        print("Testing /api/teams/my")
        print(separator)

        """
        GET request, non authenticated (expected HTTP 401)
        """
        print("GET request, non authenticated")
        print(small_separator)
        api_response = client.get(reverse(self.my_team_url))
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
        api_response = client.post(reverse(self.my_team_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, no active event (expected HTTP 404)
        """
        print("GET request, no active event")
        print(small_separator)
        api_response = client.get(reverse(self.my_team_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        # Move user 2 to team 1
        self.team_member_2.team_id = self.team_1.pk
        self.team_member_2.save()

        """
        GET request, active event, user in a team (expected HTTP 200, valid data)
        """
        print("GET request, active event, user in a team")
        print(small_separator)
        api_response = client.get(reverse(self.my_team_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        api_response = api_response.data
        self.assertEqual(api_response['id'], self.team_1.pk)
        print("Matching team ID")
        self.assertEqual(api_response['is_disqualified'], self.team_1.is_disqualified)
        print("Matching disqualification status")
        self.assertEqual(api_response['is_winner'], self.team_1.is_winner)
        print("Matching winner status")
        self.assertEqual(api_response['timer_started'], self.team_1.timer_started)
        print("Matching timer status")
        member_1 = api_response['members'][0]
        member_2 = api_response['members'][1]
        # Check member 1
        self.assertEqual(member_1['id'], self.user_1.pk)
        print("Member 1 - Matching user ID")
        self.assertEqual(member_1['first_name'], self.user_1.first_name)
        print("Member 1 - Matching first name")
        self.assertEqual(member_1['last_name'], self.user_1.last_name)
        print("Member 1 - Matching last name")
        self.assertEqual(member_1['email'], self.user_1.email)
        print("Member 1 - Matching email")
        self.assertEqual(member_1['phone'], self.user_1.phone)
        print("Member 1 - Matching phone")

        # Check member 2
        self.assertEqual(member_2['id'], self.user_2.pk)
        print("Member 2 - Matching user ID")
        self.assertEqual(member_2['first_name'], self.user_2.first_name)
        print("Member 2 - Matching first name")
        self.assertEqual(member_2['last_name'], self.user_2.last_name)
        print("Member 2 - Matching last name")
        self.assertEqual(member_2['email'], self.user_2.email)
        print("Member 2 - Matching email")
        self.assertEqual(member_2['phone'], self.user_2.phone)
        print("Member 2 - Matching phone")

        print(separator)

        # Remove user from team
        self.team_member_1.delete()

        """
        GET request, active event, user not in a team (expected HTTP 404)
        """
        print("GET request, active event, user not in a team")
        print(small_separator)
        api_response = client.get(reverse(self.my_team_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)
