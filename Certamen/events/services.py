# apps/events/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Event

@transaction.atomic
def join_event(event_id, user_id):
    # Bloquea la fila del evento durante la transacción
    event = Event.objects.select_for_update().get(pk=event_id)

    # Ya inscrito: no cuenta doble y no rompe la capacidad
    if event.attendees.filter(pk=user_id).exists():
        return event  # idempotente

    # Chequea capacidad restante
    if event.capacity is not None and event.attendees.count() >= event.capacity:
        raise ValidationError("No quedan plazas disponibles para este evento.")

    event.attendees.add(user_id)
    return event
