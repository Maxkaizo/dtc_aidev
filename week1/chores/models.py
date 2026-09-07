from calendar import monthrange
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Partner(models.Model):
    slot = models.PositiveSmallIntegerField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(slot__in=[1, 2]), name="two_partner_slots")]

    def __str__(self):
        return self.user.get_username()


class Schedule(models.Model):
    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    frequency = models.CharField(max_length=10, choices=Frequency.choices)

    def date_at(self, index):
        if self.frequency == self.Frequency.DAILY:
            return self.start_date + timedelta(days=index)
        if self.frequency == self.Frequency.WEEKLY:
            return self.start_date + timedelta(weeks=index)
        month_index = self.start_date.year * 12 + self.start_date.month - 1 + index
        year, month = divmod(month_index, 12)
        month += 1
        return self.start_date.replace(year=year, month=month, day=min(self.start_date.day, monthrange(year, month)[1]))


class Chore(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        CLAIMED = "claimed", "Claimed"
        DONE = "done", "Done"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    owner = models.ForeignKey(Partner, null=True, blank=True, on_delete=models.PROTECT)
    schedule = models.ForeignKey(Schedule, null=True, blank=True, on_delete=models.PROTECT)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["schedule", "due_date"], name="unique_schedule_occurrence"),
            models.CheckConstraint(condition=(
                Q(status="available", owner__isnull=True, completed_at__isnull=True)
                | Q(status="claimed", owner__isnull=False, completed_at__isnull=True)
                | Q(status="done", owner__isnull=False, completed_at__isnull=False)
            ), name="valid_chore_state"),
        ]

    @property
    def is_overdue(self):
        return self.status != self.Status.DONE and self.due_date < timezone.localdate()

    def __str__(self):
        return self.title
