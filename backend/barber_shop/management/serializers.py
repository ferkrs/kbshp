# management/serializers.py

from rest_framework import serializers
from .models import BarberProfile, Client, AttendanceLog, User

class UserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'image']
        
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'assigned_barber', 'in_queue', 'created_at']

class BarberProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    clients = ClientSerializer(many=True, read_only=True, source='clients_assigned')

    class Meta:
        model = BarberProfile
        fields = ['id', 'user', 'is_active', 'total_clients_attended', 'clients']

class AttendanceLogSerializer(serializers.ModelSerializer):
    barber = BarberProfileSerializer()

    class Meta:
        model = AttendanceLog
        fields = ['id', 'client_name', 'barber', 'attended_at']

class ClientAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceLog
        fields = ['client_name', 'attended_at']

class AttendanceLogAllSerializer(serializers.ModelSerializer):
    barber = BarberProfileSerializer()

    class Meta:
        model = AttendanceLog
        fields = ['id', 'client_name', 'attended_at', 'barber']