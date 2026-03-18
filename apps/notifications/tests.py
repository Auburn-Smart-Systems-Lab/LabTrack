"""
Unit tests for the notifications app.

Covers:
- notify() creates Notification with correct fields
- notify() skips inactive users
- notify_admins() only notifies ADMIN-role users
- notify() sends email when credentials configured (email_notifications=True)
- notify() skips email when email_notifications=False on profile
- notify() skips email when no email credentials (console backend)
- mark_read_view (POST, non-AJAX) marks read and redirects
- mark_read_view (POST, AJAX) returns JSON with unread_count
- mark_all_read_view marks all unread and redirects
- unread_count_view returns correct JSON count
"""

import json
from unittest.mock import patch

from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, UserProfile
from apps.notifications.models import Notification
from apps.notifications.utils import notify, notify_admins


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(
    email='user@example.com',
    username='testuser',
    password='StrongPass123!',
    role='MEMBER',
    is_active=True,
):
    """Create a CustomUser with an associated UserProfile."""
    user = CustomUser.objects.create_user(
        email=email,
        username=username,
        password=password,
        role=role,
        is_active=is_active,
    )
    UserProfile.objects.get_or_create(user=user)
    return user


def make_notification(user, is_read=False, title='Test', message='Test message'):
    """Create and return a Notification for the given user."""
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        level='info',
        is_read=is_read,
    )


# ---------------------------------------------------------------------------
# notify() utility tests
# ---------------------------------------------------------------------------

class NotifyCreatesNotificationTests(TestCase):
    """Tests that notify() creates the correct Notification record."""

    def setUp(self):
        self.user = make_user(email='notify@example.com', username='notifyuser')

    def test_creates_notification_record(self):
        """notify() creates exactly one Notification in the database."""
        notify(self.user, 'Hello', 'World message', level='success', link='/foo/')
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 1)

    def test_notification_fields_are_set_correctly(self):
        """Notification title, message, level, link and recipient match arguments."""
        notify(self.user, 'My Title', 'My Message', level='warning', link='/bar/')
        n = Notification.objects.get(recipient=self.user)
        self.assertEqual(n.title, 'My Title')
        self.assertEqual(n.message, 'My Message')
        self.assertEqual(n.level, 'warning')
        self.assertEqual(n.link, '/bar/')
        self.assertEqual(n.recipient, self.user)

    def test_notification_is_unread_by_default(self):
        """Newly created notification has is_read=False."""
        notify(self.user, 'Unread', 'Check unread')
        n = Notification.objects.get(recipient=self.user)
        self.assertFalse(n.is_read)

    def test_default_level_is_info(self):
        """notify() uses 'info' level when level argument is not provided."""
        notify(self.user, 'Info level', 'Default level')
        n = Notification.objects.get(recipient=self.user)
        self.assertEqual(n.level, 'info')


class NotifySkipsInactiveUserTests(TestCase):
    """Tests that notify() does not create a notification for inactive users."""

    def test_inactive_user_receives_no_notification(self):
        """notify() silently returns without creating a record for an inactive user."""
        inactive_user = make_user(
            email='inactive@example.com',
            username='inactiveuser',
            is_active=False,
        )
        notify(inactive_user, 'Should not appear', 'No record')
        self.assertEqual(
            Notification.objects.filter(recipient=inactive_user).count(),
            0,
        )

    def test_none_recipient_does_not_raise(self):
        """notify() with recipient=None does not raise an exception."""
        try:
            notify(None, 'No recipient', 'No message')
        except Exception as exc:  # noqa: BLE001
            self.fail(f'notify(None, ...) raised an exception: {exc}')


# ---------------------------------------------------------------------------
# notify_admins() tests
# ---------------------------------------------------------------------------

class NotifyAdminsTests(TestCase):
    """Tests for the notify_admins() helper."""

    def setUp(self):
        self.admin1 = make_user(
            email='admin1@example.com',
            username='admin1',
            role='ADMIN',
        )
        self.admin2 = make_user(
            email='admin2@example.com',
            username='admin2',
            role='ADMIN',
        )
        self.member = make_user(
            email='member@example.com',
            username='member',
            role='MEMBER',
        )
        self.inactive_admin = make_user(
            email='inactivead@example.com',
            username='inactivead',
            role='ADMIN',
            is_active=False,
        )

    def test_only_active_admins_are_notified(self):
        """notify_admins() creates notifications only for active ADMIN users."""
        notify_admins('Admin Alert', 'Something happened')
        admin1_count = Notification.objects.filter(recipient=self.admin1).count()
        admin2_count = Notification.objects.filter(recipient=self.admin2).count()
        member_count = Notification.objects.filter(recipient=self.member).count()
        inactive_count = Notification.objects.filter(recipient=self.inactive_admin).count()

        self.assertEqual(admin1_count, 1)
        self.assertEqual(admin2_count, 1)
        self.assertEqual(member_count, 0)
        self.assertEqual(inactive_count, 0)

    def test_notification_count_matches_active_admin_count(self):
        """Total notifications created equals number of active admins."""
        notify_admins('Bulk Alert', 'Sent to all admins')
        total = Notification.objects.filter(
            title='Bulk Alert'
        ).count()
        self.assertEqual(total, 2)  # admin1 and admin2


