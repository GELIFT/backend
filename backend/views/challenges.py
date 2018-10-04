from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from rest_framework.views import APIView

from backend.functions import decode_base64_file, time_format
from backend.serializers import ChallengeSubmitSerializer, ChallengeReviewSerializer, \
    ChallengeSubmissionDeletionSerializer
from webapp.models import Event, UserTeam, Team, Challenge, TeamChallenge, Location

User = get_user_model()


class ChallengeView(APIView):
    """
    API endpoint allowing a team member to get the challenges for the active event\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: When not authenticated
        - HTTP 404: No active event exists, no teams exist for the active event
                    or the requesting user is not in a team
        - HTTP 405: On POST/PUT/DELETE requests
    :return:\n
        - id: challenge ID
        - title: challenge title
        - description: challenge description
        - reward: challenge reward (HH:MM)
        - status: Indicates the status of the challenge for the requesting user's team
            - "open": When the team has not submitted a request for review or when a request was rejected
            - "under_review": When a review request was submitted but is pending
            - "accepted": When a review request was submitted and validated by an administrator
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Try to get the active event
        event = Event.objects.filter(is_active=True)
        if event:
            # Get the active event
            event = Event.objects.get(is_active=True)
            # Get the user's teams
            teams = UserTeam.objects.filter(user_id=request.user.pk)
            if teams:
                # Try to get the user's team for the active event
                team = Team.objects.filter(event_id=event.pk, pk__in=teams.values_list('team_id'))
                if team:
                    # Get the user's team for the active event
                    team = Team.objects.get(event_id=event.pk, pk__in=teams.values_list('team_id'))
                    # Get all the challenges for the active event
                    challenges = Challenge.objects.filter(event_id=event.pk)

                    # List of challenges that will be returned
                    challenge_list = []
                    for challenge in challenges:
                        # Set the default status as "open"
                        status = "open"

                        # For each challenge, retrieve the status for the user's team
                        team_challenge = TeamChallenge.objects.filter(challenge_id=challenge.pk, team_id=team.pk)
                        if team_challenge:
                            # If there is an entry, get the status
                            team_challenge = TeamChallenge.objects.get(challenge_id=challenge.pk, team_id=team.pk)
                            status = team_challenge.is_accepted
                            if status:
                                status = "accepted"
                            else:
                                status = "under_review"

                        # Construct the data to return
                        reward = time_format(challenge.reward)
                        data = dict(id=challenge.pk, title=challenge.title, description=challenge.description,
                                    reward=reward, status=status)
                        # Add it to the list
                        challenge_list.append(data)
                    # Return the list
                    return Response(challenge_list, status=HTTP_200_OK)

                # The requesting user is not in a team for the active event
                else:
                    return Response(status=HTTP_404_NOT_FOUND)
            # The requesting user is not in a team
            else:
                return Response(status=HTTP_404_NOT_FOUND)
        # No active event
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class SubmitChallengeView(APIView):
    """
    API endpoint allowing a user to submit an entry for a challenge\n
    Allowed methods: POST\n
    Fields:\n
        - challenge_id: ID of the challenge the entry is made for
        - latitude : location latitude
        - longitude: location longitude
        - picture: data field containing a binary picture file (required if @base64_picture is empty)
        - base64_picture: base64 encoded picture (required if @picture is empty)
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: On invalid POST data
        - HTTP 401: When unauthorized
        - HTTP 403: When there is already an entry for this team for challenge @challenge_id
        - HTTP 404: When there is no active event or the user is not in a team for the active event
        - HTTP 405: On GET/PUT/DELETE requests
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = self.request.user
        # Get the active event
        event = Event.objects.filter(is_active=True)
        if event:
            event = Event.objects.get(is_active=True)
            # Check if the user is in a team
            team = UserTeam.objects.filter(team__event_id=event.pk, user_id=user.pk)
            if team:
                team = UserTeam.objects.get(team__event_id=event.pk, user_id=user.pk)
                # Check if POST data is valid
                serializer = ChallengeSubmitSerializer(data=request.data)
                if serializer.is_valid():
                    # Check if an image is submitted
                    base64_picture = serializer.data.get("base64_picture")

                    # Try to get a picture if it was submitted in binary form
                    try:
                        picture = serializer.validated_data["picture"]
                    except KeyError:
                        picture = None

                    if picture or base64_picture:
                        # Check if challenge exists
                        challenge_id = serializer.validated_data["challenge_id"]
                        challenge = Challenge.objects.filter(pk=challenge_id)
                        if challenge:
                            # Check if there is already an entry
                            team_entry = TeamChallenge.objects.filter(team_id=team.team_id, challenge_id=challenge_id)
                            if not team_entry:
                                # Retrieve data and save it
                                location = Location()
                                location.latitude = serializer.validated_data["latitude"]
                                location.longitude = serializer.validated_data["longitude"]
                                location.save()

                                team_challenge = TeamChallenge()
                                team_challenge.challenge_id = serializer.validated_data["challenge_id"]
                                team_challenge.is_accepted = False
                                team_challenge.team_id = team.team_id
                                team_challenge.location_id = location.pk

                                if base64_picture:
                                    picture = decode_base64_file(base64_picture)

                                team_challenge.picture = picture

                                team_challenge.save()

                                return Response(status=HTTP_200_OK)
                            # There is already an entry for this team and challenge
                            else:
                                return Response(status=HTTP_403_FORBIDDEN)
                        # The challenge doesn't exist
                        else:
                            return Response(status=HTTP_404_NOT_FOUND)
                    # No picture was submitted
                    else:
                        return Response(status=HTTP_400_BAD_REQUEST)
                # POST data invalid
                else:
                    return Response(status=HTTP_400_BAD_REQUEST)
            # The user is not in a team
            else:
                return Response(status=HTTP_404_NOT_FOUND)
        # No active event
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class DeleteChallengeSubmissionView(APIView):
    """
        API endpoint allowing an team member to delete a submission for a challenge\n
        Allowed methods: POST\n
        Fields:\n
            - challenge_id: ID of the challenge for which the submission needs to be deleted
        Possible HTTP responses:\n
            - HTTP 200: On successful request
            - HTTP 400: On invalid POST data
            - HTTP 401: When unauthorized
            - HTTP 404: When there is no active event, the user is not in a team, the challenge doesn't exist or
                        there is no submission for the user's team for @challenge_id
            - HTTP 405: On GET/PUT/DELETE requests
        """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # Validate the POST data
        serializer = ChallengeSubmissionDeletionSerializer(data=request.POST)
        if serializer.is_valid():
            user = self.request.user
            # Get the active event
            event = Event.objects.filter(is_active=True)
            if event:
                event = Event.objects.get(is_active=True)
                # Check if the user is in a team
                teams = Team.objects.filter(event_id=event.pk)
                user_team = UserTeam.objects.filter(user_id=user.pk, team_id__in=teams.values_list('id'))

                if user_team:
                    user_team = UserTeam.objects.get(user_id=user.pk, team_id__in=teams.values_list('id'))

                    # Get the challenge
                    challenge_id = serializer.validated_data['challenge_id']
                    challenge = Challenge.objects.filter(pk=challenge_id)

                    if challenge:
                        # Get the submission (only if under review)
                        submission = TeamChallenge.objects.filter(team_id=user_team.team_id, challenge_id=challenge_id,
                                                                  is_accepted=False)
                        if submission:
                            # Delete the submission
                            submission.delete()
                            return Response(status=HTTP_200_OK)

                        # No submission found
                        else:
                            return Response(status=HTTP_404_NOT_FOUND)
                    # The challenge does not exist
                    else:
                        return Response(status=HTTP_404_NOT_FOUND)
                # The user is not in a team for the active event
                else:
                    return Response(status=HTTP_404_NOT_FOUND)
            # No active event
            else:
                return Response(status=HTTP_404_NOT_FOUND)
        # Invalid POST data
        else:
            return Response(status=HTTP_400_BAD_REQUEST)


