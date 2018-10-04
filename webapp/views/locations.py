from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, \
    HTTP_405_METHOD_NOT_ALLOWED

from webapp.forms import IdForm, SubLocationCoordinatesForm, SubLocationCityForm, SubLocationOrderForm, LocationForm
from webapp.models import Event, Location, SubLocation

maps_key = settings.GMAPS_API_KEY

@login_required
def add_sublocation(request):
    # Check for permission
    if request.user.is_superuser:
        if request.method == "POST":
            # Check for valid input
            form = IdForm(data=request.POST)
            if form.is_valid():
                # Retrieve data
                id = form.cleaned_data["id"]
                event = Event.objects.filter(pk=id)
                if event:
                    # Create a new location
                    location = Location()
                    # Give it Eindhoven coordinates (arbitrary)
                    location.latitude = 51.43
                    location.longitude = 5.47
                    location.save()
                    # Create a new sub-destination and return it
                    sublocation = SubLocation()
                    sublocation.location_id = location.pk
                    sublocation.event_id = id
                    sublocation.city = "Eindhoven"

                    # Retrieve the order of the last sub-destination for the event
                    last_sublocation = SubLocation.objects.filter(event_id=id)
                    if last_sublocation:
                        last_sublocation = SubLocation.objects.filter(event_id=id).order_by('-order')[0]
                        sublocation.order = last_sublocation.order + 1
                    else:
                        sublocation.order = 1

                    sublocation.save()

                    return HttpResponse(status=HTTP_200_OK)
                # Event does not exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # The POST data is invalid
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # The request is not a POST request
        else:
            return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
    # The user is not the superuser
    else:
        return HttpResponse(status=HTTP_403_FORBIDDEN)


@login_required
def edit_sublocation(request, event_id):
    if request.user.is_superuser:
        # Check if event exists
        event = get_object_or_404(Event, pk=event_id)
        # Get associated sub-destinations
        sublocation_details = []
        sub_locations = SubLocation.objects.filter(event_id=event_id).order_by('order')
        for subloc in sub_locations:
            # Get location details
            location = Location.objects.get(pk=subloc.location_id)
            location.latitude = round(location.latitude, 2)
            location.longitude = round(location.longitude, 2)
            data = dict(sub_location=subloc, location=location)
            sublocation_details.append(data)

        return render(request, 'webapp/admin/edit_sublocations.html',
                      {'event': event_id, 'event_title': event.title, 'data': sublocation_details,
                       'gmaps_key': maps_key})
    else:
        return redirect('login')


# Allows the superuser to change the coordinates of a sub-destination
@login_required
def edit_sublocation_coordinates(request):
    # Check for permission
    if request.user.is_superuser:
        # Check for request type
        if request.method == "POST":
            # Check for valid data
            form = SubLocationCoordinatesForm(data=request.POST)
            if form.is_valid():
                # Retrieve data
                id = form.cleaned_data["id"]
                latitude = form.cleaned_data["latitude"]
                longitude = form.cleaned_data["longitude"]
                coordinates = [latitude, longitude]

                # Check if sub-destination exists in database
                sublocation = SubLocation.objects.filter(pk=id)
                if sublocation:
                    # Get sub-destination
                    sublocation = SubLocation.objects.get(pk=id)
                    location = Location.objects.get(pk=sublocation.location_id)

                    # Save
                    location.latitude = latitude
                    location.longitude = longitude

                    location.save()
                    sublocation.save()
                    return HttpResponse(status=HTTP_200_OK)
                # Sub-destination not found
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # Invalid POST data
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # The request is not a POST request
        else:
            return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
    # If the user is not the superuser
    else:
        return HttpResponse(status=HTTP_403_FORBIDDEN)


