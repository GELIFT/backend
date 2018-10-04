from datetime import timedelta

from django.db.models import Max
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK
from rest_framework.views import APIView

from backend.functions import time_format
from webapp.models import Event, Team, UserTeam, User, SubLocation, Score, TeamChallenge, Challenge, TeamLocation


class Scoreboard(APIView):
    """
    API endpoint allowing a user to view the scoreboard
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 401: If unauthenticated
        - HTTP 404: If there is no active event
        - HTTP 405: On POST/PUT/DELETE requests
    :return: The scoreboard for the active event as a list with items for each team
        - members: list of teams members containing the first names of the members
        - segments: List of the segments
            - order: Order of the segment
            - name: Name of the segment (city to city)
            - time: Time the team took to complete the segment, N/A if not completed
        - travel_time: Total travel time of a team
        - bonus_time: Bonus time earned by a team via challenges
        - final_time: Total time - bonus time
        - is_disqualified: Whether the team is disqualified or not
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Get active event
        event = Event.objects.filter(is_active=True)
        if event:
            event = Event.objects.get(is_active=True)

            # Get the teams
            teams = Team.objects.filter(event_id=event.pk)
            team_ids = teams.values_list('id')

            # Get the sub-destinations
            sub_destinations = SubLocation.objects.filter(event_id=event.pk).order_by('order')
            last_sub_destination_order = sub_destinations.aggregate(order=Max('order')).get('order')

            # Get the challenges
            challenges = Challenge.objects.filter(event_id=event.pk)

            # Get the scores
            scores = Score.objects.filter(team_id__in=team_ids)
            team_locations = TeamLocation.objects.filter(team__event_id=event.pk)

            # Get the challenges validated by the teams
            team_challenges = TeamChallenge.objects.filter(team_id__in=team_ids, is_accepted=True)

            # Construct the segments

            segment_names = []
            segment_ids = []

            for location in sub_destinations:
                # If order is 1, then create the start location to first sub-destination segment
                if location.order == 1:
                    segment_names.append(event.start_city + "-" + location.city)
                    ids = dict(order=location.order, end_id=location.location_id)
                    segment_ids.append(ids)
                # If order is the biggest one in the table, add last sub-destination to end location segment
                if location.order == last_sub_destination_order:
                    segment_names.append(location.city + "-" + event.end_city)
                    ids = dict(order=location.order + 1, end_id=event.end_location_id)
                    segment_ids.append(ids)
                else:
                    next_location = sub_destinations.get(order=location.order + 1)
                    segment_names.append(location.city + "-" + next_location.city)
                    ids = dict(order=location.order + 1, end_id=next_location.location_id)
                    segment_ids.append(ids)

            # Construct array to return
            return_data = []

            # For each team
            for team in teams:

                # Get the member first names
                members = UserTeam.objects.filter(team_id=team.pk)
                users = User.objects.filter(pk__in=members.values_list('user_id'))
                names = []
                for user in users:
                    names.append(user.first_name)

                # For each segment, fetch the time and the order
                segments = []
                for segment_name in segment_names:
                    # Get the array index
                    index = segment_names.index(segment_name)

                    # Get the order and end location of the segment
                    order = segment_ids[index].get('order')
                    end_location = segment_ids[index].get('end_id')

                    # Get the score data for that segment
                    team_score = scores.filter(end_location_id=end_location, team_id=team.pk)
                    time = timedelta()
                    if team_score:
                        time = team_score.filter(end_location_id=end_location, team_id=team.pk).first().time

                    # Construct segment data (time in HH:MM format or N/A if equal to 00:00)
                    if time > timedelta(seconds=0):
                        time = time_format(time)
                    else:
                        time = "N/A"

                    segment = dict(order=order, name=segment_name, time=time)
                    segments.append(segment)

                # Fetch the bonus time
                bonus_time = timedelta()
                for team_challenge in team_challenges.filter(team_id=team.pk):
                    reward = challenges.get(pk=team_challenge.challenge_id).reward
                    bonus_time = bonus_time + reward

                # Calculate the total travel time
                total_travel_time = timedelta()
                team_location = team_locations.filter(team_id=team.pk)
                for data in team_location.values('segment').distinct():
                    segment = team_location.filter(segment=data['segment'])
                    start_time = segment.earliest('datetime').datetime
                    end_time = segment.latest('datetime').datetime

                    delta = end_time - start_time
                    total_travel_time = total_travel_time + delta

                # Calculate the final time
                final_time = total_travel_time - bonus_time

                # Convert the times to HH:MM format
                travel_time = time_format(total_travel_time)
                bonus_time = time_format(bonus_time)
                final_time = time_format(final_time)

                # Construct array for the team
                team_data = dict(members=names, segments=segments, travel_time=travel_time, bonus_time=bonus_time,
                                 final_time=final_time, is_disqualified=team.is_disqualified)

                # Add the array to the return values
                return_data.append(team_data)

            return Response(return_data, status=HTTP_200_OK)

        # No active event
        return Response(status=HTTP_404_NOT_FOUND)
