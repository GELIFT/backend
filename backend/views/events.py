from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView

from backend.serializers import EmergencyContactSerializer
from webapp.models import Event, Location, SubLocation

User = get_user_model()


class ActiveEventView(APIView):
    """
    API endpoint for getting the active event\n
    Allowed methods: GET\n
    Possible HTTP responses:\n
        - HTTP 200: On successful request
        - HTTP 404: When no event is marked as active
        - HTTP 405: On POST/PUT/DELETE requests
    :return:\n
        - id: active event ID
        - title: active event title
        - start_date: active event starting date
        - end_date: active event ending date
        - start_location: active event starting location
            - id: starting location ID
            - latitude: starting location latitude
            - longitude: starting location longitude
        - end_location: active event ending location
            - id: ending location ID
            - latitude: ending location latitude
            - longitude: ending location longitude
        - emergency_contact: The phone number of the person to call in case of a problem
        - sub_destinations: list of all sub-destination of the active event
            - id: sub-destination ID
            - latitude: sub-destination latitude
            - longitude: sub-destination longitude
    """

    def get(self, request):

        # Only get active event
        event = Event.objects.filter(is_active=True)
        if event:
            event = Event.objects.get(is_active=True)

            # Get locations (start, end, sub-destinations)
            start_location = Location.objects.get(pk=event.start_location.pk)
            end_location = Location.objects.get(pk=event.end_location.pk)

            # Get start and end location detailed info
            start_location = dict(id=start_location.pk, latitude=start_location.latitude,
                                  longitude=start_location.longitude, name=event.start_city)
            end_location = dict(id=end_location.pk, latitude=end_location.latitude,
                                longitude=end_location.longitude, name=event.end_city)

            sub_destinations = []

            sub_dest_db = SubLocation.objects.filter(event_id=event.pk).order_by('order')

            # Fetch all sub-destinations with eventID = active event
            for sub_dest in sub_dest_db:
                location = Location.objects.get(pk=sub_dest.location_id)
                data = dict(id=sub_dest.location_id, latitude=location.latitude, longitude=location.longitude,
                            name=sub_dest.city, order=sub_dest.order)
                sub_destinations.append(data)

            # Put all data for the active event in a dictionary
            data = dict(id=event.id, title=event.title, start_date=event.start_date, end_date=event.end_date,
                        emergency_contact=event.emergency_contact,
                        start_location=start_location, end_location=end_location,
                        sub_destinations=sub_destinations)

            return Response(data)
        # If no active event is found, return 404
        else:
            return Response(status=HTTP_404_NOT_FOUND)


class EmergencyContactView(APIView):
    """
       API endpoint allowing an administrator to change the emergency contact information
       Allowed methods: POST\n
       Fields:\n
           - emergency_contact: Phone number of the person to call in case of emergency
       Possible HTTP responses:\n
           - HTTP 200: On successful request
           - HTTP 400: On invalid POST data
           - HTTP 401: When unauthorized
           - HTTP 403: When the requesting user is not an administrator
           - HTTP 404: When there is no active event
           - HTTP 405: On GET/PUT/DELETE requests
       """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # Check for permission
        if self.request.user.is_staff:
            # Check for active event
            event = Event.objects.filter(is_active=True)
            if event:
                # Get event
                event = Event.objects.get(is_active=True)
                # Check POST data
                serializer = EmergencyContactSerializer(data=request.data)
                if serializer.is_valid():
                    # Get data
                    emergency_contact = serializer.validated_data["emergency_contact"]
                    # Update event in database
                    event.emergency_contact = emergency_contact
                    event.save()

                    return Response(status=HTTP_200_OK)

                # Invalid POST data
                else:
                    return Response(status=HTTP_400_BAD_REQUEST)
            # No active event
            else:
                return Response(status=HTTP_404_NOT_FOUND)
        # The user is not an administrator
        else:
            return Response(status=HTTP_403_FORBIDDEN)
