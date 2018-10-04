from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from backend.serializers import PublicUserSerializer
from webapp.models import Event, Team, UserTeam, Location, TeamLocation

User = get_user_model()


class TeamView(APIView):
    """
    API endpoint allowing to get all teams for the active event\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: When unauthenticated
        - HTTP 404: When no team exists/is associated to the active event or when there is no active event
        - HTTP 405: On POST/PUT/DELETE requests
    :return: List of teams\n
        - id: team ID
        - is_disqualified: Whether the team is disqualified
        - is_winner: Whether the team is this event's winner
        - members: List of team members
            - id: team member ID
            - first_name: team member first name
            - last_name: team member last name
        last_location: last known location of the team
            - latitude: location latitude
            - longitude: location longitude
            - datetime: date and time when the destination was reached
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Get the active event
        event = Event.objects.filter(is_active=True)

        # If it exists
        if event:
            event = Event.objects.get(is_active=True)

            # Get the teams associated to the event
            teams = Team.objects.filter(event_id=event.pk)

            # If they exists, return them
            if teams:

                response = []

                # For each team:
                for team in teams:

                    # Get the team members
                    members = UserTeam.objects.filter(team_id=team.pk)
                    team_members = []
                    # Add the member to the team member array
                    for member in members:
                        member_object = User.objects.get(pk=member.user_id)
                        member_data = dict(id=member_object.pk, first_name=member_object.first_name,
                                           last_name=member_object.last_name)

                        team_members.append(member_data)

                    # Try to get the last known location for a team
                    try:
                        last_location = TeamLocation.objects.filter(team_id=team.pk).latest('datetime')
                    except TeamLocation.DoesNotExist:
                        last_location = False

                    # If it exists, retrieve location info
                    if last_location:
                        location = Location.objects.get(pk=last_location.location_id)
                        location = dict(latitude=location.latitude, longitude=location.longitude,
                                        datetime=last_location.datetime)

                    # Otherwise return a blank location
                    else:
                        location = {}
                    # Create a dictionary containing the data
                    data = dict(id=team.pk, is_disqualified=team.is_disqualified, is_winner=team.is_winner,
                                members=team_members, last_location=location)
                    response.append(data)

                # Return the data
                return Response(response)
            # Otherwise return 404
            else:
                return Response(status=HTTP_404_NOT_FOUND)

        # If there is no active event
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class MyTeamView(APIView):
    """
    API endpoint allowing to retrieve a user's team\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: When unauthenticated
        - HTTP 404: When there is no active event or the requesting user is not in a team for this event
        - HTTP 405: On POST/PUT/DELETE requests
    :return:\n
        - id: team ID
        - is_disqualified: whether the team is disqualified
        - is_winner: whether the team is the event's winner
        - timer_started: whether the team timer is running
        - members: list of team members
            - id: team member ID
            - first_name: team member first name
            - last_name: team member last name
            - email: team member email
            - phone: team member phone number
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):

        # Get the ID of the user performing the request
        user_id = self.request.user.pk

        # Get the active event (if it exists)
        active_event = Event.objects.filter(is_active=True)

        # If there is an active event, get the teams associated to it
        if active_event:
            active_event = Event.objects.get(is_active=True)
            teams = Team.objects.filter(event_id=active_event)

            # Look for the requesting user's team
            team_id = -1
            for team in teams:
                team_members = UserTeam.objects.filter(team_id=team, user_id=user_id)

                # If the requesting user is in a team for the active event,
                if team_members:
                    team_members = UserTeam.objects.get(team_id=team, user_id=user_id)
                    team_id = team_members.team_id

            # If there exists such a user, get the other team members
            if team_id is not -1:
                team_members = []
                team = Team.objects.get(pk=team_id)
                team_members_id = UserTeam.objects.filter(team_id=team.pk).order_by('user_id')

                # Get team members' informations
                for user in team_members_id:
                    user = User.objects.get(pk=user.user_id)
                    serializer = PublicUserSerializer(user)
                    team_members.append(serializer.data)

                # Return requesting user's team
                data = dict(id=team.pk, is_disqualified=team.is_disqualified, is_winner=team.is_winner,
                            timer_started=team.timer_started, members=team_members)

                return Response(data)

            # If the requesting user is not in a team for the active event, return 404
            else:
                return Response(status=HTTP_404_NOT_FOUND)

        # If there is no active event, return 404
        else:
            return Response(status=HTTP_404_NOT_FOUND)
