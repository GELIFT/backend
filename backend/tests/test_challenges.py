""" Unit tests for the challenges REST API (backend) """
import shutil
import tempfile
from base64 import b64encode
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, HTTP_200_OK, HTTP_401_UNAUTHORIZED, \
    HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from webapp.models import Location, Event, Team, UserTeam, Challenge, TeamChallenge

client = Client()
User = get_user_model()
separator = "====================================================================="
small_separator = "---------------------------------------------------------------------"


class ChallengeTests(TestCase):
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
    challenge_view_url = 'api_challenges'
    submit_url = 'api_challenge_submit'
    delete_submission_url = 'api_challenge_submission_delete'
    admin_view_url = 'api_challenge_admin'
    admin_accept_url = 'api_challenge_admin_accept'
    admin_reject_url = 'api_challenge_admin_reject'

    """
    Database set-up for unit tests
    """

    def setUp(self):
        # Set MEDIA_ROOT as temp folder
        settings.MEDIA_ROOT = self.folder
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

        # Create locations for challenges
        self.challenge_location_1 = Location.objects.create(latitude=2, longitude=2)
        self.challenge_location_2 = Location.objects.create(latitude=3, longitude=3)

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

        # Create challenges
        self.challenge_1 = Challenge.objects.create(
            title='Challenge 1',
            description='Description',
            reward='00:15',
            event_id=self.event.pk
        )
        self.challenge_2 = Challenge.objects.create(
            title='Challenge 2',
            description='Description',
            reward='00:10',
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

        # Reset read head for image
        self.image_io.seek(0)

    """
    Unit tests for view ChallengeView
    """

    def test_challenge_view(self):
        print(separator)
        print("Testing /api/challenges/")
        print(separator)

        """
        GET request, not logged in (expected HTTP 401)
        """
        print("GET request, not logged in")
        print(small_separator)
        api_response = client.get(reverse(self.challenge_view_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Login as user not in team
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        POST request (expected HTTP 405)
        """
        print("POST request")
        print(small_separator)
        api_response = client.post(reverse(self.challenge_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, no active event (expected HTTP 404)
        """
        print("GET request, no active event")
        print(small_separator)
        api_response = client.get(reverse(self.challenge_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Set event as active
        self.event.is_active = True
        self.event.save()

        """
        GET request, active event, user not in a team (expected HTTP 404)
        """
        print("GET request, active event, user not in a team")
        print(small_separator)
        api_response = client.get(reverse(self.challenge_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Login as a user in a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data["token"]
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        GET request, active event, user in a team (expected HTTP 200, valid data)
        """
        print("GET request, active event, user in a team")
        print(small_separator)
        api_response = client.get(reverse(self.challenge_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)

        # Check response data against database

        # Challenge 1
        print("Challenge 1")
        api_challenge_1 = api_response.data[1]
        self.assertEqual(api_challenge_1['id'], self.challenge_1.pk)
        print("Matching challenge ID")
        self.assertEqual(api_challenge_1['title'], self.challenge_1.title)
        print("Matching title")
        self.assertEqual(api_challenge_1['description'], self.challenge_1.description)
        print("Matching description")
        self.assertEqual(api_challenge_1['reward'], self.challenge_1.reward)
        print("Matching reward")
        self.assertEqual(api_challenge_1['status'], self.challenge_status['ur'])
        print("Matching challenge status")
        print(small_separator)

        # Challenge 2
        print("Challenge 2")
        api_challenge_2 = api_response.data[0]
        self.assertEqual(api_challenge_2['id'], self.challenge_2.pk)
        print("Matching challenge ID")
        self.assertEqual(api_challenge_2['title'], self.challenge_2.title)
        print("Matching title")
        self.assertEqual(api_challenge_2['description'], self.challenge_2.description)
        print("Matching description")
        self.assertEqual(api_challenge_2['reward'], self.challenge_2.reward)
        print("Matching reward")
        self.assertEqual(api_challenge_2['status'], self.challenge_status['o'])
        print("Matching challenge status")

        print(separator)

        # Delete teams
        self.submission.delete()
        self.team_member.delete()
        self.team.delete()

        """
        GET request, active event, no teams (expected HTTP 404)
        """
        api_response = client.get(reverse(self.challenge_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

    """
    Unit tests for view SubmitChallengeView
    """

    def test_submit_challenge_view(self):
        print(separator)
        print("Testing /api/challenges/submit/")
        print(separator)

        """
        POST request, non logged in (expected HTTP 401) 
        """
        print("POST request, non logged in")
        print(small_separator)
        api_response = client.post(reverse(self.submit_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as a user not in a team
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, inactive event (expected HTTP 405)
        """
        print("GET request, inactive event")
        print(small_separator)
        api_response = client.get(reverse(self.submit_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, inactive event, user not in a team (expected HTTP 404)
        """
        print("POST request, inactive event, user not in a team")
        print(small_separator)
        api_response = client.post(reverse(self.submit_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event active
        self.event.is_active = True
        self.event.save()

        """
        POST request, active event, user not in a team (expected HTTP 404)
        """
        print("POST request, active event, user not in a team")
        print(small_separator)
        api_response = client.post(reverse(self.submit_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Log in as a user in a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data["token"]
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        POST request, active event, user in a team, invalid data (expected HTTP 400)
        """
        print("POST request, active event, user in a team, invalid data")
        print(small_separator)
        api_response = client.post(reverse(self.submit_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, active event, user in a team, already existing submission (expected HTTP 403)
        """
        print("POST request, active event, user in a team, already existing submission")
        print(small_separator)

        data = {"longitude": 2, "latitude": 2, "challenge_id": self.challenge_1.pk, "picture": self.image}

        api_response = client.post(reverse(self.submit_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_403_FORBIDDEN)
        print("Got HTTP 403")
        print(separator)

        # Delete existing submission
        self.submission.delete()

        """
        POST request, active event, user in a team, file (expected HTTP 200 and valid data)
        """
        print("POST request, active event, user in a team, file")
        print(small_separator)

        # Reset image IO read head
        self.image_io.seek(0)

        data = {"longitude": 2, "latitude": 2, "challenge_id": self.challenge_1.pk, "picture": self.image}
        api_response = client.post(reverse(self.submit_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check data against database
        team_challenge = TeamChallenge.objects.latest('pk')
        location = Location.objects.get(pk=team_challenge.location_id)
        self.assertEqual(data["challenge_id"], team_challenge.challenge_id)
        print("Matching challenge ID")
        self.assertEqual(self.team_member.team_id, team_challenge.team_id)
        print("Matching team ID")
        self.assertEqual(team_challenge.is_accepted, False)
        print("Matching challenge status")
        self.assertEqual(data["latitude"], location.latitude)
        print("Matching latitude")
        self.assertEqual(data["longitude"], location.longitude)
        print("Matching longitude")

        # Reset image IO read head
        self.image_io.seek(0)

        self.assertEqual(team_challenge.picture.read(), self.image.read())
        print("Matching picture")
        print(separator)

        """
        POST request, active event, user in a team, b64 file (expected HTTP 200 and valid data)
        """
        print("POST request, active event, user in a team, b64 file")
        print(small_separator)

        # Reset image IO read head
        self.image_io.seek(0)
        # Encode the image in base64, and remove the first 'b' that indicates these are bytes
        b64_image = str(b64encode(self.image.read()))[1:]

        data = {"longitude": 3, "latitude": 3, "challenge_id": self.challenge_2.pk, "base64_picture": b64_image}
        api_response = client.post(reverse(self.submit_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check data against database
        team_challenge = TeamChallenge.objects.latest('pk')
        location = Location.objects.get(pk=team_challenge.location_id)
        self.assertEqual(data["challenge_id"], team_challenge.challenge_id)
        print("Matching challenge ID")
        self.assertEqual(self.team_member.team_id, team_challenge.team_id)
        print("Matching team ID")
        self.assertEqual(team_challenge.is_accepted, False)
        print("Matching challenge status")
        self.assertEqual(data["latitude"], location.latitude)
        print("Matching latitude")
        self.assertEqual(data["longitude"], location.longitude)
        print("Matching longitude")

        # Reset image IO read head
        self.image_io.seek(0)

        self.assertEqual(team_challenge.picture.read(), self.image.read())
        print("Matching picture")
        print(separator)

    """
    Unit tests for view DeleteChallengeSubmissionView
    """

    def test_delete_submission_view(self):
        print(separator)
        print("Testing /api/challenges/delete")
        print(separator)

        """
        POST request, not authenticated (expected HTTP 401) 
        """
        print("POST request, not authenticated")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as user not in a team
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": 'Token ' + token}

        """
        GET request, authenticated (expected HTTP 405)
        """
        print("GET request, authenticated")
        print(small_separator)
        api_response = client.get(reverse(self.delete_submission_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, inactive event, user not in a team (expected HTTP 404)
        """
        print("POST request, inactive event, user not in a team")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url), {"challenge_id": self.challenge_2.pk},
                                   **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Log in a user in a team
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data["token"]
        headers["HTTP_AUTHORIZATION"] = 'Token ' + token

        """
        POST request, active event, user not in a team (expected HTTP 404)
        """
        print("POST request, active event, user not in a team")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url), {"challenge_id": self.challenge_2.pk},
                                   **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        POST request, active event, user in a team, invalid data (expected HTTP 400)
        """
        print("POST request, active event, user in a team, invalid data")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(separator)

        """
        POST request, active event, user in a team, challenge does not exist (expected HTTP 404)
        """
        print("POST request, active event, user in a team, challenge does not exist")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url), {"challenge_id": 10}, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        """
        POST request, active event, user in a team, no submission (expected HTTP 404)
        """
        print("POST request, active event, user in a team, no submission")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url), {"challenge_id": self.challenge_2.pk},
                                   **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        """
        POST request, active event, user in a team, valid data (expected HTTP 200 and deleted submission)
        """
        print("POST request, active event, user in a team, valid data")
        print(small_separator)
        api_response = client.post(reverse(self.delete_submission_url), {"challenge_id": self.challenge_1.pk},
                                   **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        # Check against database
        submission_count = TeamChallenge.objects.filter(team_id=self.team_member.team_id).count()
        self.assertEqual(submission_count, 0)
        print("Submission deleted successfully")
        print(separator)

    """
    Unit tests for view AdminChallengeView
    """

    def test_admin_challenge_view(self):
        print(separator)
        print("Testing /api/admin/challenges")
        print(separator)
        """
        GET request, not authenticated (expected HTTP 401) 
        """
        print("GET request, not authenticated")
        print(small_separator)
        api_response = client.get(reverse(self.admin_view_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as a user
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data['token']
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, logged in as user (expected HTTP 403)
        """
        print("GET request, logged in as user")
        print(small_separator)
        api_response = client.get(reverse(self.admin_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_403_FORBIDDEN)
        print("Got HTTP 403")
        print(separator)

        # Log in as admin
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        POST request, authenticated as admin (expected HTTP 405)
        """
        print("POST request, authenticated as admin")
        print(small_separator)
        api_response = client.post(reverse(self.admin_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        GET request, as admin, no active event (expected HTTP 404)
        """
        print("GET request, as admin, no active event")
        print(small_separator)
        api_response = client.get(reverse(self.admin_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        # Mark event as active
        self.event.is_active = True
        self.event.save()

        """
        GET request, as admin, active event (expected HTTP 200, valid data)
        """
        print("GET request, as admin, active event")
        print(small_separator)
        api_response = client.get(reverse(self.admin_view_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check against database
        api_response = api_response.data[0]
        self.assertEqual(api_response["challenge_id"], self.challenge_1.pk)
        print("Matching challenge ID")
        self.assertEqual(api_response["challenge_title"], self.challenge_1.title)
        print("Matching challenge title")
        self.assertEqual(api_response["team_id"], self.submission.team_id)
        print("Matching team ID")
        full_url = settings.URL + self.submission.picture.url
        self.assertEqual(api_response["picture_link"], full_url)
        print("Matching picture link")
        print(separator)

    """
    Unit tests for view AcceptChallengeView
    """

    def test_accept_challenge_view(self):
        print(separator)
        print("Testing /api/admin/challenges/accept")
        print(separator)

        """
        POST request, non authenticated (expected HTTP 401)
        """
        print("POST request, non authenticated")
        print(small_separator)
        api_response = client.post(reverse(self.admin_accept_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as regular user
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as a user (expected HTTP 405)
        """
        print("GET request, as a user")
        print(small_separator)
        api_response = client.get(reverse(self.admin_accept_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, as a user (expected HTTP 403)
        """
        print("POST request, as a user")
        print(small_separator)
        api_response = client.post(reverse(self.admin_accept_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_403_FORBIDDEN)
        print("Got HTTP 403")
        print(separator)

        # Log in as admin
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        POST request, as admin, invalid data (expected HTTP 400)
        """
        print("POST request, as admin, invalid data")
        print(small_separator)
        api_response = client.post(reverse(self.admin_accept_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(small_separator)

        """
        POST request, as admin, non existing submission (expected HTTP 404)
        """
        print("POST request, as admin, non existing submission")
        print(small_separator)
        data = {"team_id": self.team.pk, "challenge_id": self.challenge_2.pk}
        api_response = client.post(reverse(self.admin_accept_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        """
        POST request, as admin, valid data (expected HTTP 200, submission set as 'accepted')
        """
        print("POST request, as admin, valid data")
        print(small_separator)
        data = {"team_id": self.team.pk, "challenge_id": self.challenge_1.pk}
        api_response = client.post(reverse(self.admin_accept_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check state in database
        challenge = TeamChallenge.objects.get(challenge_id=self.challenge_1.pk)
        self.assertEqual(challenge.is_accepted, True)
        print("Challenge submission successfully accepted")
        print(separator)

    """
    Unit tests for view RejectChallengeView
    """

    def test_reject_challenge_view(self):
        print(separator)
        print("Testing /api/admin/challenges/reject")
        print(separator)

        """
        POST request, non authenticated (expected HTTP 401)
        """
        print("POST request, non authenticated")
        print(small_separator)
        api_response = client.post(reverse(self.admin_reject_url))
        self.assertEqual(api_response.status_code, HTTP_401_UNAUTHORIZED)
        print("Got HTTP 401")
        print(separator)

        # Log in as regular user
        request = client.post(reverse(self.login_url), {'username': self.user.email, 'password': self.password})
        token = request.data["token"]
        headers = {"HTTP_AUTHORIZATION": "Token " + token}

        """
        GET request, as a user (expected HTTP 405)
        """
        print("GET request, as a user")
        print(small_separator)
        api_response = client.get(reverse(self.admin_reject_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        print("Got HTTP 405")
        print(separator)

        """
        POST request, as a user (expected HTTP 403)
        """
        print("POST request, as a user")
        print(small_separator)
        api_response = client.post(reverse(self.admin_reject_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_403_FORBIDDEN)
        print("Got HTTP 403")
        print(separator)

        # Log in as admin
        client.get(reverse(self.logout_url))
        request = client.post(reverse(self.login_url), {'username': self.team_user.email, 'password': self.password})
        token = request.data['token']
        headers["HTTP_AUTHORIZATION"] = "Token " + token

        """
        POST request, as admin, invalid data (expected HTTP 400)
        """
        print("POST request, as admin, invalid data")
        print(small_separator)
        api_response = client.post(reverse(self.admin_reject_url), **headers)
        self.assertEqual(api_response.status_code, HTTP_400_BAD_REQUEST)
        print("Got HTTP 400")
        print(small_separator)

        """
        POST request, as admin, non existing submission (expected HTTP 404)
        """
        print("POST request, as admin, non existing submission")
        print(small_separator)
        data = {"team_id": self.team.pk, "challenge_id": self.challenge_2.pk}
        api_response = client.post(reverse(self.admin_reject_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_404_NOT_FOUND)
        print("Got HTTP 404")
        print(separator)

        """
        POST request, as admin, valid data (expected HTTP 200, submission set as 'accepted')
        """
        print("POST request, as admin, valid data")
        print(small_separator)
        data = {"team_id": self.team.pk, "challenge_id": self.challenge_1.pk}
        api_response = client.post(reverse(self.admin_reject_url), data=data, **headers)
        self.assertEqual(api_response.status_code, HTTP_200_OK)
        print("Got HTTP 200")
        print(small_separator)
        # Check state in database
        challenge = TeamChallenge.objects.filter(team_id=self.team.pk).count()
        self.assertEqual(challenge, 0)
        print("Challenge submission successfully accepted")
        print(separator)

        # Delete temporary folder
        shutil.rmtree(self.folder)
