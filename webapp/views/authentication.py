from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST, \
    HTTP_404_NOT_FOUND, HTTP_200_OK

from backend.serializers import UserSingleSerializer
from webapp.forms import LoginForm, UserCreationForm, IdForm
from webapp.models import User, UserTeam


# User list
@login_required
def user(request):
    if request.user.is_superuser:
        users = User.objects.exclude(is_superuser=True).order_by("first_name")
        return render(request, 'webapp/admin/users.html', {'users': users})
    else:
        return redirect('index')


# Allows the superuser to delete a user
@login_required
def delete_user(request):
    if request.user.is_superuser:
        if request.method == "POST":
            form = IdForm(data=request.POST)
            if form.is_valid():
                id = form.cleaned_data['id']
                user = get_object_or_404(User, pk=id)

                # Delete the teams the user is in
                UserTeam.objects.filter(user_id=user.pk).delete()
                # Delete the user
                user.delete()
                return HttpResponse(status=HTTP_200_OK)
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        else:
            return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
    else:
        return HttpResponse(status=HTTP_403_FORBIDDEN)


# Allows users to log in
def login_view(request):
    # Check if the user is already authenticated
    if not request.user.is_authenticated:
        # If a login is attempted
        if request.method == "POST":
            form = LoginForm(data=request.POST)
            # Check if the data entered in the form is valid
            if form.is_valid():

                # Get email and password
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']

                # Try to authenticate user
                user = authenticate(request, username=email, password=password)

                # If the credentials exist and are correct
                if user is not None:

                    # Check whether the user is an admin or the superuser
                    user_check = User.objects.get(email=email)
                    if user_check.is_staff or user_check.is_superuser:

                        # Login user and return template with success message
                        auth_login(request, user)
                        return render(request, 'webapp/authentication/login.html', {'success': True})

                    # Otherwise, show error message
                    else:
                        return render(request, 'webapp/authentication/login.html', {'not_admin': True})

                # If the login is not valid, show the login form again
                else:
                    form = LoginForm()
                    return render(request, 'webapp/authentication/login.html', {'form': form})

            # If the data is not valid, show the form again
            else:
                form = LoginForm()
                return render(request, 'webapp/authentication/login.html', {'form': form})

        # If there is no POST data, show the form
        else:
            form = LoginForm()
            return render(request, 'webapp/authentication/login.html', {'form': form})
    # User already authenticated
    else:
        return redirect('index')


# Allows the superuser to create new users
@login_required
def add_user(request):
    if request.user.is_superuser:
        if request.method == "POST":
            form = UserCreationForm(data=request.POST)
            if form.is_valid():
                form.save()
                return render(request, 'webapp/admin/add_user.html', {'is_valid': True})
            else:
                return render(request, 'webapp/admin/add_user.html', {'is_valid': False})
        else:
            form = UserCreationForm()
            return render(request, 'webapp/admin/add_user.html', {'form': form})
    else:
        return redirect('index')


# Allows the superuser to edit new users
@login_required
def edit_user(request, user_id):
    if request.user.is_superuser:
        # Get the user
        user = get_object_or_404(User, pk=user_id)
        # Superuser cannot be edited
        if not user.is_superuser:
            # If an edit was posted
            if request.method == "POST":
                # Check for valid data
                form = UserCreationForm(data=request.POST, instance=user)
                if form.is_valid():
                    # Edit user
                    user.email = form.cleaned_data["email"]
                    user.first_name = form.cleaned_data["first_name"]
                    user.last_name = form.cleaned_data["last_name"]
                    user.is_staff = form.cleaned_data["is_staff"]
                    user.save()
                    return render(request, 'webapp/admin/add_user.html',
                                  {'edit': True, 'is_valid': True})

                # Invalid data
                else:
                    return render(request, 'webapp/admin/add_user.html',
                                  {'edit': True, 'is_valid': False})
            # Show the edit form
            else:
                form = UserCreationForm(instance=user)
                return render(request, 'webapp/admin/add_user.html', {'form': form, 'edit': True})
        else:
            return redirect('index')
    # User does not have the right to edit users
    else:
        return redirect('login')


# Allows the superuser to edit administrators
@login_required
def administrators(request):
    if request.user.is_superuser:
        # Get all users except the superuser
        users = User.objects.exclude(is_superuser=True)
        return render(request, 'webapp/admin/edit_admins.html', {'users': users})
    else:
        return redirect('index')


# Allows the superuser to add an administrator
@login_required
def add_administrator(request):
    if request.method == "POST":
        # Check for permission
        if request.user.is_superuser:
            # Check the POST data
            serializer = UserSingleSerializer(data=request.POST)
            if serializer.is_valid():
                # Get the data
                user_id = serializer.validated_data["id"]
                # Check if the user exists
                user = User.objects.filter(pk=user_id)
                if user:
                    # Retrieve user
                    user = User.objects.get(pk=user_id)
                    # Set the user as administrator
                    user.is_staff = True
                    # Save and return
                    user.save()
                    return HttpResponse(status=HTTP_200_OK)
                # The user doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # POST data invalid
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # User is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    # Request type is not POST
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


# Allows the superuser to remove an administrator
@login_required
def remove_administrator(request):
    if request.method == "POST":
        # Check for permission
        if request.user.is_superuser:
            # Check the POST data
            serializer = UserSingleSerializer(data=request.POST)
            if serializer.is_valid():
                # Get the data
                user_id = serializer.validated_data["id"]
                # Check if the user exists
                user = User.objects.filter(pk=user_id)
                if user:
                    # Retrieve user
                    user = User.objects.get(pk=user_id)
                    # Set the user as non-administrator
                    user.is_staff = False
                    # Save and return
                    user.save()
                    return HttpResponse(status=HTTP_200_OK)
                # The user doesn't exist
                else:
                    return HttpResponse(status=HTTP_404_NOT_FOUND)
            # POST data invalid
            else:
                return HttpResponse(status=HTTP_400_BAD_REQUEST)
        # User is not the superuser
        else:
            return HttpResponse(status=HTTP_403_FORBIDDEN)
    # Request type is not POST
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)
