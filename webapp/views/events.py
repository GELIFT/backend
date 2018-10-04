from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_405_METHOD_NOT_ALLOWED, \
    HTTP_400_BAD_REQUEST

from backend.functions import time_format
from webapp.forms import EventCreationForm, EventLocationEditForm, EventEditForm, EventCityNameForm, EventWinnerForm
from webapp.functions import get_map
from webapp.models import Event, Team, Score, TeamLocation, TeamChallenge, Challenge, SubLocation, Location, UserTeam, \
    User

maps_key = settings.GMAPS_API_KEY


# Shows a specific event page
def event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    # If there is a winner photo
    photo = None
    if event.winner_photo:
        photo = event.winner_photo
    team_routes = get_map(event_id)

    # Get the teams
    teams = Team.objects.filter(event_id=event_id)
    team_ids = teams.values_list('id')

    # Get the sub-destinations
    sub_destinations = SubLocation.objects.filter(event_id=event_id).order_by('order')
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

    # If there is no subdestination, create the segment start city - end city
    if not sub_destinations:
        seg_name = event.start_city + "-" + event.end_city
        segment_names.append(seg_name)
        id = dict(order=1, end_id=event.end_location_id)
        segment_ids.append(id)

    # Construct array to return
    return_data = []
    winning_team = None
    # For each team
    for team in teams:
        # Get the member first names
        members = UserTeam.objects.filter(team_id=team.pk)
        users = User.objects.filter(pk__in=members.values_list('user_id'))
        names = []
        for user in users:
            names.append(user.first_name)

        # If the team won, add the names to the winning team
        if team.is_winner:
            winning_team = names

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

            segment = dict(name=segment_name, time=time)
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
        team_data = dict(team_id=team.pk, members=names, segments=segments, travel_time=travel_time,
                         bonus_time=bonus_time,
                         final_time=final_time, is_disqualified=team.is_disqualified)

        # Add the array to the return values
        return_data.append(team_data)

    # Sort the return list by total time
    return_data = sorted(return_data, key=lambda k: k['final_time'])
    return_data = sorted(return_data, key=lambda k: k['is_disqualified'])

    return render(request, 'webapp/event_detail.html',
                  {'teams': teams, 'team_routes': team_routes, 'event': event, 'subdestinations': sub_destinations,
                   'team_data': return_data, 'segment_names': segment_names, 'winning_team': winning_team,
                   'photo': photo, 'gmaps_key': maps_key})


# Shows the list of all events
def event_list(request):
    active_events = Event.objects.filter(is_active=True).order_by('-start_date')
    inactive_events = Event.objects.filter(is_active=False).order_by('-start_date')

    return render(request, 'webapp/events.html',
                  {'active_events': active_events, 'inactive_events': inactive_events})


# Allows the superuser to create an event
@login_required
def add_event(request):
    # Check if requesting user is the superuser
    if request.user.is_superuser:
        # Check if data was posted
        if request.method == "POST":
            # Check if the form is valid
            form = EventCreationForm(data=request.POST)
            if form.is_valid():

                # Get data from the form
                title = form.cleaned_data['title']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                emergency_contact = form.cleaned_data['emergency_contact']
                start_location = form.cleaned_data['start_location']
                end_location = form.cleaned_data['end_location']
                start_city = form.cleaned_data['start_city']
                end_city = form.cleaned_data['end_city']

                # If is_active checkbox is not shown, set it to false by default
                is_active = form.cleaned_data['is_active']
                if not is_active:
                    is_active = False

                # Create event
                Event.objects.create(title=title, start_date=start_date, end_date=end_date, winner_photo='',
                                     emergency_contact=emergency_contact, is_active=is_active,
                                     start_location_id=start_location.pk, end_location_id=end_location.pk,
                                     start_city=start_city, end_city=end_city)

                return render(request, 'webapp/admin/create_event.html', {'stored': True, })

        # If no data was posted, show the form
        else:

            # Verify whether there already is an active event
            is_active = False
            events = Event.objects.filter(is_active=True)
            # If so, set boolean is_active to true and hide the checkbox in the template
            if events:
                is_active = True
            form = EventCreationForm()
            return render(request, 'webapp/admin/create_event.html',
                          {'form': form, 'active_event': is_active, 'gmaps_key': maps_key})
    else:
        return redirect('login')


