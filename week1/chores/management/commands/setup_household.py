from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from chores.models import Partner


class Command(BaseCommand):
    help = "Create the household's two partner accounts interactively."

    def handle(self, *args, **options):
        if Partner.objects.exists():
            raise CommandError("Household already configured. Use changepassword to reset a password.")
        User = get_user_model()
        users = []
        for slot in (1, 2):
            username = input(f"Partner {slot} username: ").strip()
            user = User(username=username)
            try:
                user.full_clean(exclude=["password"])
                if username in [u.username for u in users]:
                    raise ValidationError("Choose two different usernames.")
                password = getpass(f"Password for {username}: ")
                if password != getpass("Confirm password: "):
                    raise ValidationError("Passwords do not match.")
                validate_password(password, user)
            except ValidationError as exc:
                raise CommandError("; ".join(exc.messages)) from exc
            user.set_password(password)
            users.append(user)
        with transaction.atomic():
            for slot, user in enumerate(users, start=1):
                user.save()
                Partner.objects.create(slot=slot, user=user)
        self.stdout.write(self.style.SUCCESS("Household ready. Both partners can now sign in."))
