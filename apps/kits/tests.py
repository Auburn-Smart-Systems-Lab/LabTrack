"""Unit tests for the kits app."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser, UserProfile
from apps.equipment.models import Equipment
from apps.kits.forms import KitForm
from apps.kits.models import Kit, KitItem


class KitModelTest(TestCase):
    """Tests for the Kit model."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='creator@lab.test',
            username='creator',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user)
        self.kit = Kit.objects.create(
            name='Basic Electronics Kit',
            description='A starter kit for electronics experiments.',
            created_by=self.user,
            is_active=True,
            is_shared=False,
        )

    def test_kit_str_returns_name(self):
        """Kit.__str__ should return the kit name."""
        self.assertEqual(str(self.kit), 'Basic Electronics Kit')


class KitFormTest(TestCase):
    """Tests for KitForm."""

    def test_kit_form_includes_is_shared_field(self):
        """KitForm must expose the is_shared field."""
        form = KitForm()
        self.assertIn('is_shared', form.fields)


class KitListViewTest(TestCase):
    """Tests for kit_list_view."""

    def setUp(self):
        # Primary user (the one we'll log in as)
        self.user = CustomUser.objects.create_user(
            email='member@lab.test',
            username='member',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user)

        # Another user
        self.other_user = CustomUser.objects.create_user(
            email='other@lab.test',
            username='other',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.other_user)

        # Kit owned by the primary user
        self.my_kit = Kit.objects.create(
            name='My Kit',
            created_by=self.user,
            is_active=True,
            is_shared=False,
        )

        # Shared kit from another user — should appear in shared_kits
        self.shared_kit = Kit.objects.create(
            name='Shared Kit',
            created_by=self.other_user,
            is_active=True,
            is_shared=True,
        )

        # Private kit from another user — must NOT appear anywhere for this user
        self.private_other_kit = Kit.objects.create(
            name='Private Other Kit',
            created_by=self.other_user,
            is_active=True,
            is_shared=False,
        )

        self.client.force_login(self.user)
        self.url = reverse('kits:list')

    def test_my_kits_contains_only_own_kits(self):
        """my_kits in context should contain only kits created by the logged-in user."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        my_kits = list(response.context['my_kits'])
        self.assertIn(self.my_kit, my_kits)
        self.assertNotIn(self.shared_kit, my_kits)
        self.assertNotIn(self.private_other_kit, my_kits)

    def test_shared_kits_contains_other_users_shared_kits(self):
        """shared_kits in context should contain is_shared=True kits from other users."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        shared_kits = list(response.context['shared_kits'])
        self.assertIn(self.shared_kit, shared_kits)

    def test_shared_kits_excludes_current_users_own_kits(self):
        """The current user's own kits must not appear in shared_kits even if shared."""
        self.my_kit.is_shared = True
        self.my_kit.save()
        response = self.client.get(self.url)
        shared_kits = list(response.context['shared_kits'])
        self.assertNotIn(self.my_kit, shared_kits)

    def test_private_kits_from_other_users_not_in_shared_kits(self):
        """Private kits (is_shared=False) from other users must not appear in shared_kits."""
        response = self.client.get(self.url)
        shared_kits = list(response.context['shared_kits'])
        self.assertNotIn(self.private_other_kit, shared_kits)


