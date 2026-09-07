from django.utils import timezone
from .models import Chore, Schedule


def generate_occurrences(today=None):
    """Keep every scheduled occurrence through today plus the next future one.

    Dates always derive from the original anchor. Unique constraints make
    repeated or simultaneous board visits safe from duplicate occurrences.
    """
    today = today or timezone.localdate()
    for schedule in Schedule.objects.all():
        index = 0
        dates = []
        while True:
            due = schedule.date_at(index)
            dates.append(due)
            if due > today:
                break
            index += 1
        existing = set(schedule.chore_set.values_list("due_date", flat=True))
        Chore.objects.bulk_create([
            Chore(title=schedule.title, description=schedule.description, due_date=due, schedule=schedule)
            for due in dates if due not in existing
        ], ignore_conflicts=True)
