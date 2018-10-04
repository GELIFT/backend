import base64
import imghdr
import uuid

import six
from django.core.files.base import ContentFile


# Get a file extension
def get_file_extension(file_name, decoded_file):
    extension = imghdr.what(file_name, decoded_file)
    extension = "jpg" if extension == "jpeg" else extension

    return extension


# Used to decode a base64 string
def decode_base64_file(data):
    # Check if this is a base64 string
    if isinstance(data, six.string_types):
        # Check if the base64 string is in the "data:" format
        if 'data:' in data and ';base64,' in data:
            # Break out the header from the base64 content
            header, data = data.split(';base64,')

        # Try to decode the file. Return validation error if it fails.
        try:
            decoded_file = base64.b64decode(data)
        except TypeError:
            TypeError('invalid_image')

        # Generate file name:
        file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
        # Get the file name extension:
        file_extension = get_file_extension(file_name, decoded_file)

        complete_file_name = "%s.%s" % (file_name, file_extension,)

        return ContentFile(decoded_file, name=complete_file_name)


# Used to format a timedelta object to HH:MM format
def time_format(timedelta):
    negative = False
    # Take the absolute value of the number of seconds
    seconds = int(abs(timedelta.total_seconds()))
    # If the time is negative
    if timedelta.total_seconds() < 0:
        negative = True

    # Get hours and minutes
    hours = seconds // 3600
    minutes = (seconds // 60) - (hours * 60)

    # If hours < 10, add leading 0
    if hours < 10:
        hours = "0" + str(hours)

    # If minutes < 10, add leading 0
    if minutes < 10:
        minutes = "0" + str(minutes)

    # Combine hours and minutes
    time = str(hours) + ":" + str(minutes)

    # If negative time, add leading "-"
    if negative:
        time = "-" + time
    return time