# Allows the superuser to delete an event
@login_required
def delete_event(request, event_id):
    if request.method == "GET":
        # Check if the user is a superuser
        if request.user.is_superuser:
            event = Event.objects.filter(pk=event_id)
            # If the event exists
            if event:
                # Get the teams
                teams = Team.objects.filter(event_id=event_id).values_list('id')
                # Delete the scores
                Score.objects.filter(team_id__in=teams).delete()
                # Delete the team locations
                TeamLocation.objects.filter(team_id__in=teams).delete()
                # Delete the team challenges
                TeamChallenge.objects.filter(team_id__in=teams).delete()
                # Delete the challenges
                Challenge.objects.filter(event_id=event_id).delete()
                # Delete the sub-destinations
                SubLocation.objects.filter(event_id=event_id).delete()
                # Delete the teams
                Team.objects.filter(event_id=event_id)
                # Delete the event
                Event.objects.filter(pk=event_id).delete()

                return HttpResponse(status=HTTP_200_OK)
            # Event does not exist
            return HttpResponse(status=HTTP_404_NOT_FOUND)
        # User is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows a superuser to edit an event
@login_required
def edit_event(request, event_id):
    # JQuery ajax requests
    if request.method == "POST":
        event = Event.objects.filter(pk=event_id)
        # If an event was provided
        if event:
            event = Event.objects.get(pk=event_id)
            form = EventEditForm(data=request.POST)

            # If the POST data is valid
            if form.is_valid():
                # Get fields
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                title = form.cleaned_data['title']
                emergency_contact = form.cleaned_data['emergency_contact']

                # Only allow changes on name and dates if the superuser makes the request
                if request.user.is_superuser:

                    # Change start date
                    if start_date:
                        event.start_date = start_date
                        event.save()
                        return HttpResponse(status=HTTP_200_OK)

                    # Change end date
                    if end_date:
                        event.end_date = end_date
                        event.save()
                        return HttpResponse(status=HTTP_200_OK)

                    # Change title
                    if title:
                        event.title = title
                        event.save()
                        return HttpResponse(status=HTTP_200_OK)

                    # Change emergency contact
                    if emergency_contact:
                        event.emergency_contact = emergency_contact
                        event.save()
                        return HttpResponse(status=HTTP_200_OK)

                    # If there is no information submitted
                    return HttpResponse(status=HTTP_400_BAD_REQUEST)

                else:
                    # If not superuser, return forbidden
                    return HttpResponse(status=HTTP_403_FORBIDDEN)
            else:
                # If the data is not valid, return 400
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        else:
            # If no event, return 400
            return HttpResponse(status=HTTP_400_BAD_REQUEST)

    # If the request is not an Ajax POST request
    else:
        # Get the event
        event = get_object_or_404(Event, pk=event_id)

        team_composition = []
        # Get the first five teams participating to this event
        teams = Team.objects.filter(event_id=event_id).order_by('id')
        event_winner = False

        for team in teams:
            # Get team composition
            team_members = UserTeam.objects.filter(team_id=team.pk)

            users = User.objects.filter(pk__in=team_members.values_list('user_id')).order_by('last_name')

            data = dict(team=team, members=users)
            team_composition.append(data)

            # If there is a winner
            if team.is_winner:
                event_winner = True

        # Get locations
        start_location = Location.objects.get(pk=event.start_location.pk)
        end_location = Location.objects.get(pk=event.end_location.pk)

        # Get the first five sub-destinations
        sub_locations = SubLocation.objects.filter(event_id=event.pk).order_by('order')[:5]

        # Get the first five challenges
        challenges = Challenge.objects.filter(event_id=event.pk).order_by('id')[:5]

        return render(request, 'webapp/admin/edit_event.html',
                      {'event': event, 'team_composition': team_composition,
                       'start_location': start_location, 'end_location': end_location,
                       'sub_locations': sub_locations, 'challenges': challenges, 'event_winner': event_winner,
                       'gmaps_key': maps_key})


