from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChoreForm
from .models import Chore, Partner, Schedule
from .services import generate_occurrences


def partner_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            request.partner = Partner.objects.get(user=request.user)
        except Partner.DoesNotExist:
            raise PermissionDenied("This account is not one of the household's two partners.")
        return view(request, *args, **kwargs)
    return wrapped


@partner_required
def board(request):
    generate_occurrences()
    chores = Chore.objects.select_related("owner__user", "schedule")
    columns = [(label, chores.filter(status=value)) for value, label in Chore.Status.choices]
    return render(request, "chores/board.html", {"columns": columns, "today": timezone.localdate()})


@partner_required
def create_chore(request):
    form = ChoreForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            if data["recurrence"]:
                Schedule.objects.create(title=data["title"], description=data["description"],
                    start_date=data["due_date"], frequency=data["recurrence"])
                generate_occurrences()
            else:
                Chore.objects.create(title=data["title"], description=data["description"], due_date=data["due_date"])
        messages.success(request, "Chore added.")
        return redirect("board")
    return render(request, "chores/form.html", {"form": form})


@partner_required
@require_POST
def chore_action(request, pk, action):
    get_object_or_404(Chore, pk=pk)
    # Conditional UPDATE makes claiming atomic: only one partner can win.
    if action == "claim":
        changed = Chore.objects.filter(pk=pk, status=Chore.Status.AVAILABLE, owner=None).update(
            status=Chore.Status.CLAIMED, owner=request.partner)
    elif action == "release":
        changed = Chore.objects.filter(pk=pk, status=Chore.Status.CLAIMED, owner=request.partner).update(
            status=Chore.Status.AVAILABLE, owner=None)
    elif action == "complete":
        changed = Chore.objects.filter(pk=pk, status=Chore.Status.CLAIMED, owner=request.partner).update(
            status=Chore.Status.DONE, completed_at=timezone.now())
    else:
        raise PermissionDenied("Unknown chore action.")
    if changed:
        messages.success(request, {"claim": "Chore reserved for you.", "release": "Chore is available again.", "complete": "Chore completed. Thank you!"}[action])
    else:
        messages.error(request, "This chore changed or belongs to your partner. Check its current status.")
    return redirect("board")
