"""
Unit tests for the accounts app.

Covers:
- CustomUser model properties (full_name, is_admin)
- UserProfile defaults
- login_view (GET, POST valid, POST invalid)
- profile_edit_view (saves user + profile fields, email_notifications toggle)
- password_change view (login-required redirect)
- CustomUserCreationForm (duplicate email, duplicate username)
"""

from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.forms import CustomUserCreationForm
from apps.accounts.models import CustomUser, UserProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(
    email='user@example.com',
    username='testuser',
    password='StrongPass123!',
    first_name='',
    last_name='',
    role='MEMBER',
    is_active=True,
):
    """Create and return a CustomUser with an associated profile."""
    user = CustomUser.objects.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=is_active,
    )
    UserProfile.objects.get_or_create(user=user)
    return user


# ---------------------------------------------------------------------------
# CustomUser model tests
# ---------------------------------------------------------------------------

class CustomUserFullNameTests(TestCase):
    """Tests for the CustomUser.full_name property."""

    def test_full_name_with_both_names(self):
        """full_name returns 'First Last' when both names are set."""
        user = make_user(
            email='john@example.com',
            username='johndoe',
            first_name='John',
            last_name='Doe',
        )
        self.assertEqual(user.full_name, 'John Doe')

    def test_full_name_with_first_name_only(self):
        """full_name returns just the first name when last_name is blank."""
        user = make_user(
            email='alice@example.com',
            username='alice',
            first_name='Alice',
            last_name='',
        )
        self.assertEqual(user.full_name, 'Alice')

    def test_full_name_with_last_name_only(self):
        """full_name returns just the last name when first_name is blank."""
        user = make_user(
            email='smith@example.com',
            username='smith',
            first_name='',
            last_name='Smith',
        )
        self.assertEqual(user.full_name, 'Smith')

    def test_full_name_falls_back_to_username_when_both_blank(self):
        """full_name returns the username when both first_name and last_name are blank."""
        user = make_user(
            email='noname@example.com',
            username='noname_user',
            first_name='',
            last_name='',
        )
        self.assertEqual(user.full_name, 'noname_user')


class CustomUserIsAdminTests(TestCase):
    """Tests for the CustomUser.is_admin property."""

    def test_is_admin_true_for_admin_role(self):
        """is_admin returns True when role is ADMIN."""
        user = make_user(
            email='admin@example.com',
            username='adminuser',
            role='ADMIN',
        )
        self.assertTrue(user.is_admin)

    def test_is_admin_false_for_member_role(self):
        """is_admin returns False when role is MEMBER."""
        user = make_user(
            email='member@example.com',
            username='memberuser',
            role='MEMBER',
        )
        self.assertFalse(user.is_admin)

    def test_is_admin_false_for_default_role(self):
        """is_admin returns False for users created with default role."""
        user = CustomUser.objects.create_user(
            email='default@example.com',
            username='defaultuser',
            password='StrongPass123!',
        )
        self.assertFalse(user.is_admin)


# ---------------------------------------------------------------------------
# UserProfile model tests
# ---------------------------------------------------------------------------

class UserProfileDefaultsTests(TestCase):
    """Tests for UserProfile default field values."""

    def test_email_notifications_defaults_to_true(self):
        """email_notifications is True by default on a new profile."""
        user = make_user(
            email='profile@example.com',
            username='profileuser',
        )
        profile = UserProfile.objects.get(user=user)
        self.assertTrue(profile.email_notifications)

    def test_profile_str_includes_user_email(self):
        """UserProfile.__str__ includes the associated user's email."""
        user = make_user(
            email='strtest@example.com',
            username='struser',
        )
        profile = UserProfile.objects.get(user=user)
        self.assertIn('strtest@example.com', str(profile))


# ---------------------------------------------------------------------------
# Login view tests
# ---------------------------------------------------------------------------