class AdminChallengeView(APIView):
    """
    API endpoint allowing an administrator to get the submissions for the challenges (active event)\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: When not authenticated
        - HTTP 403: When the requesting user is not an administrator
        - HTTP 404: When no active event is found
        - HTTP 405: On POST/PUT/DELETE requests
    :return:\n
        - challenge_id: Challenge ID
        - challenge_title: The title of the challenge
        - team_id: ID of the team that requested a review
        - picture_link: A link to the picture up for review
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = self.request.user
        # Check for permission
        if user.is_staff:
            # Check for active event
            event = Event.objects.filter(is_active=True)
            if event:
                event = Event.objects.get(is_active=True)
                # Get the submissions
                challenges = Challenge.objects.filter(event_id=event.pk)
                submissions = TeamChallenge.objects.filter(challenge_id__in=challenges.values_list('id'),
                                                           is_accepted=False)

                # Create list of submissions to return
                submission_list = []
                # Populate the list
                for submission in submissions:
                    # Get the link to the picture
                    picture_link = settings.URL + submission.picture.url
                    # Get the challenge title
                    challenge_title = Challenge.objects.get(pk=submission.challenge_id).title
                    data = dict(challenge_id=submission.challenge_id, team_id=submission.team_id,
                                picture_link=picture_link, challenge_title=challenge_title)
                    submission_list.append(data)

                return Response(submission_list, status=HTTP_200_OK)

            # No active event
            else:
                return Response(status=HTTP_404_NOT_FOUND)
        # The requesting user is not an administrator
        else:
            return Response(status=HTTP_403_FORBIDDEN)


class AcceptChallengeView(APIView):
    """
    API endpoint allowing an administrator to accept a challenge submission\n
    Allowed methods: POST\n
    Fields:\n
        - challenge_id: ID of the challenge the entry is made for
        - team_id: ID of the team that made the submission
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: On invalid POST data
        - HTTP 401: When unauthorized
        - HTTP 403: When the requesting user is not an administrator
        - HTTP 404: When the submission does not exist
        - HTTP 405: On GET/PUT/DELETE requests
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = self.request.user
        # Check for permission
        if user.is_staff:
            # Check POST data
            serializer = ChallengeReviewSerializer(data=request.data)
            if serializer.is_valid():
                # Retrieve data
                challenge_id = serializer.validated_data["challenge_id"]
                team_id = serializer.validated_data["team_id"]

                # Check if the submission exists
                submission = TeamChallenge.objects.filter(challenge_id=challenge_id, team_id=team_id)
                if submission:
                    # Mark the submission as accepted
                    submission = TeamChallenge.objects.get(challenge_id=challenge_id, team_id=team_id)
                    submission.is_accepted = True
                    submission.save()
                    return Response(status=HTTP_200_OK)
                # The submission does not exist
                else:
                    return Response(status=HTTP_404_NOT_FOUND)
            # POST data invalid
            else:
                return Response(status=HTTP_400_BAD_REQUEST)
        # User is not an administrator
        else:
            return Response(status=HTTP_403_FORBIDDEN)


