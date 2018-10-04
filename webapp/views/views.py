from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from webapp.models import Event, User


@login_required
def admin_dashboard(request):
    events = Event.objects.all().order_by('-start_date')[:5]
    users = User.objects.exclude(is_superuser=True).order_by('last_name')[:5]
    return render(request, 'webapp/admin/admin_dashboard.html', {'events': events, 'users': users})


def index(request):
    # Get active event
    event = Event.objects.filter(is_active=True)
    if event:
        event = Event.objects.get(is_active=True)
        return render(request, 'webapp/index.html', {'event': event})
    else:
        return render(request, 'webapp/index.html')
