import random

from django.contrib.auth.base_user import BaseUserManager
from django.core.mail import send_mail


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, first_name, last_name, **extra_fields):
        """
        Creates and saves a new User
        :param email: user's email
        :param password: user's password
        :param extra_fields: Eventual extra fields (is_admin, is_active)
        :return: The newly created user
        """
        if not email:
            raise ValueError('The email cannot be empty.')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Send email to newly created user
        subject = 'Welcome to lifTUe!'
        message = 'Welcome to lifTUe!\n\n You can start using the application using the following credentials:\n\n' \
                  'Email: ' + email + '\n Password: ' + password + '\n\n You will need to change your password the ' \
                                                                   'first time you log in.'

        send_mail(subject, message, 'noreply@gelift.win.tue.nl', (user.email,), email)
        return user

    def create_user(self, email, first_name, last_name, **extra_fields):
        """
        Creates a new user using @_create_user()
        :param email: User's email, must be unique
        :param first_name: User's first name
        :param last_name: User's last name
        :param extra_fields: Eventual extra fields (is_staff, etc)
        :return: Result of @_create_user()
        """
        # Generate a random password the first time the user is created.
        password = ''.join([random.choice('1234567890qwertyuiopasdfghjklzxcvbnm') for i in range(8)])
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, first_name, last_name, **extra_fields)

    def create_superuser(self, email, first_name, last_name, password, **extra_fields):
        """
        Creates a superuser using @_create_user() with parameters is_superuser and is_staff set to True
        :param email: Superuser's email
        :param first_name: Superuser's first name
        :param last_name: Superuser's last name
        :param password: Superuser's password
        :param extra_fields: Eventual extra fields (is_superuser, is_staff, etc)
        :return: The newly created superuser returned by @_create_user()
        """
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, first_name, last_name, **extra_fields)