# Allows the superuser to change the city of a sub-destination
@login_required
def edit_sublocation_city(request):
    # Check for permission
    if request.user.is_superuser:
        # Check for request type
        if request.method == "POST":
            # Check for valid data
            form = SubLocationCityForm(data=request.POST)
            if form.is_valid():
                # Retrieve data
                id = form.cleaned_data["id"]
                city = form.cleaned_data["city"]

                # Check if sub-destination exists in database
                sublocation = SubLocation.objects.filter(pk=id)
                if sublocation:
                    # Get sub-destination
                    sublocation = SubLocation.objects.get(pk=id)

                    # Save changes
                    sublocation.city = city
                    sublocation.save()

                    return HttpResponse(city, status=HTTP_200_OK)
                # Sub-destination not found
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # Invalid POST data
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # The request is not a POST request
        else:
            return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
    # If the user is not the superuser
    else:
        return HttpResponse(status=HTTP_403_FORBIDDEN)


# Allows the superuser to modify the order of the sub-destinations
@login_required
def edit_sublocation_order(request):
    if request.method == "POST":
        # Check if the user is the superuser
        if request.user.is_superuser:
            # Check if the POST data is valid
            form = SubLocationOrderForm(data=request.POST)
            if form.is_valid():
                # Get the data
                sublocation_id = form.cleaned_data['sublocation_id']
                event_id = form.cleaned_data['event_id']
                # Check if the event and the sub-destination exist
                event = Event.objects.filter(pk=event_id)
                sub_destination = SubLocation.objects.filter(pk=sublocation_id)
                if event and sub_destination:

                    # Get the new order from the POST data
                    new_order = request.POST.getlist('order[]')

                    # For each sub-destination
                    for location in new_order:
                        sublocation_id = location
                        sublocation_order = new_order.index(location)

                        # Retrieve sub-destination and modify it
                        try:
                            sublocation = SubLocation.objects.get(pk=sublocation_id)
                            sublocation.order = sublocation_order + 1
                            sublocation.save()
                        except SubLocation.DoesNotExist:
                            pass

                    return HttpResponse(status=HTTP_200_OK)

                # The event doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)

            # The provided ID is not valid
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # Requesting user is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    # Not a GET request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows the superuser to delete a sub-destination
@login_required
def delete_event_sublocation(request):
    if request.method == "POST":
        # Check if the user is the superuser
        if request.user.is_superuser:
            # Check if the POST data is valid
            form = IdForm(data=request.POST)
            if form.is_valid():
                # Get the sub-destination ID
                sublocation_id = form.cleaned_data['id']
                # Check if the sub-destination exists
                sub_destination = SubLocation.objects.filter(pk=sublocation_id)
                if sub_destination:
                    # Get sub-destination
                    sub_destination = SubLocation.objects.get(pk=sublocation_id)
                    # Retrieve the other sub-destinations
                    sub_locations = SubLocation.objects.filter(event_id=sub_destination.event_id)

                    # Update the order for the other sub-destinations
                    for location in sub_locations:
                        if location.order > sub_destination.order:
                            location.order = location.order - 1
                            location.save()

                    # Delete sub-destination
                    sub_destination.delete()

                    return HttpResponse(status=HTTP_200_OK)

                # The sub-destination doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)

            # The provided ID is not valid
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # Requesting user is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    # Not a GET request
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows to create a location
@login_required
def add_location(request):
    # Check for permission
    if request.user.is_superuser:
        # Check for POST data
        if request.method == "POST":
            # Check validity of data
            form = LocationForm(data=request.POST)
            if form.is_valid():
                # Get POST data
                latitude = form.cleaned_data["latitude"]
                longitude = form.cleaned_data["longitude"]

                # Create new location
                location = Location()
                location.latitude = latitude
                location.longitude = longitude
                location.save()

                return HttpResponse(location.pk, status=HTTP_200_OK)
            # Invalid POST data
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # No POST data
        else:
            return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
    # User is not superuser
    else:
        return HttpResponse(status=HTTP_403_FORBIDDEN)
