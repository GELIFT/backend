from datetime import timedelta, datetime

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from webapp.models import Event, Challenge


class UserCreationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        del self.fields['password1']
        del self.fields['password2']

        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'

        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['is_staff'].widget.attrs['class'] = ''

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'is_staff',)

    def save(self, commit=True):
        get_user_model().objects.create_user(email=self.cleaned_data['email'],
                                             first_name=self.cleaned_data['first_name'],
                                             last_name=self.cleaned_data['last_name'],
                                             is_staff=self.cleaned_data['is_staff'])


class UserChangeForm(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        del self.fields['username']

    class Meta:
        model = get_user_model()
        fields = UserChangeForm.Meta.fields


class EventCreationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EventCreationForm, self).__init__(*args, **kwargs)

        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'

        self.fields['title'].widget.attrs['placeholder'] = 'Title'
        self.fields['start_date'].widget.attrs['placeholder'] = 'Start date'
        self.fields['end_date'].widget.attrs['placeholder'] = 'End date'
        self.fields['start_city'].widget.attrs['placeholder'] = 'Start city name'
        self.fields['end_city'].widget.attrs['placeholder'] = 'End city name'

    class Meta:
        model = Event
        fields = (
            'title', 'start_date', 'end_date', 'emergency_contact', 'is_active', 'start_city', 'end_city',
            'start_location', 'end_location')


class LoginForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'

    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())


class ChallengeCreationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ChallengeCreationForm, self).__init__(*args, **kwargs)

        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'

        self.fields['title'].widget.attrs['placeholder'] = 'Title'
        self.fields['description'].widget.attrs['placeholder'] = 'Description'
        self.fields['reward'].widget.attrs['placeholder'] = 'Reward'

    class Meta:
        model = Challenge
        fields = ('title', 'description')

    reward = forms.CharField()

    def clean_reward(self):
        reward = self.cleaned_data['reward']
        print(reward)
        reward = datetime.strptime(reward, "%H:%M")
        reward = timedelta(hours=reward.hour, minutes=reward.minute)

        return reward


class EventWinnerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(EventWinnerForm, self).__init__(*args, **kwargs)

        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'

    team_id = forms.IntegerField()
    photo = forms.ImageField(allow_empty_file=False, required=False)

# JQUERY FORMS

# Allows to edit an event (via JQuery)
class EventEditForm(forms.Form):
    title = forms.CharField(max_length=255, required=False)
    start_date = forms.DateTimeField(required=False)
    end_date = forms.DateTimeField(required=False)
    emergency_contact = forms.RegexField(regex=r'^\+?1?\d{9,15}$', required=False)


# Allows to change an event start/end location (via JQuery)
class EventLocationEditForm(forms.Form):
    latitude = forms.FloatField()
    longitude = forms.FloatField()
    location_type = forms.CharField(max_length=10)


# Allows to change the coordinates of a sub-destination
class SubLocationCoordinatesForm(forms.Form):
    id = forms.IntegerField()
    latitude = forms.FloatField()
    longitude = forms.FloatField()


# Allows to verify the input for a city name when changing it on a sub-destination
class SubLocationCityForm(forms.Form):
    id = forms.IntegerField()
    city = forms.CharField(max_length=255)


# Allows to update the order of sub-destinations
class SubLocationOrderForm(forms.Form):
    event_id = forms.IntegerField()
    sublocation_id = forms.IntegerField()


# Allows to verify the input is a number
class IdForm(forms.Form):
    id = forms.IntegerField()


# Form allowing to add/remove a user to/from a team
class UserTeamForm(forms.Form):
    user_id = forms.IntegerField()
    team_id = forms.IntegerField()
    old_team_id = forms.IntegerField(required=False)


# Form allowing to add a location
class LocationForm(forms.Form):
    latitude = forms.FloatField()
    longitude = forms.FloatField()


# Form allowing to change the city names of an event
class EventCityNameForm(forms.Form):
    event_id = forms.IntegerField()
    city_name = forms.CharField(max_length=255)
    type = forms.CharField(max_length=255)
