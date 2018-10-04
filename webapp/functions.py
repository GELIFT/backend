# Get map for a specific event

from webapp.models import Team, TeamLocation, Location, Event


def get_map(event_id):
    event = Event.objects.filter(pk=event_id)

    if event:
        event = Event.objects.get(pk=event_id)
        teams = Team.objects.filter(event=event)
        # This is our return array. It will contain all segments, which are arrays of locations with the team_id at 0
        # format: [[team_id_1, loc_1, loc_2, ..., loc_25], [team_id_1, loc_26, loc_27, ...], ... [team_id_2, loc1, ...]]
        team_routes = []

        # Get the location history of all teams
        if teams:
            for team in teams:
                # Get the location history of one team, in order of ascending date
                team_locations = TeamLocation.objects.filter(team=team).order_by('datetime')
                team_segments = []

                # Get all the segments
                for team_location in team_locations:
                    if team_location.segment not in team_segments:
                        team_segments.append(team_location.segment)

                # For each segment, add the team ID and the corresponding locations
                for team_segment in team_segments:
                    segment = [team.id]
                    segment_locations = Location.objects.filter(teamlocation__team=team,
                                                                teamlocation__segment=team_segment)
                    # segment.append(list(segment_locations))
                    for location in segment_locations:
                        segment.append({'lat': location.latitude, 'lng': location.longitude})

                    # Add the segment to the return array
                    team_routes.append(segment)

            return team_routes
    else:
        return None
