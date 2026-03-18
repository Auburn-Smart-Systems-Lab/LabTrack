"""Unit tests for the incidents app."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser, UserProfile
from apps.equipment.models import Equipment
from apps.incidents.models import IncidentReport
from apps.incidents.views import _can_manage_incident
from apps.notifications.models import Notification


class IncidentReportModelTest(TestCase):
    """Tests for the IncidentReport model."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='reporter@lab.test',
            username='reporter',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user)
        self.equipment = Equipment.objects.create(
            name='Test Spectrometer',
            is_active=True,
        )
        self.incident = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.user,
            title='Broken display',
            description='The display shows artifacts.',
            severity='MEDIUM',
            status='OPEN',
        )

    def test_incident_str_includes_title(self):
        """IncidentReport.__str__ should include the title."""
        result = str(self.incident)
        self.assertIn('Broken display', result)


class CanManageIncidentTest(TestCase):
    """Tests for the _can_manage_incident helper."""

    def setUp(self):
        # Reporter
        self.reporter = CustomUser.objects.create_user(
            email='reporter@lab.test',
            username='reporter',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.reporter)

        # Equipment owner
        self.owner = CustomUser.objects.create_user(
            email='owner@lab.test',
            username='owner',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.owner)

        # Assigned investigator
        self.assignee = CustomUser.objects.create_user(
            email='assignee@lab.test',
            username='assignee',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.assignee)

        # Admin user
        self.admin = CustomUser.objects.create_user(
            email='admin@lab.test',
            username='admin',
            password='testpass123',
            role='ADMIN',
        )
        UserProfile.objects.get_or_create(user=self.admin)

        # Unrelated member
        self.unrelated = CustomUser.objects.create_user(
            email='random@lab.test',
            username='random',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.unrelated)

        self.equipment = Equipment.objects.create(
            name='HPLC Machine',
            owner=self.owner,
            is_active=True,
        )
        self.incident = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.reporter,
            assigned_to=self.assignee,
            title='Pump failure',
            description='Pump pressure dropped.',
            severity='HIGH',
            status='INVESTIGATING',
        )

    def test_reporter_can_manage(self):
        """_can_manage_incident returns True for the incident reporter."""
        self.assertTrue(_can_manage_incident(self.reporter, self.incident))

    def test_equipment_owner_can_manage(self):
        """_can_manage_incident returns True for the equipment owner."""
        self.assertTrue(_can_manage_incident(self.owner, self.incident))

    def test_assigned_to_can_manage(self):
        """_can_manage_incident returns True for the assigned investigator."""
        self.assertTrue(_can_manage_incident(self.assignee, self.incident))

    def test_admin_can_manage(self):
        """_can_manage_incident returns True for an admin user."""
        self.assertTrue(_can_manage_incident(self.admin, self.incident))

    def test_unrelated_member_cannot_manage(self):
        """_can_manage_incident returns False for an unrelated member."""
        self.assertFalse(_can_manage_incident(self.unrelated, self.incident))