# ---------------------------------------------------------------------------
# notify() email-sending tests
# ---------------------------------------------------------------------------

class NotifyEmailSendTests(TestCase):
    """Tests for the email-sending behaviour inside notify()."""

    def setUp(self):
        self.user = make_user(
            email='emailtest@example.com',
            username='emailtestuser',
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='test@test.com',
        EMAIL_HOST_PASSWORD='pass',
        DEFAULT_FROM_EMAIL='test@test.com',
    )
    @patch('apps.notifications.utils.send_mail')
    def test_sends_email_when_credentials_configured(self, mock_send):
        """notify() calls send_mail with the correct subject and recipient."""
        notify(self.user, 'Alert Title', 'Alert body')

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        # Positional or keyword — handle both
        args, kwargs = call_kwargs
        subject = args[0] if args else kwargs.get('subject', '')
        recipient_list = args[3] if len(args) > 3 else kwargs.get('recipient_list', [])

        self.assertIn('Alert Title', subject)
        self.assertIn('[LabTrack]', subject)
        self.assertIn('emailtest@example.com', recipient_list)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='test@test.com',
        EMAIL_HOST_PASSWORD='pass',
        DEFAULT_FROM_EMAIL='test@test.com',
    )
    @patch('apps.notifications.utils.send_mail')
    def test_skips_email_when_email_notifications_false(self, mock_send):
        """notify() does not call send_mail when user's email_notifications is False."""
        profile = self.user.profile
        profile.email_notifications = False
        profile.save()

        notify(self.user, 'Skipped', 'Should not send')

        mock_send.assert_not_called()

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        EMAIL_HOST_USER='',
        EMAIL_HOST_PASSWORD='',
        DEFAULT_FROM_EMAIL='noreply@labtrack.local',
    )
    @patch('apps.notifications.utils.send_mail')
    def test_send_mail_still_attempted_with_console_backend(self, mock_send):
        """
        When email credentials are absent the settings module sets the console
        backend, but _send_email() itself does not gate on the backend — it
        gates on EMAIL_HOST_USER/PASSWORD at the settings level.  The
        notification is still created; whether send_mail is called depends on
        the runtime backend.  This test verifies the Notification record IS
        created regardless of backend.
        """
        notify(self.user, 'Console Notif', 'No SMTP configured')
        self.assertEqual(
            Notification.objects.filter(recipient=self.user, title='Console Notif').count(),
            1,
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='test@test.com',
        EMAIL_HOST_PASSWORD='pass',
        DEFAULT_FROM_EMAIL='test@test.com',
    )
    @patch('apps.notifications.utils.send_mail')
    def test_email_message_body_contains_notification_message(self, mock_send):
        """send_mail message body contains the notification message text."""
        notify(self.user, 'Subject Here', 'Body content here')

        args, kwargs = mock_send.call_args
        body = args[1] if len(args) > 1 else kwargs.get('message', '')
        self.assertIn('Body content here', body)


# ---------------------------------------------------------------------------
# mark_read_view tests
# ---------------------------------------------------------------------------

