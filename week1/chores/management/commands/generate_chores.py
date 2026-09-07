from django.core.management.base import BaseCommand
from chores.services import generate_occurrences


class Command(BaseCommand):
    help = "Generate due recurring chores and the next future occurrence."

    def handle(self, *args, **options):
        generate_occurrences()
        self.stdout.write(self.style.SUCCESS("Recurring chores are up to date."))
