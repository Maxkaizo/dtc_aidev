from django import forms
from .models import Schedule


class ChoreForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    due_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    recurrence = forms.ChoiceField(choices=[("", "One-off chore"), *Schedule.Frequency.choices], required=False)