class KitCreateViewTest(TestCase):
    """Tests for kit_create_view."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='creator@lab.test',
            username='creator',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)
        self.url = reverse('kits:create')

    def test_post_creates_kit_with_request_user_as_creator(self):
        """A valid POST to kit_create_view should create a kit with created_by=request.user."""
        response = self.client.post(self.url, {
            'name': 'New Test Kit',
            'description': 'Created in a unit test.',
            'is_shared': False,
        })
        self.assertEqual(Kit.objects.count(), 1)
        kit = Kit.objects.first()
        self.assertEqual(kit.created_by, self.user)
        self.assertEqual(kit.name, 'New Test Kit')
        # Should redirect to the detail page after creation
        self.assertRedirects(response, reverse('kits:detail', kwargs={'pk': kit.pk}))


class KitEditViewTest(TestCase):
    """Tests for kit_edit_view."""

    def setUp(self):
        self.creator = CustomUser.objects.create_user(
            email='creator@lab.test',
            username='creator',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.creator)

        self.other = CustomUser.objects.create_user(
            email='other@lab.test',
            username='other',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.other)

        self.kit = Kit.objects.create(
            name='Editable Kit',
            created_by=self.creator,
            is_active=True,
        )
        self.url = reverse('kits:edit', kwargs={'pk': self.kit.pk})

    def test_creator_can_edit_kit(self):
        """The kit creator should be able to POST an update successfully."""
        self.client.force_login(self.creator)
        response = self.client.post(self.url, {
            'name': 'Updated Kit Name',
            'description': 'Updated description.',
            'is_shared': True,
        })
        self.kit.refresh_from_db()
        self.assertEqual(self.kit.name, 'Updated Kit Name')
        self.assertRedirects(response, reverse('kits:detail', kwargs={'pk': self.kit.pk}))

    def test_non_creator_cannot_edit_kit(self):
        """A non-creator should receive an error and be redirected without saving changes."""
        self.client.force_login(self.other)
        response = self.client.post(self.url, {
            'name': 'Hijacked Name',
            'description': '',
            'is_shared': False,
        })
        # Should redirect to detail page
        self.assertRedirects(response, reverse('kits:detail', kwargs={'pk': self.kit.pk}))
        # Name should remain unchanged
        self.kit.refresh_from_db()
        self.assertEqual(self.kit.name, 'Editable Kit')
        # Error message should have been queued
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('permission' in str(m).lower() for m in messages))


class KitDeleteViewTest(TestCase):
    """Tests for kit_delete_view."""

    def setUp(self):
        self.creator = CustomUser.objects.create_user(
            email='creator@lab.test',
            username='creator',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.creator)

        self.other = CustomUser.objects.create_user(
            email='other@lab.test',
            username='other',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.other)

        self.kit = Kit.objects.create(
            name='Kit To Delete',
            created_by=self.creator,
            is_active=True,
        )
        self.url = reverse('kits:delete', kwargs={'pk': self.kit.pk})

    def test_creator_can_delete_kit(self):
        """A POST from the creator should delete the kit and redirect to the list."""
        self.client.force_login(self.creator)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('kits:list'))
        self.assertFalse(Kit.objects.filter(pk=self.kit.pk).exists())

    def test_non_creator_cannot_delete_kit(self):
        """A POST from a non-creator should not delete the kit."""
        self.client.force_login(self.other)
        response = self.client.post(self.url)
        # Redirects to detail, kit still exists
        self.assertRedirects(response, reverse('kits:detail', kwargs={'pk': self.kit.pk}))
        self.assertTrue(Kit.objects.filter(pk=self.kit.pk).exists())


class KitItemAddViewTest(TestCase):
    """Tests for kit_item_add_view."""

    def setUp(self):
        self.creator = CustomUser.objects.create_user(
            email='creator@lab.test',
            username='creator',
            password='testpass123',
        )
        UserProfile.objects.get_or_create(user=self.creator)

        self.kit = Kit.objects.create(
            name='Kit With Items',
            created_by=self.creator,
            is_active=True,
        )
        self.equipment = Equipment.objects.create(
            name='Test Oscilloscope',
            is_active=True,
        )
        self.url = reverse('kits:add_item', kwargs={'pk': self.kit.pk})

    def test_creator_can_add_equipment_to_kit(self):
        """The kit creator should be able to add an equipment item to their kit."""
        self.client.force_login(self.creator)
        response = self.client.post(self.url, {
            'equipment': self.equipment.pk,
            'quantity': 1,
            'notes': '',
        })
        self.assertEqual(KitItem.objects.filter(kit=self.kit).count(), 1)
        item = KitItem.objects.get(kit=self.kit)
        self.assertEqual(item.equipment, self.equipment)
        self.assertRedirects(response, reverse('kits:detail', kwargs={'pk': self.kit.pk}))