class LoginViewTests(TestCase):
    """Tests for the login_view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:login')
        self.user = make_user(
            email='login@example.com',
            username='loginuser',
            password='GoodPassword99!',
        )

    def test_get_returns_200(self):
        """GET /accounts/login/ returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_renders_login_template(self):
        """GET renders the accounts/login.html template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_post_valid_credentials_redirects_to_dashboard(self):
        """POST with valid email/password redirects to /dashboard/."""
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'GoodPassword99!',
        })
        self.assertRedirects(
            response,
            '/dashboard/',
            fetch_redirect_response=False,
        )

    def test_post_invalid_password_rerenders_form(self):
        """POST with wrong password re-renders the login page (200)."""
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_post_invalid_password_shows_error_message(self):
        """POST with wrong password surfaces an error message in the response."""
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'WrongPassword!',
        })
        messages = list(response.context['messages'])
        self.assertTrue(
            any('Invalid' in str(m) or 'invalid' in str(m) for m in messages),
            msg='Expected an error message for invalid credentials.',
        )

    def test_post_unknown_email_rerenders_form(self):
        """POST with an email that has no account re-renders login page."""
        response = self.client.post(self.url, {
            'email': 'nobody@example.com',
            'password': 'AnyPass123!',
        })
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirected_away_from_login(self):
        """A logged-in user visiting /accounts/login/ is redirected to dashboard."""
        self.client.login(username='login@example.com', password='GoodPassword99!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# Profile edit view tests
# ---------------------------------------------------------------------------

class ProfileEditViewTests(TestCase):
    """Tests for the profile_edit_view."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(
            email='edit@example.com',
            username='edituser',
            password='EditPass99!',
            first_name='Old',
            last_name='Name',
        )
        self.profile = UserProfile.objects.get(user=self.user)
        self.url = reverse('accounts:profile_edit')
        self.client.login(username='edit@example.com', password='EditPass99!')

    def test_get_returns_200(self):
        """GET /accounts/profile/edit/ returns HTTP 200 when logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_saves_user_name_fields(self):
        """POST updates first_name and last_name on the user."""
        self.client.post(self.url, {
            'first_name': 'New',
            'last_name': 'Name',
            'username': self.user.username,
            # profile fields
            'phone': '',
            'department': '',
            'student_id': '',
            'bio': '',
            'email_notifications': 'on',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')

    def test_post_saves_profile_bio(self):
        """POST updates the bio field on the profile."""
        self.client.post(self.url, {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'phone': '01700000000',
            'department': 'CSE',
            'student_id': '2021-1-60-001',
            'bio': 'Hello world bio',
            'email_notifications': 'on',
        })
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Hello world bio')

    def test_post_disables_email_notifications(self):
        """POST without email_notifications checkbox sets it to False."""
        # Confirm it starts as True
        self.assertTrue(self.profile.email_notifications)

        self.client.post(self.url, {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'phone': '',
            'department': '',
            'student_id': '',
            'bio': '',
            # email_notifications omitted → checkbox unchecked → False
        })
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.email_notifications)

    def test_post_enables_email_notifications(self):
        """POST with email_notifications=on sets it to True."""
        # First disable it
        self.profile.email_notifications = False
        self.profile.save()

        self.client.post(self.url, {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'phone': '',
            'department': '',
            'student_id': '',
            'bio': '',
            'email_notifications': 'on',
        })
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.email_notifications)

    def test_post_redirects_to_profile_on_success(self):
        """Successful POST redirects to accounts:profile."""
        response = self.client.post(self.url, {
            'first_name': 'Updated',
            'last_name': 'User',
            'username': self.user.username,
            'phone': '',
            'department': '',
            'student_id': '',
            'bio': '',
            'email_notifications': 'on',
        })
        self.assertRedirects(
            response,
            reverse('accounts:profile'),
            fetch_redirect_response=False,
        )


# ---------------------------------------------------------------------------
# Password change view tests
# ---------------------------------------------------------------------------

class PasswordChangeViewTests(TestCase):
    """Tests for the built-in password change view."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(
            email='pwchange@example.com',
            username='pwchangeuser',
            password='OldPass99!',
        )
        self.url = reverse('accounts:password_change')

    def test_unauthenticated_user_is_redirected(self):
        """An anonymous visitor is redirected to login instead of seeing the form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_authenticated_user_can_access(self):
        """A logged-in user can GET the password change page (200)."""
        self.client.login(username='pwchange@example.com', password='OldPass99!')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Registration form validation tests
# ---------------------------------------------------------------------------

class RegistrationFormValidationTests(TestCase):
    """Tests for CustomUserCreationForm duplicate-detection logic."""

    def setUp(self):
        # Create an existing user to trigger duplicate checks
        self.existing = make_user(
            email='existing@example.com',
            username='existinguser',
        )

    def _base_data(self, **overrides):
        data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'UniquePass456!',
            'password2': 'UniquePass456!',
        }
        data.update(overrides)
        return data

    def test_valid_data_passes(self):
        """Form is valid when all fields are unique and passwords match."""
        form = CustomUserCreationForm(data=self._base_data())
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_duplicate_email_is_rejected(self):
        """Form raises a validation error when the email already exists."""
        form = CustomUserCreationForm(
            data=self._base_data(email='existing@example.com')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email_case_insensitive(self):
        """Duplicate email check is case-insensitive."""
        form = CustomUserCreationForm(
            data=self._base_data(email='Existing@Example.COM')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_username_is_rejected(self):
        """Form raises a validation error when the username already exists."""
        form = CustomUserCreationForm(
            data=self._base_data(username='existinguser')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_username_case_insensitive(self):
        """Duplicate username check is case-insensitive."""
        form = CustomUserCreationForm(
            data=self._base_data(username='ExistingUser')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_mismatched_passwords_rejected(self):
        """Form is invalid when password1 and password2 do not match."""
        form = CustomUserCreationForm(
            data=self._base_data(password1='Pass123!', password2='Different!')
        )
        self.assertFalse(form.is_valid())
