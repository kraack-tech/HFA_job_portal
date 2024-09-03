from rest_framework import serializers
from django.shortcuts import get_object_or_404
from .models import Calendar, User

# =============================================================================== #
#                              CALENDAR SERIALIZER                                #
# =============================================================================== #
class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = ['id', 'title', 'start_time', 'end_time', 'description', 'user', 'liaison']
    
    # Initliase user variable
    user = serializers.CharField() 

    # Show calendar appointments
    def to_representation(self, appointment):
        representation = super().to_representation(appointment)
        representation['start'] = representation.pop('start_time')
        representation['end'] = representation.pop('end_time')
        representation['user'] = appointment.user.username
        representation['liaison'] = appointment.liaison.username
        return representation
    
    # Validate user
    def validate_user(self, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Username does not exist.")
        return user
    
    # Create appointment: Liaisons only
    def create(self, validated_data):
        user = validated_data.pop('user')
        event = Calendar.objects.create(
            liaison=self.context['request'].user,
            user=user,
            **validated_data
        )
        return event

    # Update appointment: Liaisons only
    def update(self, appointment, validated_data):
        print("appointment", appointment)
        appointment.title = validated_data.get('title', appointment.title)
        appointment.description = validated_data.get('description', appointment.description)
        appointment.start_time = validated_data.get('start_time', appointment.start_time)
        appointment.end_time = validated_data.get('end_time', appointment.end_time)
        appointment.save()
        return appointment

    # Delete appointment
    def delete(self):
        appointment = self.instance
        if appointment:
            appointment.delete()
            return {"status": "success", "message": "Event deleted successfully"}
        else:
            raise serializers.ValidationError("No appointments found to delete.")
