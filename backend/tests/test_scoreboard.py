""" Unit tests for the scoreboard REST API (backend) """
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_401_UNAUTHORIZED

from webapp.models import Location, Event, Team, UserTeam, Challenge, TeamChallenge, SubLocation, TeamLocation, Score

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class ScoreboardTests(TestCase):
    # Create a temporary folder to hold submission images
    folder = tempfile.mkdtemp()

    # Create a new image for testing
    image = Image.new(mode='RGB', size=(200, 200))
    image_io = BytesIO()
    image.save(image_io, 'JPEG')
    image_io.seek(0)
    image = InMemoryUploadedFile(image_io, None, 'image.jpg', 'image/jpeg', image_io, None)

    password = '123456abc'

    challenge_status = {
        'ur': 'under_review',
        'a': 'accepted',
        'o': 'open'
    }

    # URLs
    login_url = 'api_login'
    logout_url = 'api_logout'
    scoreboard_url = 'api_scoreboard'

    """
    Database set-up for unit tests
    """

    def setUp(self):
        # Set MEDIA_ROOT as temp folder
        settings.MEDIA_ROOT = self.folder
        # Create users
        self.user = User.objects.create(
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

        # Create start, end and sub-destination locations
        self.start_location = Location.objects.create(latitude=0, longitude=0)
        self.end_location = Location.objects.create(latitude=1, longitude=1)
        self.subdest_location = Location.objects.create(latitude=2, longitude=2)

        # Create locations for challenges
        self.challenge_location_1 = Location.objects.create(latitude=3, longitude=3)

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

        # Create a sub-destination
        self.sub_dest = SubLocation.objects.create(
            event_id=self.event.pk,
            location_id=self.subdest_location.pk,
            city="Utrecht",
            order=1,
        )

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
            user_id=self.user.pk
        )

        # Create challenges
        self.challenge_1 = Challenge.objects.create(
            title='Challenge 1',
            description='Description',
            reward='00:15',
            event_id=self.event.pk
        )

        # Create a submission
        self.submission = TeamChallenge.objects.create(
            challenge_id=self.challenge_1.pk,
            team_id=self.team.pk,
            is_accepted=False,
            location_id=self.challenge_location_1.pk,
            picture=self.image
        )
        # Create team locations
        self.team_location_start = TeamLocation.objects.create(
            segment=1,
            datetime=now(),
            location_id=self.event.start_location_id,
            team_id=self.team.pk
        )
        self.team_location_subdest_stop = TeamLocation.objects.create(
            segment=1,
            datetime=now() + timedelta(minutes=30),
            location_id=self.subdest_location.pk,
            team_id=self.team.pk
        )
        self.team_location_subdest_start = TeamLocation.objects.create(
            segment=2,
            datetime=(now() + timedelta(hours=1)),
            location_id=self.subdest_location.pk,
            team_id=self.team.pk
        )
        self.team_location_end = TeamLocation.objects.create(
            segment=2,
            datetime=(now() + timedelta(hours=2)),
            location_id=self.event.end_location_id,
            team_id=self.team.pk
        )

        # Create score
        self.score_start_subdest = Score.objects.create(
            time=self.team_location_subdest_stop.datetime - self.team_location_start.datetime,
            start_location_id=self.event.start_location_id,
            end_location_id=self.subdest_location.pk,
            team_id=self.team.pk
        )

        self.score_subdest_end = Score.objects.create(
            time=self.team_location_end.datetime - self.team_location_subdest_start.datetime,
            start_location_id=self.subdest_location.pk,
            end_location_id=self.event.end_location_id,
            team_id=self.team.pk
        )

        # Reset read head for image
        self.image_io.seek(0)

    """
    Unit tests for Scoreboard view
    """

    def test_scoreboard(self):
        print(separator)
        print("Testing /api/scoreboard/")
        print(separator)

        """
        GET request, unauthenticated (expected HTTP 401)
        """
        print("GET request, unauthenticated")
        print(small_separator)
        api_response = client.get(reverse(self.scoreboard_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Login
        request = self.client.post(reverse(self.login_url), {"username": self.user.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        POST request, as user (expected HTTP 405)
        """
        print("POST request, as user")
        print(small_separator)
        api_response = client.post(reverse(self.scoreboard_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, no active event (expected HTTP 404)
        """
        print("GET request, no active event")
        print(small_separator)
        api_response = client.get(reverse(self.scoreboard_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        GET request, active event, data (expected HTTP 200, valid data)
        """
        print("GET request, active event, data")
        print(small_separator)
        api_response = client.get(reverse(self.scoreboard_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Check against database
        api_response = api_response.data[0]
        self.assertEqual(api_response['final_time'], '01:30')
        print("Matching final time")
        self.assertEqual(api_response['bonus_time'], '00:00')
        print("Matching bonus time")
        self.assertEqual(api_response['travel_time'], '01:30')
        print("Matching travel time")
        self.assertEqual(api_response['is_disqualified'], False)
        print("Matching disqualification status")
        members = api_response['members']
        segments = api_response['segments']
        self.assertEqual(members[0], self.user.first_name)
        print("Matching team member")
        self.assertEqual(segments[0]['time'], '00:30')
        print("Segment 1 - Matching time")
        self.assertEqual(segments[0]['name'], "Eindhoven-Utrecht")
        print("Segment 1 - Matching name")
        self.assertEqual(segments[0]['order'], 1)
        print("Segment 1 - Matching order")
        self.assertEqual(segments[1]['time'], '01:00')
        print("Segment 2 - Matching time")
        self.assertEqual(segments[1]['name'], "Utrecht-Amsterdam")
        print("Segment 2 - Matching name")
        self.assertEqual(segments[1]['order'], 2)
        print("Segment 2 - Matching order")
        print(separator)

        # Mark challenge as accepted
        self.submission.is_accepted = True
        self.submission.save()

        """
        GET request, active event, data, bonus time (expected HTTP 200, valid data)
        """
        print("GET request, active event, data, bonus time")
        print(small_separator)
        api_response = client.get(reverse(self.scoreboard_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        api_response = api_response.data[0]
        self.assertEqual(api_response['final_time'], '01:15')
        print("Matching final time")
        self.assertEqual(api_response['bonus_time'], '00:15')
        print("Matching bonus time")
        self.assertEqual(api_response['travel_time'], '01:30')
        print("Matching travel time")
        self.assertEqual(api_response['is_disqualified'], False)
        print("Matching disqualification status")
        members = api_response['members']
        segments = api_response['segments']
        self.assertEqual(members[0], self.user.first_name)
        print("Matching team member")
        self.assertEqual(segments[0]['time'], '00:30')
        print("Segment 1 - Matching time")
        self.assertEqual(segments[0]['name'], "Eindhoven-Utrecht")
        print("Segment 1 - Matching name")
        self.assertEqual(segments[0]['order'], 1)
        print("Segment 1 - Matching order")
        self.assertEqual(segments[1]['time'], '01:00')
        print("Segment 2 - Matching time")
        self.assertEqual(segments[1]['name'], "Utrecht-Amsterdam")
        print("Segment 2 - Matching name")
        self.assertEqual(segments[1]['order'], 2)
        print("Segment 2 - Matching order")
        print(separator)

        # Remove data
        TeamLocation.objects.all().delete()
        Score.objects.all().delete()
        TeamChallenge.objects.all().delete()
        UserTeam.objects.all().delete()
        Team.objects.all().delete()

        """
        GET request, active event, no data (expected HTTP 200, valid data)
        """
        print("GET request, active event, no data")
        print(small_separator)
        api_response = client.get(reverse(self.scoreboard_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        assert not api_response.data
        print("Empty list")
        print(separator)

        # Delete temporary folder
        shutil.rmtree(self.folder)
