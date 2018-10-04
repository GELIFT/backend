from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils.timezone import now
from fcm_django.models import FCMDevice
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, \
    HTTP_417_EXPECTATION_FAILED
from rest_framework.views import APIView

from backend.serializers import LocationSerializer, TeamLocationStopSerializer
from webapp.models import Event, Team, UserTeam, Location, TeamLocation, Score

User = get_user_model()


class LocationView(APIView):
    """
    API endpoint allowing a user to submit his current location\n
    Allowed methods: POST\n
    Fields:\n
        - latitude: location latitude
        - longitude: location longitude
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: On invalid POST data
        - HTTP 401: When not authenticated
        - HTTP 404: When there is no active event or the user is not in a team for the active event
        - HTTP 405: On GET/PUT/DELETE requests
        - HTTP 417: When the timer is not started or there is no last known location
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = LocationSerializer(data=request.data)

        # Check if the POST data is valid
        if serializer.is_valid():
            # Check if there is an active event
            event = Event.objects.filter(is_active=True)
            if event:
                event = Event.objects.get(is_active=True)

                # Check if the requesting user is in a team for this event
                user = self.request.user
                team = UserTeam.objects.filter(user_id=user.pk, team__event_id=event.pk)

                if team:
                    # Check if timer is started
                    team = UserTeam.objects.get(user_id=user.pk, team__event_id=event.pk)
                    team = Team.objects.get(pk=team.team_id)

                    if team.timer_started:
                        # Check if there is a last known location
                        try:
                            last_location = TeamLocation.objects.filter(team_id=team.pk).latest('datetime')
                        except TeamLocation.DoesNotExist:
                            return Response(status=HTTP_417_EXPECTATION_FAILED)

                        segment = last_location.segment

                        # Create a new location
                        location = Location()
                        location.latitude = serializer.data.get("latitude")
                        location.longitude = serializer.data.get("longitude")
                        location.save()

                        # Associate it to the team
                        team_location = TeamLocation()
                        team_location.team_id = team.pk
                        team_location.location_id = location.pk
                        team_location.segment = segment
                        team_location.datetime = now()
                        team_location.save()

                        return Response(status=HTTP_200_OK)

                    else:
                        # The team timer is not started
                        return Response(status=HTTP_417_EXPECTATION_FAILED)
                else:
                    # Requesting user is not in a team for the active event
                    return Response(status=HTTP_404_NOT_FOUND)
            else:
                # There is no active event
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            # Invalid POST data
            return Response(status=HTTP_400_BAD_REQUEST)


class TeamLocationStart(viewsets.ModelViewSet):
    """
    API endpoint allowing a user to start its team timer\n
    Allowed methods: POST\n
    Fields:\n
        - latitude: user's latitude
        - longitude: user's longitude
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: If POST data is invalid
        - HTTP 401: If unauthenticated
        - HTTP 404: If there is no active event or the user is not in a team
        - HTTP 405: On GET/PUT/DELETE requests
        - HTTP 418: If the timer was already started by another team member
    :return: Nothing
    """
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = "post"
    serializer_class = LocationSerializer
    queryset = TeamLocation.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = LocationSerializer(data=request.data)
        # If POST data is valid
        if serializer.is_valid():
            # Get serializer data
            latitude = serializer.data.get("latitude")
            longitude = serializer.data.get("longitude")

            user = self.request.user

            # Check whether there is an active event
            event = Event.objects.filter(is_active=True)

            # If there is an active event
            if event:
                event = Event.objects.get(is_active=True)

                # Check if the requesting user is in a team for this event
                team = UserTeam.objects.filter(user_id=user.pk, team__event_id=event.pk)

                if team:
                    # Check if the timer is already running
                    team = UserTeam.objects.get(user_id=user.pk, team__event_id=event.pk)
                    team = Team.objects.get(pk=team.team_id)

                    # If not
                    if not team.timer_started:
                        # Start the team timer
                        team.timer_started = True
                        team.save()

                        # Get a list of participants of the same team (excluding requesting user)
                        team_members = UserTeam.objects.filter(team_id=team.pk).exclude(user_id=user.pk)
                        # Get team member devices
                        devices = FCMDevice.objects.filter(user_id__in=team_members.values_list('user_id'), active=True)
                        if devices:
                            # Send firebase message
                            devices.send_message(data={"timer_started": True})

                        # Create a new location with provided coordinates
                        location = Location()
                        location.latitude = latitude
                        location.longitude = longitude
                        location.save()

                        # Get existing last known location (if any) If there is not last known location,
                        # the new segment number will be 1. Otherwise last segment + 1
                        segment = 1
                        try:
                            previous_location = TeamLocation.objects.filter(team_id=team.pk).latest('datetime')
                        except TeamLocation.DoesNotExist:
                            previous_location = False

                        if previous_location:
                            segment = previous_location.segment + 1

                        # Create a new TeamLocation entry
                        team_location = TeamLocation()
                        team_location.team_id = team.pk
                        team_location.location_id = location.pk
                        team_location.segment = segment
                        team_location.datetime = now()
                        team_location.save()

                        # Return HTTP 200
                        return Response(status=HTTP_200_OK)

                    else:
                        # If the timer is already started for the team, return I'm a teapot
                        return Response(status=418)
                else:
                    # If the requesting user is not in a team for the event
                    return Response(status=HTTP_404_NOT_FOUND)
            else:
                # If there is no active event
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            # If POST data is invalid
            return Response(status=HTTP_400_BAD_REQUEST)


class TeamLocationStop(viewsets.ModelViewSet):
    """
    API endpoint allowing a user to stop its team timer\n
    Allowed methods: POST\n
    Fields:\n
        - latitude: user's latitude
        - longitude: user's longitude
        - location_id: -1 if not at a sublocation/end location, location ID otherwise
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 400: If POST data is invalid
        - HTTP 401: If unauthenticated
        - HTTP 404: If there is no active event or the user is not in a team
        - HTTP 405: On GET/PUT/DELETE requests
        - HTTP 417: If there is no previous last known location or if a provided location doesn't exist in the database
        - HTTP 418: If the timer was already stopped by another team member
    :return: Nothing
    """
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = "post"
    serializer_class = TeamLocationStopSerializer
    queryset = TeamLocation.objects.all()

    def create(self, request, *args, **kwargs):
        # Check if POST data is valid
        serializer = TeamLocationStopSerializer(data=request.data)
        if serializer.is_valid():
            # Check if there is an active event
            event = Event.objects.filter(is_active=True)
            if event:
                event = Event.objects.get(is_active=True)

                # Check if the requesting user is in a team for this event
                user = self.request.user
                team = UserTeam.objects.filter(user_id=user.pk, team__event_id=event.pk)

                if team:
                    # Check if the timer is already running
                    team = UserTeam.objects.get(user_id=user.pk, team__event_id=event.pk)
                    team = Team.objects.get(pk=team.team_id)

                    # If so
                    if team.timer_started:

                        # Retrieve last segment number
                        try:
                            last_team_location = TeamLocation.objects.filter(team_id=team.pk).latest('datetime')
                        except TeamLocation.DoesNotExist:
                            return Response(status=HTTP_417_EXPECTATION_FAILED)

                        last_segment = last_team_location.segment

                        # Check if a location ID is provided
                        latitude = serializer.data.get("latitude")
                        longitude = serializer.data.get("longitude")
                        location_id = serializer.data.get("location_id")

                        # Prepare a new TeamLocation entry
                        team_location = TeamLocation()
                        team_location.team_id = team.pk
                        team_location.segment = last_segment
                        team_location.datetime = now()

                        # If so, update score and set location ID to provided ID
                        if location_id is not -1:

                            # Verify whether the location exists in the database or not
                            location_check = Location.objects.filter(pk=location_id)
                            if not location_check:
                                return Response(status=HTTP_417_EXPECTATION_FAILED)

                            team_location.location_id = location_id
                            team_location.save()

                            # Check if there is already a score for that location
                            check_score = Score.objects.filter(team_id=team.pk, end_location_id=location_id)

                            # If there is none, calculate and store the new score
                            if not check_score:
                                # Get all distinct segments as a list
                                segments = list(
                                    TeamLocation.objects.filter(team_id=team.id)
                                        .distinct('segment')
                                        .values_list('segment', flat=True))
                                segments.sort()
                                # For each segment, calculate the time it took to complete
                                segment_times = []
                                for segment in segments:
                                    start_time = TeamLocation.objects.filter(team_id=team.id, segment=segment) \
                                        .earliest('datetime').datetime
                                    end_time = TeamLocation.objects.filter(team_id=team.id, segment=segment) \
                                        .latest('datetime').datetime

                                    time = end_time - start_time
                                    segment_times.append(time)

                                # Add the times of each segment to get the score
                                time_score = timedelta()
                                for time in segment_times:
                                    time_score = time_score + time

                                # Get the starting location
                                start_location = event.start_location_id

                                # Check for previous score
                                # If any, change the start location and calculate the score since then
                                previous_scores = Score.objects.filter(team_id=team.pk)
                                if previous_scores:
                                    for previous_score in previous_scores:
                                        time_score = time_score - previous_score.time

                                    # Get new starting location
                                    start_location = Score.objects.filter(team_id=team.pk).latest('id').end_location_id

                                # Store the score in the database, except if the calculated score is 00:00
                                score = Score()
                                score.team_id = team.pk
                                score.time = time_score
                                score.start_location_id = start_location
                                score.end_location_id = location_id
                                if time_score.total_seconds() != 0:
                                    score.save()

                        # If no location ID is provided, the score is not updated and a new location is stored
                        else:
                            location = Location()
                            location.latitude = latitude
                            location.longitude = longitude
                            location.save()

                            team_location.location_id = location.pk
                            team_location.save()

                        # Stop the timer
                        team.timer_started = False
                        team.save()

                        # Get a list of participants of the same team (excluding requesting user)
                        team_members = UserTeam.objects.filter(team_id=team.pk).exclude(user_id=user.pk)
                        # Get team member devices
                        devices = FCMDevice.objects.filter(user_id__in=team_members.values_list('user_id'), active=True)
                        if devices:
                            # Send firebase message
                            devices.send_message(data={"timer_started": False})

                        return Response(status=HTTP_200_OK)
                    else:
                        # Timer already stopped
                        return Response(status=418)
                else:
                    # User not in a team for the active event
                    return Response(status=HTTP_404_NOT_FOUND)
            else:
                # No active event
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            # If POST data is not valid
            return Response(status=HTTP_400_BAD_REQUEST)


class TeamRoute(APIView):
    """
    API endpoint allowing a user to view their team route
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: If unauthenticated
        - HTTP 404: If there is no route for the requesting user's team
        - HTTP 405: On POST/PUT/DELETE requests
    :return: A list of the locations the team went through, grouped by segment\n
        - segment: Segment number
        - locations:
            - id: Location ID
            - latitude: Location's latitude
            - longitude: Location's longitude
            - datetime: Date/time the team reached the location
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Check if there is an active event
        event = Event.objects.filter(is_active=True)
        if event:
            event = Event.objects.get(is_active=True)

            # Check if the requesting user is in a team for this event
            user = self.request.user
            team = UserTeam.objects.filter(user_id=user.pk, team__event_id=event.pk)

            if team:
                # Retrieve the entries from TeamLocation
                team = UserTeam.objects.get(user_id=user.pk, team__event_id=event.pk)
                team_locations = TeamLocation.objects.filter(team_id=team.team_id).order_by('segment')
                route = []
                segments = []

                # Get all the segments
                for team_location in team_locations:
                    if team_location.segment not in segments:
                        segments.append(team_location.segment)

                # For each segment, get the corresponding locations
                for segment in segments:
                    team_segment = TeamLocation.objects.filter(segment=segment, team_id=team.team_id)
                    locations = []
                    # For each location, get its corresponding data
                    for data in team_segment:
                        location = Location.objects.get(pk=data.location_id)
                        serialized_location = dict(id=location.id, latitude=location.latitude,
                                                   longitude=location.longitude, datetime=data.datetime)
                        locations.append(serialized_location)
                    # Combine locations with segment
                    combined_segments = dict(segment=segment, locations=locations)
                    route.append(combined_segments)
                return Response(route, status=HTTP_200_OK)
            else:
                # The user is not in a team for the active event
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            # There is no active event
            return Response(status=HTTP_404_NOT_FOUND)
