from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_405_METHOD_NOT_ALLOWED

from backend.functions import time_format
from webapp.forms import ChallengeCreationForm, IdForm
from webapp.models import Event, Challenge, TeamChallenge


def challenges(request, event_id):
    # Get the event
    event = get_object_or_404(Event, pk=event_id)
    # Get the challenges
    challenges = Challenge.objects.filter(event_id=event.pk).order_by('id')
    challenge_list = []
    for challenge in challenges:
        challenge.reward = time_format(challenge.reward)
        challenge_list.append(challenge)
    return render(request, 'webapp/challenges.html', {'event': event, 'challenges': challenge_list})


def challenge_detail(request, challenge_id):
    # Try to get the challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    reward = time_format(challenge.reward)
    return render(request, 'webapp/challenge_detail.html', {'challenge': challenge, 'reward': reward})


# Allows an administrator to add a challenge
@login_required
def add_challenge(request, event_id):
    # Get event
    event = get_object_or_404(Event, pk=event_id)

    # Handle new challenge
    if request.method == "POST":
        # Validate form
        form = ChallengeCreationForm(data=request.POST)
        if form.is_valid():
            # Get form data
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            reward = form.cleaned_data['reward']

            # Create a new challenge
            challenge = Challenge(event_id=event_id, title=title, description=description, reward=reward)
            challenge.save()

            return render(request, 'webapp/admin/add_challenge.html', {'event': event, 'is_valid': True})

        # If the data is invalid
        else:
            return render(request, 'webapp/admin/add_challenge.html', {'event': event_id, 'is_valid': False})

    # Show new challenge form
    else:
        # Get form
        form = ChallengeCreationForm()
        return render(request, 'webapp/admin/add_challenge.html', {'event': event, 'form': form})


# Allows an administrator to edit a challenge
@login_required
def edit_challenge(request, challenge_id):
    # Get the challenge
    challenge = get_object_or_404(Challenge, pk=challenge_id)

    # If an edit was posted
    if request.method == "POST":
        # Check for valid data
        form = ChallengeCreationForm(data=request.POST, instance=challenge)
        if form.is_valid():
            # Edit challenge
            challenge.title = form.cleaned_data["title"]
            challenge.description = form.cleaned_data["description"]
            challenge.reward = form.cleaned_data["reward"]
            challenge.save()
            return render(request, 'webapp/admin/add_challenge.html',
                          {'edit': True, 'is_valid': True, 'challenge': challenge})

        # Invalid data
        else:
            return render(request, 'webapp/admin/add_challenge.html',
                          {'edit': True, 'is_valid': False, 'challenge': challenge})
    # Show the edit form
    else:
        form = ChallengeCreationForm(instance=challenge)
        reward = time_format(challenge.reward)
        return render(request, 'webapp/admin/add_challenge.html',
                      {'form': form, 'reward': reward, 'edit': True, 'challenge': challenge})


# Allows the superuser to delete a sub-destination
@login_required
def delete_challenge(request):
    if request.method == "POST":
        # Check if the POST data is valid
        form = IdForm(data=request.POST)
        if form.is_valid():
            # Get the sub-destination ID
            challenge_id = form.cleaned_data['id']
            # Check if the sub-destination exists
            challenge = Challenge.objects.filter(pk=challenge_id)
            if challenge:
                # Get challenge
                challenge = Challenge.objects.get(pk=challenge_id)

                # Delete associated team challenges
                TeamChallenge.objects.filter(challenge_id=challenge_id).delete()
                # Delete challenge
                challenge.delete()

                return HttpResponse(status=HTTP_200_OK)

            # The sub-destination doesn't exist
            else:
                return HttpResponse(status=HTTP_404_NOT_FOUND)

        # The provided ID is not valid
        else:
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
    # Not a POST request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
