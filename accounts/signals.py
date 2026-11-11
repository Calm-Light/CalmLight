from django.contrib import messages
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in)
def welcome_message(sender, request, user, **kwargs):
    # Signup adds its own message; only greet on a normal login.
    if request is not None and request.path != "/signup/":
        messages.success(request, f"Logged in as {user.username}.", fail_silently=True)


@receiver(user_logged_out)
def goodbye_message(sender, request, user, **kwargs):
    if request is not None:
        messages.info(request, "You have been logged out.", fail_silently=True)
