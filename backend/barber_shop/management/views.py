# management/views.py

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import BarberProfile, Client, AttendanceLog, User
from .serializers import *
from django.shortcuts import get_object_or_404
import random
from rest_framework.schemas import get_schema_view

schema_view = get_schema_view(
    title="Barber Shop API",
    description="API para la gestión de una barbería",
    version="1.0.0",
    public=True,
)

#Barberos 
@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_barber(request):
    username = request.data.get('username')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    if username and password:
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='barber'
        )
        BarberProfile.objects.create(user=user)
        return Response({'message': 'Barbero agregado exitosamente.'}, status=201)
    else:
        return Response({'error': 'Datos incompletos.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def edit_barber(request):
    """
    Edita los detalles de un barbero.
    """
    barber_id = request.data.get('barber_id')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')

    if barber_id:
        barber_profile = get_object_or_404(BarberProfile, id=barber_id)
        user = barber_profile.user

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        user.save()
        return Response({'message': 'Barbero actualizado exitosamente.'}, status=200)
    else:
        return Response({'error': 'Se requiere el ID del barbero.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def toggle_barber_status(request):
    """
    Activa o desactiva un barbero.
    """
    barber_id = request.data.get('barber_id')

    if barber_id:
        barber_profile = get_object_or_404(BarberProfile, id=barber_id)
        barber_profile.is_active = not barber_profile.is_active
        barber_profile.save()
        status = 'activo' if barber_profile.is_active else 'inactivo'
        return Response({'message': f'El barbero ahora está {status}.'}, status=200)
    else:
        return Response({'error': 'Se requiere el ID del barbero.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile(request):
    user = request.user
    data = request.data

    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    if 'image' in data:
        user.image = data['image']
    user.save()

    serializer = ClientSerializer(user)
    return Response(serializer.data, status=200)

#Barberos y clientes
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ticket(request):
    name = request.data.get('name')
    barber_id = request.data.get('barber_id')  # Puede ser None o 'esperar'

    if name:
        client = Client(name=name)
        if barber_id and barber_id != 'esperar':
            barber = get_object_or_404(BarberProfile, id=barber_id, is_active=True)
            client.assigned_barber = barber
            client.in_queue = False
        client.save()
        return Response({'message': 'Ticket generado exitosamente.'}, status=201)
    else:
        return Response({'error': 'Nombre del cliente es requerido.'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_attendance(request):
    client_id = request.data.get('client_id')
    if client_id:
        client = get_object_or_404(Client, id=client_id)
        barber_profile = get_object_or_404(BarberProfile)

        if client.assigned_barber_id == barber_profile.id:
            client_name = client.name  # Obtener el nombre del cliente antes de eliminarlo
            try:
                attendance_log = AttendanceLog.objects.create(client_name=client_name, barber=barber_profile)
            except Exception as e:
                print('Error creating AttendanceLog:', e)
                return Response({'error': 'Error al crear el registro de asistencia.'}, status=500)
            
            # Actualizar el total de clientes atendidos
            barber_profile.total_clients_attended += 1
            barber_profile.save()
            # Eliminar el cliente
            client.delete()
            return Response({'message': 'Atención completada exitosamente.'}, status=200)
        else:
            return Response({'error': 'El cliente no está asignado a este barbero.'}, status=403)
    else:
        return Response({'error': 'Se requiere el ID del cliente.'}, status=400)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_client_from_barber(request):
    """
    Elimina un cliente de la lista de un barbero.
    """
    client_id = request.data.get('client_id')

    if client_id:
        client = get_object_or_404(Client, id=client_id)
        barber_profile = get_object_or_404(BarberProfile, user=request.user)

        # Verificar que el cliente está asignado al barbero actual
        if client.assigned_barber == barber_profile:
            client.delete()
            return Response({'message': 'Cliente eliminado de la lista.'}, status=200)
        else:
            return Response({'error': 'El cliente no está asignado a este barbero.'}, status=403)
    else:
        return Response({'error': 'Se requiere el ID del cliente.'}, status=400)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reassign_client_to_queue(request):
    """
    Reasigna un cliente a un barbero específico o a uno disponible automáticamente.
    """
    client_id = request.data.get('client_id')
    barber_id = request.data.get('barber_id')  # ID del barbero al que se desea asignar (opcional)
    
    if not client_id:
        return Response({'error': 'Se requiere el ID del cliente.'}, status=400)

    client = get_object_or_404(Client, id=client_id)

    if barber_id:
        # Reasignar al barbero especificado
        barber = BarberProfile.objects.filter(id=barber_id, is_active=True).first()
    else:
        # Buscar barberos activos que no tengan clientes asignados actualmente
        available_barbers = BarberProfile.objects.filter(
            is_active=True,
            clients_assigned__isnull=True  # Sin clientes asignados
        )

        if not available_barbers.exists():
            return Response({'error': 'No hay barberos disponibles en este momento.'}, status=200)

        # Seleccionar un barbero aleatoriamente
        barber = random.choice(available_barbers)

    # Asignar el cliente al barbero
    client.assigned_barber = barber
    client.in_queue = False
    client.save()

    return Response({
        'message': f'Cliente asignado a {barber.user.get_full_name()} exitosamente.'
    }, status=200)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_client_from_queue(request):
    """
    Elimina un cliente de la cola de espera.
    """
    client_id = request.data.get('client_id')

    if client_id:
        client = get_object_or_404(Client, id=client_id, in_queue=True)
        client.delete()
        return Response({'message': 'Cliente eliminado de la cola exitosamente.'}, status=200)
    else:
        return Response({'error': 'Se requiere el ID del cliente.'}, status=400)
    
#Aciones Cerrar 
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def close_day(request):
    """
    Cierra el día, reiniciando contadores y registros.
    """
    # Reiniciar total de clientes atendidos
    BarberProfile.objects.update(total_clients_attended=0)
    # Eliminar clientes y registros
    Client.objects.all().delete()
    AttendanceLog.objects.all().delete()
    return Response({'message': 'Día cerrado exitosamente.'}, status=200)

#Vista para Obtener Barberos y sus Clientes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_barbers_and_clients(request):
    """
    Devuelve la lista de barberos con sus clientes asignados.
    """
    barbers = BarberProfile.objects.filter(user__is_active=True).prefetch_related('clients_assigned', 'user')
    serializer = BarberProfileSerializer(barbers, many=True)
    return Response(serializer.data, status=200)

#Vista para Obtener Clientes en Cola 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clients_in_queue(request):
    """
    Devuelve la lista de clientes en cola.
    """
    clients = Client.objects.filter(in_queue=True).order_by('created_at')
    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data, status=200)

#Vista para Obtener el Registro de Atenciones 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance_log(request):
    """
    Devuelve el registro de atenciones.
    """
    clients_history = AttendanceLog.objects.all().order_by('-attended_at')
    serializer = AttendanceLogAllSerializer(clients_history, many=True)

    return Response(serializer.data, status=200)