# Allows the superuser to edit the start and end locations of an event
@login_required
def edit_event_location(request, event_id):
    if request.method == "POST":
        # Check if the user is the superuser
        if request.user.is_superuser:
            # If event id is provided
            if event_id:
                # Check if the event exists
                event = Event.objects.filter(pk=event_id)
                if event:
                    # Retrieve event
                    event = Event.objects.get(pk=event_id)
                    form = EventLocationEditForm(data=request.POST)

                    # Check if the POST data is valid
                    if form.is_valid():
                        location_type = form.cleaned_data["location_type"]
                        latitude = form.cleaned_data["latitude"]
                        longitude = form.cleaned_data["longitude"]

                        # Create a new location
                        location = Location()
                        location.latitude = latitude
                        location.longitude = longitude
                        location.save()

                        # If the changed location was the start location
                        if location_type == 'start':
                            event.start_location_id = location.pk

                        # If the changed location was the end location
                        if location_type == 'end':
                            event.end_location_id = location.pk

                        # Save the new location
                        event.save()

                        return HttpResponse(status=HTTP_200_OK)

                    # The POST data is invalid
                    else:
                        return HttpResponse(status=HTTP_400_BAD_REQUEST)

                # The event doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # If no event ID is provided, return an error
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # The user is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    else:
        return redirect('index')


