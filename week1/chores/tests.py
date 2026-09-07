from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Chore, Partner, Schedule
from .services import generate_occurrences


class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alex = get_user_model().objects.create_user(username='alex', password='test-password')
        cls.sam = get_user_model().objects.create_user(username='sam', password='test-password')
        cls.partner = Partner.objects.create(slot=1, user=cls.alex)
        Partner.objects.create(slot=2, user=cls.sam)

    def setUp(self):
        self.client.force_login(self.alex)
        self.chore = Chore.objects.create(title='Wash dishes', due_date=timezone.localdate() - timedelta(days=1))

    def action(self, action):
        return self.client.post(reverse('chore_action', args=[self.chore.pk, action]))

    def test_sign_in_and_shared_board(self):
        self.client.logout()
        self.assertRedirects(self.client.get('/'), '/accounts/login/?next=/')
        response = self.client.post('/accounts/login/', {'username': 'alex', 'password': 'test-password'}, follow=True)
        self.assertContains(response, 'Wash dishes')
        self.client.force_login(self.sam)
        self.assertContains(self.client.get('/'), 'Wash dishes')

    def test_non_partner_cannot_access_board_or_mutate(self):
        outsider = get_user_model().objects.create_user(username='outsider')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get('/').status_code, 403)
        self.assertEqual(self.action('claim').status_code, 403)
        self.assertEqual(self.client.post('/chores/new/', {}).status_code, 403)

    def test_required_due_date_and_one_off_creation(self):
        response = self.client.post('/chores/new/', {'title': 'Vacuum'})
        self.assertContains(response, 'This field is required.')
        self.assertFalse(Chore.objects.filter(title='Vacuum').exists())
        response = self.client.post('/chores/new/', {'title': 'Vacuum', 'due_date': '2026-09-10'})
        self.assertRedirects(response, '/')
        self.assertIsNone(Chore.objects.get(title='Vacuum').schedule)

    def test_claim_is_exclusive_and_overdue_owner_stays(self):
        self.action('claim')
        self.client.force_login(self.sam)
        response = self.action('claim')
        self.assertRedirects(response, '/')
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.owner, self.partner)
        self.assertTrue(self.chore.is_overdue)
        self.assertEqual(self.chore.status, Chore.Status.CLAIMED)

    def test_only_owner_can_complete_or_release(self):
        self.action('claim')
        self.client.force_login(self.sam)
        self.action('release')
        self.action('complete')
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.status, Chore.Status.CLAIMED)
        self.client.force_login(self.alex)
        self.action('release')
        self.chore.refresh_from_db()
        self.assertIsNone(self.chore.owner)
        self.assertEqual(self.chore.status, Chore.Status.AVAILABLE)
        self.action('claim')
        self.action('complete')
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.status, Chore.Status.DONE)
        self.assertIsNotNone(self.chore.completed_at)
        self.assertFalse(self.chore.is_overdue)
        self.assertContains(self.client.get('/'), 'Completed by')

    def test_available_chore_cannot_be_completed_directly(self):
        self.action('complete')
        self.chore.refresh_from_db()
        self.assertEqual(self.chore.status, Chore.Status.AVAILABLE)

    def test_actions_require_post_and_csrf(self):
        url = reverse('chore_action', args=[self.chore.pk, 'claim'])
        self.assertEqual(self.client.get(url).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alex)
        self.assertEqual(client.post(url).status_code, 403)

    def test_title_is_escaped(self):
        self.chore.title = '<script>alert(1)</script>'
        self.chore.save()
        self.assertContains(self.client.get('/'), '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_recurring_form_generates_occurrences(self):
        today = timezone.localdate()
        self.client.post('/chores/new/', {'title': 'Laundry', 'due_date': today.isoformat(), 'recurrence': 'weekly'})
        self.assertEqual(list(Chore.objects.filter(title='Laundry').values_list('due_date', flat=True)), [today, today + timedelta(days=7)])

    def test_only_two_partner_slots(self):
        outsider = get_user_model().objects.create_user(username='third')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Partner.objects.create(slot=3, user=outsider)


class RecurrenceTests(TestCase):
    def test_catch_up_keeps_unfinished_and_is_idempotent(self):
        schedule = Schedule.objects.create(title='Laundry', start_date=date(2026, 9, 1), frequency='weekly')
        generate_occurrences(date(2026, 9, 16))
        generate_occurrences(date(2026, 9, 16))
        self.assertEqual(list(schedule.chore_set.values_list('due_date', flat=True)), [date(2026, 9, day) for day in (1, 8, 15, 22)])
        self.assertEqual(schedule.chore_set.filter(status='available').count(), 4)

    def test_month_end_returns_to_original_day(self):
        schedule = Schedule.objects.create(title='Deep clean', start_date=date(2028, 1, 31), frequency='monthly')
        generate_occurrences(date(2028, 3, 1))
        self.assertEqual(list(schedule.chore_set.values_list('due_date', flat=True)), [date(2028, 1, 31), date(2028, 2, 29), date(2028, 3, 31)])

    def test_daily_and_future_start(self):
        schedule = Schedule.objects.create(title='Dishes', start_date=date(2026, 9, 5), frequency='daily')
        generate_occurrences(date(2026, 9, 1))
        self.assertEqual(schedule.chore_set.count(), 1)
        generate_occurrences(date(2026, 9, 7))
        self.assertEqual(list(schedule.chore_set.values_list('due_date', flat=True)), [date(2026, 9, day) for day in (5, 6, 7, 8)])

    def test_late_completion_does_not_move_schedule(self):
        user = get_user_model().objects.create_user(username='alex')
        partner = Partner.objects.create(slot=1, user=user)
        schedule = Schedule.objects.create(title='Laundry', start_date=date(2026, 9, 1), frequency='weekly')
        generate_occurrences(date(2026, 9, 10))
        first = schedule.chore_set.first()
        first.owner = partner
        first.status = 'done'
        first.completed_at = timezone.now()
        first.save()
        generate_occurrences(date(2026, 9, 16))
        self.assertEqual(list(schedule.chore_set.values_list('due_date', flat=True)), [date(2026, 9, day) for day in (1, 8, 15, 22)])
        self.assertEqual(schedule.chore_set.get(pk=first.pk).status, 'done')


class SetupTests(TestCase):
    @patch('chores.management.commands.setup_household.getpass', return_value='Safe-house-password-42!')
    @patch('builtins.input', side_effect=['alex', 'sam'])
    def test_setup_creates_two_accounts_and_refuses_rerun(self, input_mock, password_mock):
        call_command('setup_household', stdout=StringIO())
        self.assertEqual(Partner.objects.count(), 2)
        self.assertTrue(get_user_model().objects.get(username='alex').check_password('Safe-house-password-42!'))
        with self.assertRaises(CommandError):
            call_command('setup_household')

    @patch('chores.management.commands.setup_household.getpass', return_value='Safe-house-password-42!')
    @patch('builtins.input', side_effect=['alex', 'alex'])
    def test_invalid_setup_does_not_leave_partial_accounts(self, input_mock, password_mock):
        with self.assertRaises(CommandError):
            call_command('setup_household')
        self.assertEqual(get_user_model().objects.count(), 0)
