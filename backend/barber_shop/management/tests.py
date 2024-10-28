# management/tests.py
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import BarberProfile, Client, AttendanceLog
from rest_framework.test import APIClient
from rest_framework import status

class BarberProfileModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='barber1',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez',
            role='barber'
        )
        self.barber_profile = BarberProfile.objects.create(user=self.user)

    def test_barber_profile_creation(self):
        self.assertEqual(str(self.barber_profile), 'Juan Pérez')
        self.assertTrue(self.barber_profile.is_active)
        self.assertEqual(self.barber_profile.total_clients_attended, 0)

class ClientModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name='Cliente Test')

    def test_client_creation(self):
        self.assertEqual(str(self.client), 'Cliente Test')
        self.assertTrue(self.client.in_queue)
        self.assertIsNone(self.client.assigned_barber)

class AttendanceLogModelTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username='barber2',
            password='testpass123',
            first_name='Ana',
            last_name='Gómez',
            role='barber'
        )
        barber = BarberProfile.objects.create(user=user)
        client = Client.objects.create(name='Cliente Log', assigned_barber=barber, in_queue=False)
        self.attendance_log = AttendanceLog.objects.create(client=client, barber=barber)

    def test_attendance_log_creation(self):
        self.assertEqual(
            str(self.attendance_log),
            f"{self.attendance_log.client.name} atendido por {self.attendance_log.barber.user.get_full_name()} a las {self.attendance_log.attended_at}"
        )

class ViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Crear un usuario administrador
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            password='adminpass',
            role='admin'
        )

        # Crear un usuario barbero
        self.barber_user = get_user_model().objects.create_user(
            username='barber',
            password='barberpass',
            role='barber'
        )
        self.barber_profile = BarberProfile.objects.create(user=self.barber_user)

        # Crear un cliente
        self.client_user = Client.objects.create(name='Cliente1')

    def test_add_barber(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('add_barber')
        data = {
            'username': 'new_barber',
            'password': 'newpass123',
            'first_name': 'Nuevo',
            'last_name': 'Barbero'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(get_user_model().objects.filter(username='new_barber').exists())


    def test_add_barber(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('add_barber')
        data = {
            'username': 'new_barber',
            'password': 'newpass123',
            'first_name': 'Nuevo',
            'last_name': 'Barbero'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(get_user_model().objects.filter(username='new_barber').exists())


    def test_generate_ticket(self):
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('generate_ticket')
        data = {
            'name': 'Cliente Test',
            'barber_id': 'esperar'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Client.objects.filter(name='Cliente Test').exists())

    def test_complete_attendance(self):
        # Asignar un cliente al barbero
        client = Client.objects.create(
            name='Cliente Atender',
            assigned_barber=self.barber_profile,
            in_queue=False
        )
        client.refresh_from_db()
        self.assertEqual(client.assigned_barber, self.barber_profile)
        print('Assigned Barber ID:', client.assigned_barber_id)
        print('Barber Profile ID:', self.barber_profile.id)

        self.client.force_authenticate(user=self.barber_user)
        url = reverse('complete_attendance')
        data = {
            'client_id': client.id
        }
        response = self.client.post(url, data, format='json')
        print('Response:', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Client.objects.filter(id=client.id).exists())
        self.assertEqual(AttendanceLog.objects.count(), 1)
        self.barber_profile.refresh_from_db()
        self.assertEqual(self.barber_profile.total_clients_attended, 1)

    def test_remove_client_from_barber(self):
        # Asignar un cliente al barbero
        client = Client.objects.create(name='Cliente Remover', assigned_barber=self.barber_profile, in_queue=False)
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('remove_client_from_barber')
        data = {
            'client_id': client.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Client.objects.filter(id=client.id).exists())

    def test_reassign_client_to_queue(self):
        # Asignar un cliente al barbero
        client = Client.objects.create(name='Cliente Reasignar', assigned_barber=self.barber_profile, in_queue=False)
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('reassign_client_to_queue')
        data = {
            'client_id': client.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client.refresh_from_db()
        self.assertIsNone(client.assigned_barber)
        self.assertTrue(client.in_queue)

    def test_remove_client_from_queue(self):
        # Crear un cliente en cola
        client_in_queue = Client.objects.create(name='Cliente Cola')
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('remove_client_from_queue')
        data = {
            'client_id': client_in_queue.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Client.objects.filter(id=client_in_queue.id).exists())

    def test_edit_barber(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('edit_barber')
        data = {
            'barber_id': self.barber_profile.id,
            'first_name': 'Nombre Editado',
            'last_name': 'Apellido Editado'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.barber_user.refresh_from_db()
        self.assertEqual(self.barber_user.first_name, 'Nombre Editado')
        self.assertEqual(self.barber_user.last_name, 'Apellido Editado')

    def test_toggle_barber_status(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('toggle_barber_status')
        data = {
            'barber_id': self.barber_profile.id
        }
        # Desactivar
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.barber_profile.refresh_from_db()
        self.assertFalse(self.barber_profile.is_active)
        # Activar
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.barber_profile.refresh_from_db()
        self.assertTrue(self.barber_profile.is_active)

    def test_close_day(self):
        # Crear datos
        AttendanceLog.objects.create(client=self.client_user, barber=self.barber_profile)
        self.barber_profile.total_clients_attended = 5
        self.barber_profile.save()
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('close_day')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.barber_profile.refresh_from_db()
        self.assertEqual(self.barber_profile.total_clients_attended, 0)
        self.assertEqual(Client.objects.count(), 0)
        self.assertEqual(AttendanceLog.objects.count(), 0)

    def test_get_barbers_and_clients(self):
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('get_barbers_and_clients')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


    def test_get_clients_in_queue(self):
        Client.objects.create(name='Cliente en Cola')
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('get_clients_in_queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_attendance_log(self):
        AttendanceLog.objects.create(client=self.client_user, barber=self.barber_profile)
        self.client.force_authenticate(user=self.barber_user)
        url = reverse('get_attendance_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