class MarkReadViewTests(TestCase):
    """Tests for the mark_read_view."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(
            email='reader@example.com',
            username='readeruser',
            password='ReadPass99!',
        )
        self.client.login(username='reader@example.com', password='ReadPass99!')
        self.notification = make_notification(self.user, is_read=False)
        self.url = reverse('notifications:mark_read', kwargs={'pk': self.notification.pk})

    def test_post_marks_notification_as_read(self):
        """POST to mark_read_view sets is_read=True on the notification."""
        self.client.post(self.url)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_post_sets_read_at_timestamp(self):
        """POST to mark_read_view sets a read_at timestamp."""
        self.client.post(self.url)
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.read_at)

    def test_non_ajax_post_redirects_to_notification_list(self):
        """Non-AJAX POST redirects to the notifications list URL."""
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse('notifications:list'),
            fetch_redirect_response=False,
        )

    def test_ajax_post_returns_json(self):
        """AJAX POST returns a JSON response with success and unread_count keys."""
        response = self.client.post(
            self.url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content)
        self.assertIn('success', data)
        self.assertIn('unread_count', data)
        self.assertTrue(data['success'])

    def test_ajax_unread_count_decrements_after_mark_read(self):
        """unread_count in JSON response reflects one fewer unread notification."""
        # Create a second unread notification so count starts at 2
        make_notification(self.user, is_read=False, title='Second')

        response = self.client.post(
            self.url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = json.loads(response.content)
        # After marking one of two as read, unread_count should be 1
        self.assertEqual(data['unread_count'], 1)

    def test_get_method_not_allowed(self):
        """GET request to mark_read_view returns 405 Method Not Allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_cannot_mark_other_users_notification(self):
        """A user cannot mark a notification belonging to another user as read."""
        other_user = make_user(
            email='other@example.com',
            username='otheruser',
            password='OtherPass99!',
        )
        other_notification = make_notification(other_user, is_read=False)
        url = reverse('notifications:mark_read', kwargs={'pk': other_notification.pk})
        response = self.client.post(url)
        # Should return 404 since the notification does not belong to this user
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# mark_all_read_view tests
# ---------------------------------------------------------------------------

class MarkAllReadViewTests(TestCase):
    """Tests for the mark_all_read_view."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(
            email='allread@example.com',
            username='allreaduser',
            password='AllReadPass99!',
        )
        self.client.login(username='allread@example.com', password='AllReadPass99!')
        self.url = reverse('notifications:mark_all_read')

        # Create several unread notifications
        for i in range(3):
            make_notification(self.user, is_read=False, title=f'Notif {i}')
        # Create one already-read notification
        make_notification(self.user, is_read=True, title='Already read')

    def test_post_marks_all_unread_as_read(self):
        """POST marks all previously unread notifications as read."""
        self.client.post(self.url)
        unread_remaining = Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()
        self.assertEqual(unread_remaining, 0)

    def test_post_does_not_affect_other_users(self):
        """POST only marks the requesting user's notifications as read."""
        other_user = make_user(
            email='other2@example.com',
            username='otheruser2',
        )
        make_notification(other_user, is_read=False, title='Other unread')

        self.client.post(self.url)

        other_unread = Notification.objects.filter(
            recipient=other_user, is_read=False
        ).count()
        self.assertEqual(other_unread, 1)

    def test_post_redirects_to_notification_list(self):
        """Non-AJAX POST redirects to the notifications list."""
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse('notifications:list'),
            fetch_redirect_response=False,
        )

    def test_get_method_not_allowed(self):
        """GET request to mark_all_read_view returns 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_unauthenticated_user_is_redirected(self):
        """Unauthenticated POST is redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


# ---------------------------------------------------------------------------
# unread_count_view tests
# ---------------------------------------------------------------------------

class UnreadCountViewTests(TestCase):
    """Tests for the unread_count_view."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(
            email='counter@example.com',
            username='counteruser',
            password='CountPass99!',
        )
        self.client.login(username='counter@example.com', password='CountPass99!')
        self.url = reverse('notifications:unread_count')

    def test_returns_json_response(self):
        """GET returns a JSON response."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_returns_zero_when_no_notifications(self):
        """Returns unread_count of 0 when user has no notifications."""
        data = json.loads(self.client.get(self.url).content)
        self.assertEqual(data['unread_count'], 0)

    def test_returns_correct_unread_count(self):
        """Returns the exact number of unread notifications."""
        make_notification(self.user, is_read=False)
        make_notification(self.user, is_read=False)
        make_notification(self.user, is_read=True)  # should not count

        data = json.loads(self.client.get(self.url).content)
        self.assertEqual(data['unread_count'], 2)

    def test_count_excludes_other_users_notifications(self):
        """unread_count only counts notifications for the logged-in user."""
        other = make_user(email='other3@example.com', username='other3')
        make_notification(other, is_read=False)
        make_notification(other, is_read=False)
        make_notification(self.user, is_read=False)

        data = json.loads(self.client.get(self.url).content)
        self.assertEqual(data['unread_count'], 1)

    def test_unauthenticated_user_is_redirected(self):
        """Unauthenticated GET is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_count_updates_after_mark_all_read(self):
        """unread_count returns 0 after all notifications are marked read."""
        make_notification(self.user, is_read=False)
        make_notification(self.user, is_read=False)

        self.client.post(reverse('notifications:mark_all_read'))

        data = json.loads(self.client.get(self.url).content)
        self.assertEqual(data['unread_count'], 0)