class RejectChallengeView(APIView):
    """
    API endpoint allowing an administrator to reject a challenge submission\n
    Allowed methods: POST\n
    Fields:\n
        - challenge_id: ID of the challenge the entry is made for
        - team_id: ID of the team that made the submission
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: On invalid POST data
        - HTTP 401: When unauthorized
        - HTTP 403: When the requesting user is not an administrator
        - HTTP 404: When the submission does not exist
        - HTTP 405: On GET/PUT/DELETE requests
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = self.request.user
        # Check for permission
        if user.is_staff:
            # Check POST data
            serializer = ChallengeReviewSerializer(data=request.data)
            if serializer.is_valid():
                # Retrieve data
                challenge_id = serializer.validated_data["challenge_id"]
                team_id = serializer.validated_data["team_id"]

                # Check if the submission exists
                submission = TeamChallenge.objects.filter(challenge_id=challenge_id, team_id=team_id)
                if submission:
                    # Delete submission and stored image
                    submission = TeamChallenge.objects.get(challenge_id=challenge_id, team_id=team_id)
                    submission.picture.delete()
                    submission.delete()
                    return Response(status=HTTP_200_OK)
                # The submission does not exist
                else:
                    return Response(status=HTTP_404_NOT_FOUND)
            # POST data invalid
            else:
                return Response(status=HTTP_400_BAD_REQUEST)
        # User is not an administrator
        else:
            return Response(status=HTTP_403_FORBIDDEN)