# Allows the superuser to change the event city names
@login_required
def edit_event_city_name(request):
    if request.method == "POST":
        # Check for permission
        if request.user.is_superuser:
            # Check POST data
            form = EventCityNameForm(data=request.POST)
            if form.is_valid():
                # Retrieve data
                event_id = form.cleaned_data["event_id"]
                city_name = form.cleaned_data["city_name"]
                type = form.cleaned_data["type"]

                # Check if event exists
                event = Event.objects.filter(pk=event_id)
                if event:
                    event = Event.objects.get(pk=event_id)
                    # Check whether to update the start or end city name
                    if type == "start":
                        # Update start city name
                        event.start_city = city_name
                    elif type == "end":
                        # Update end city name
                        event.end_city = city_name
                    # The type is invalid
                    else:
                        return HttpResponse(status=HTTP_400_BAD_REQUEST)
                    # Save in database and return HTTP 200
                    event.save()
                    return HttpResponse(status=HTTP_200_OK)

                # Event doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # POST data invalid
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # User is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    # Request is not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows the superuser to mark an event as active
@login_required
def mark_event_active(request, event_id):
    if request.method == "GET":
        # Check if the user is the superuser
        if request.user.is_superuser:
            # Check if the event exists
            event = Event.objects.filter(pk=event_id)
            if event:
                # Get the event
                event = Event.objects.get(pk=event_id)

                # Check if it is already active
                if event.is_active is False:
                    # Mark all other events as inactive
                    other_events = Event.objects.exclude(pk=event_id)
                    for other_event in other_events:
                        other_event.is_active = False
                        other_event.save()

                    # Mark requested event as active
                    event.is_active = True
                    event.save()

                return HttpResponse(status=HTTP_200_OK)
            # Event doesn't exist
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # User is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows the superuser to mark an event as inactive
@login_required
def mark_event_inactive(request, event_id):
    if request.method == "GET":
        # Check if the user is the superuser
        if request.user.is_superuser:
            # Check if the event exists
            event = Event.objects.filter(pk=event_id)
            if event:
                # Get the event
                event = Event.objects.get(pk=event_id)

                # Check if it is already inactive
                if event.is_active is True:
                    # Mark requested event as inactive
                    event.is_active = False
                    event.save()

                return HttpResponse(status=HTTP_200_OK)

            # Event doesn't exist
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # User is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows the administrator to declare a winner for an event
@login_required
def event_winners(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    # In case of a POST request
    if request.method == "POST":
        # Check for existing winners
        winner = Team.objects.filter(event_id=event_id, is_winner=True)
        if winner:
            return redirect('edit_event', event_id)

        # Check for valid POST data
        form = EventWinnerForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            # If no picture is posted
            if not form.cleaned_data["photo"]:
                return render(request, 'webapp/admin/event_winners.html', {'new_entry': True, 'is_valid': False})

            team_id = form.cleaned_data["team_id"]
            photo = form.cleaned_data["photo"]

            # Set the team as the winning team
            team = Team.objects.get(pk=team_id)
            team.is_winner = True
            team.save()

            # Set the event's winner photo
            event.winner_photo = photo
            event.save()

            return render(request, 'webapp/admin/event_winners.html',
                          {'new_entry': True, 'is_valid': True, 'event': event})

        # POST data invalid
        else:
            return render(request, 'webapp/admin/event_winners.html', {'new_entry': True, 'is_valid': False})

    # GET request
    else:
        # If there is already a winning team
        teams = Team.objects.filter(event_id=event_id).exclude(is_disqualified=True)
        if True in teams.values_list('is_winner', flat=True):
            return redirect('edit_event', event_id)

        # Get team compositions
        team_composition = []
        for team in teams:
            team_members = UserTeam.objects.filter(team_id=team.pk)
            users = User.objects.filter(pk__in=team_members.values_list('user_id')).order_by('last_name')
            data = dict(team=team, members=users)
            team_composition.append(data)

        # Create the form
        form = EventWinnerForm()
        return render(request, 'webapp/admin/event_winners.html',
                      {'form': form, 'event': event, 'team_composition': team_composition})


# Allows an administrator to edit the winning team of an event
@login_required
def edit_event_winners(request, event_id):
    # Get the event, teams, and winner
    event = get_object_or_404(Event, pk=event_id)
    teams = Team.objects.filter(event_id=event_id).exclude(is_disqualified=True)
    winners = teams.filter(is_winner=True).values('id')

    # If there is no winning team
    if not winners:
        return redirect('edit_event', event_id)

    # POST request
    if request.method == "POST":
        # Check the form data
        form = EventWinnerForm(data=request.POST, files=request.FILES)

        # POST data valid
        if form.is_valid():
            team_id = form.cleaned_data["team_id"]
            photo = form.cleaned_data["photo"]

            # If the team does not exist
            if team_id not in list(teams.values_list('id', flat=True)):
                raise Http404()

            # Set the previous winning team back to non-winners
            old_winner = teams.get(is_winner=True)
            old_winner.is_winner = False
            old_winner.save()

            # Declare the selected new winning team as winners
            new_winner = teams.get(pk=team_id)
            new_winner.is_winner = True
            new_winner.save()

            # Save the new photo
            event.winner_photo = photo
            event.save()

            return render(request, 'webapp/admin/event_winners.html',
                          {'new_entry': True, 'is_valid': True, 'edit': True, 'event': event})

        # POST data invalid
        else:
            return render(request, 'webapp/admin/event_winners.html', {'new_entry': True, 'is_valid': False})

    # GET request
    else:
        # Construct teams
        team_composition = []
        for team in teams:
            # Get team composition
            team_members = UserTeam.objects.filter(team_id=team.pk)

            users = User.objects.filter(pk__in=team_members.values_list('user_id')).order_by('last_name')

            data = dict(team=team, members=users)
            team_composition.append(data)

        photo = event.winner_photo

        return render(request, 'webapp/admin/event_winners.html',
                      {'edit': True, 'team_composition': team_composition, 'photo': photo, 'winners': winners})


# Allows an administrator to delete the winner of an event
@login_required
def delete_event_winners(request, event_id):
    # Get the winning team
    winners = Team.objects.filter(event_id=event_id, is_winner=True)

    if winners:
        # Set the winning team to non-winners
        winners = winners.get()
        winners.is_winner = False
        winners.save()

    return HttpResponse(status=HTTP_200_OK)
