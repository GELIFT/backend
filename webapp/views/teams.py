from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, \
    HTTP_405_METHOD_NOT_ALLOWED

from webapp.forms import IdForm, UserTeamForm
from webapp.models import Team, Score, TeamLocation, UserTeam, Event, User


# Allows an administrator to edit teams
@login_required
def edit_teams(request, event_id):
    # Fetch the event
    event = get_object_or_404(Event, pk=event_id)

    # Get existing teams
    team_composition = []
    # Get teams participating to this event
    teams = Team.objects.filter(event_id=event_id).order_by('id')

    for team in teams:
        # Get team composition
        team_members = UserTeam.objects.filter(team_id=team.pk)

        users = User.objects.filter(pk__in=team_members.values_list('user_id')).order_by('last_name')

        data = dict(team=team, members=users)
        team_composition.append(data)

    # Get users not in teams
    registered_users = UserTeam.objects.filter(team_id__in=teams).values_list('user_id')
    unassigned_users = User.objects.exclude(pk__in=registered_users).order_by('last_name')

    return render(request, 'webapp/admin/edit_teams.html',
                  {'event': event, 'team_composition': team_composition, 'unassigned_users': unassigned_users})


# Allows an administrator to delete a team for an event
@login_required
def delete_team(request):
    if request.method == "POST":
        # Check if user is an administrator
        if request.user.is_staff:
            # Check if POST data is valid
            form = IdForm(data=request.POST)
            if form.is_valid():
                # Get Team ID
                team_id = form.cleaned_data["id"]
                # Check if team exists
                team = Team.objects.filter(pk=team_id)
                if team:
                    # Retrieve team
                    team = Team.objects.get(pk=team_id)
                    # Delete associated scores
                    scores = Score.objects.filter(team_id=team.pk)
                    for score in scores:
                        score.delete()

                    # Delete associated locations
                    team_locations = TeamLocation.objects.filter(team_id=team.pk)
                    for team_location in team_locations:
                        team_location.delete()

                    # Delete team members
                    team_members = UserTeam.objects.filter(team_id=team.pk)
                    for team_member in team_members:
                        team_member.delete()

                    # Delete team
                    team.delete()

                    return HttpResponse(status=HTTP_200_OK)

                # Team doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # POST data invalid
            else:
                return HttpResponse(HTTP_400_BAD_REQUEST)
        # User is not an administrator
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows an administrator to create a team
@login_required
def add_team(request):
    # Only allow POST requests
    if request.method == "POST":
        # Check if the POST data is valid
        form = IdForm(data=request.POST)
        if form.is_valid():
            # Check if the event exists
            event_id = form.cleaned_data['id']
            event = Event.objects.filter(pk=event_id)
            if event:
                # Create a team
                team = Team()
                team.is_winner = False
                team.is_winner = False
                team.event_id = event_id
                team.timer_started = False
                team.save()

                return HttpResponse(status=HTTP_200_OK)
            # The event doesn't exist
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # Request data is invalid
        else:
            return HttpResponse(HTTP_400_BAD_REQUEST)
    # If the request type is not POST
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows an administrator to remove a user from a team (AJAX)
@login_required
def remove_member(request):
    # Check for POST request
    if request.method == 'POST':
        # Check for valid input
        form = UserTeamForm(data=request.POST)
        if form.is_valid():
            # Retrieve data
            user_id = form.cleaned_data['user_id']
            team_id = form.cleaned_data['team_id']

            # Verify if the user is in the team
            member = UserTeam.objects.filter(user_id=user_id, team_id=team_id)

            if member:
                # Delete team member
                member.delete()
                return HttpResponse(status=HTTP_200_OK)

            # User not in team
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # POST data invalid
        else:
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
    # Request is not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows an administrator to add a user to a team (AJAX)
@login_required
def add_member(request):
    # Check for a POST request:
    if request.method == "POST":
        # Validate the POST data
        form = UserTeamForm(data=request.POST)
        if form.is_valid():
            # Check if user and team exist
            user_id = form.cleaned_data["user_id"]
            team_id = form.cleaned_data["team_id"]
            user = User.objects.filter(pk=user_id)
            team = Team.objects.filter(pk=team_id)

            if user and team:
                # Get the member count
                member_count = UserTeam.objects.filter(team_id=team_id).count()

                # If the number of members in the team is lower than the maximum allowed
                if member_count < 3:
                    member = UserTeam()
                    member.team_id = team_id
                    member.user_id = user_id
                    member.save()
                    return HttpResponse(status=HTTP_200_OK)

                # If the team is already full
                else:
                    return HttpResponse(status=HTTP_403_FORBIDDEN)

            # Either the user or the team was not found
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # POST data not valid
        else:
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
    # Request is not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows an administrator to move a member from a team to another (AJAX)
@login_required
def move_member(request):
    # Check for a POST request
    if request.method == 'POST':
        # Check if the provided data is valid
        form = UserTeamForm(data=request.POST)
        if form.is_valid():
            # Retrieve data
            old_team_id = form.cleaned_data['old_team_id']
            new_team_id = form.cleaned_data['team_id']
            user_id = form.cleaned_data['user_id']

            # Check whether there is an old team ID
            if old_team_id:
                # Check if the user and new team exist, and if the user is in the old team
                new_team = Team.objects.filter(pk=new_team_id)
                old_team = Team.objects.filter(pk=old_team_id)
                user = User.objects.filter(pk=user_id)
                old_member = UserTeam.objects.filter(user_id=user_id, team_id=old_team_id)

                if old_team and new_team and user and old_member:
                    # Get the old team
                    old_member = UserTeam.objects.get(user_id=user_id, team_id=old_team_id)
                    # Move the user
                    old_member.team_id = new_team_id
                    old_member.save()
                    return HttpResponse(status=HTTP_200_OK)

                # Some of the data does not exist in the database
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # No old team ID provided
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # POST data invalid
        else:
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
    # Request is not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows an administrator to disqualify a team
@login_required
def disqualify_team(request):
    # Check for POST request
    if request.method == 'POST':
        # Check for valid input
        form = IdForm(data=request.POST)
        if form.is_valid():
            # Retrieve data
            team_id = form.cleaned_data['id']

            # Verify if the team exists
            team = Team.objects.filter(pk=team_id)

            if team:
                # Disqualify team
                team = Team.objects.get(pk=team_id)
                team.is_disqualified = True
                team.save()
                return HttpResponse(status=HTTP_200_OK)

            # Team doesn't exist
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # POST data invalid
        else:
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
    # Request is not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows an administrator to remove the disqualification of a team
@login_required
def undisqualify_team(request):
    # Check for POST request
    if request.method == 'POST':
        # Check for valid input
        form = IdForm(data=request.POST)
        if form.is_valid():
            # Retrieve data
            team_id = form.cleaned_data['id']

            # Verify if the team exists
            team = Team.objects.filter(pk=team_id)

            if team:
                # Remove disqualification
                team = Team.objects.get(pk=team_id)
                team.is_disqualified = False
                team.save()
                return HttpResponse(status=HTTP_200_OK)

            # Team doesn't exist
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)
        # POST data invalid
        else:
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
    # Request is not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