class IncidentListViewTest(TestCase):
    """Tests for incident_list_view."""

    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email='user1@lab.test',
            username='user1',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user1)

        self.user2 = CustomUser.objects.create_user(
            email='user2@lab.test',
            username='user2',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user2)

        self.equipment = Equipment.objects.create(name='Laser Cutter', is_active=True)

        self.incident_a = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.user1,
            title='Incident A',
            description='Description A',
            severity='LOW',
        )
        self.incident_b = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.user2,
            title='Incident B',
            description='Description B',
            severity='HIGH',
        )

        self.client.force_login(self.user1)
        self.url = reverse('incidents:list')

    def test_all_members_can_see_all_incidents(self):
        """Any logged-in member should see all incidents in the list, not just their own."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        incidents_on_page = list(response.context['incidents'])
        pks = [i.pk for i in incidents_on_page]
        self.assertIn(self.incident_a.pk, pks)
        self.assertIn(self.incident_b.pk, pks)


class IncidentDetailViewTest(TestCase):
    """Tests for incident_detail_view."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='member@lab.test',
            username='member',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user)

        self.reporter = CustomUser.objects.create_user(
            email='reporter@lab.test',
            username='reporter',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.reporter)

        self.equipment = Equipment.objects.create(name='3D Printer', is_active=True)
        self.incident = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.reporter,
            title='Nozzle clog',
            description='Nozzle blocked mid-print.',
            severity='MEDIUM',
        )

    def test_any_member_can_view_any_incident(self):
        """Any logged-in member — even if not the reporter — can view an incident."""
        self.client.force_login(self.user)
        url = reverse('incidents:detail', kwargs={'pk': self.incident.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['incident'], self.incident)


class IncidentEditViewTest(TestCase):
    """Tests for incident_edit_view."""

    def setUp(self):
        self.reporter = CustomUser.objects.create_user(
            email='reporter@lab.test',
            username='reporter',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.reporter)

        self.unrelated = CustomUser.objects.create_user(
            email='unrelated@lab.test',
            username='unrelated',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.unrelated)

        self.equipment = Equipment.objects.create(name='Centrifuge', is_active=True)
        self.incident = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.reporter,
            title='Vibration issue',
            description='Excessive vibration at high speed.',
            severity='MEDIUM',
            status='OPEN',
        )
        self.url = reverse('incidents:edit', kwargs={'pk': self.incident.pk})

    def test_reporter_can_edit_incident(self):
        """The reporter should be able to POST an edit to the incident."""
        self.client.force_login(self.reporter)
        response = self.client.post(self.url, {
            'equipment': self.equipment.pk,
            'title': 'Vibration issue — updated',
            'description': 'Updated description.',
            'severity': 'HIGH',
        })
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.title, 'Vibration issue — updated')
        self.assertRedirects(response, reverse('incidents:detail', kwargs={'pk': self.incident.pk}))

    def test_unrelated_member_cannot_edit_incident(self):
        """An unrelated member should be redirected with an error and changes must not be saved."""
        self.client.force_login(self.unrelated)
        response = self.client.post(self.url, {
            'equipment': self.equipment.pk,
            'title': 'Hijacked Title',
            'description': 'Unauthorized edit.',
            'severity': 'LOW',
        })
        self.assertRedirects(response, reverse('incidents:detail', kwargs={'pk': self.incident.pk}))
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.title, 'Vibration issue')
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('permission' in str(m).lower() for m in messages))


class IncidentAssignViewTest(TestCase):
    """Tests for incident_assign_view."""

    def setUp(self):
        self.reporter = CustomUser.objects.create_user(
            email='reporter@lab.test',
            username='reporter',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.reporter)

        self.investigator = CustomUser.objects.create_user(
            email='investigator@lab.test',
            username='investigator',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.investigator)

        self.equipment = Equipment.objects.create(name='Flow Meter', is_active=True)
        self.incident = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.reporter,
            title='Incorrect readings',
            description='Flow meter gives inconsistent values.',
            severity='MEDIUM',
            status='OPEN',
        )
        self.url = reverse('incidents:assign', kwargs={'pk': self.incident.pk})

    def test_reporter_can_assign_investigator(self):
        """The reporter should be able to assign an investigator via POST."""
        self.client.force_login(self.reporter)
        response = self.client.post(self.url, {
            'assigned_to': self.investigator.pk,
        })
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.assigned_to, self.investigator)
        self.assertRedirects(response, reverse('incidents:detail', kwargs={'pk': self.incident.pk}))

    def test_assigning_open_incident_sets_status_to_investigating(self):
        """When an OPEN incident is assigned, the status should auto-update to INVESTIGATING."""
        self.client.force_login(self.reporter)
        self.client.post(self.url, {'assigned_to': self.investigator.pk})
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, 'INVESTIGATING')

    def test_assigning_notifies_the_assignee(self):
        """Assigning an incident to another user should create a Notification for them."""
        self.client.force_login(self.reporter)
        self.client.post(self.url, {'assigned_to': self.investigator.pk})
        notifications = Notification.objects.filter(recipient=self.investigator)
        self.assertTrue(notifications.exists())


class IncidentResolveViewTest(TestCase):
    """Tests for incident_resolve_view."""

    def setUp(self):
        self.assignee = CustomUser.objects.create_user(
            email='assignee@lab.test',
            username='assignee',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.assignee)

        self.reporter = CustomUser.objects.create_user(
            email='reporter@lab.test',
            username='reporter',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.reporter)

        self.equipment = Equipment.objects.create(name='Autoclave', is_active=True)
        self.incident = IncidentReport.objects.create(
            equipment=self.equipment,
            reported_by=self.reporter,
            assigned_to=self.assignee,
            title='Door seal failure',
            description='The door seal is compromised.',
            severity='HIGH',
            status='INVESTIGATING',
        )
        self.url = reverse('incidents:resolve', kwargs={'pk': self.incident.pk})

    def test_assignee_can_resolve_incident(self):
        """The assigned investigator should be able to resolve the incident."""
        self.client.force_login(self.assignee)
        response = self.client.post(self.url, {
            'status': 'RESOLVED',
            'resolution': 'Seal replaced and tested successfully.',
        })
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, 'RESOLVED')
        self.assertRedirects(response, reverse('incidents:detail', kwargs={'pk': self.incident.pk}))
