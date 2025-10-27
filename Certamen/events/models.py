from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Event(models.Model):
  event_name = models.CharField("Name of the event",max_length=254)
  pub_date = models.DateTimeField("Date published")
  event_date = models.DateField("Event date")
  starts_at = models.TimeField("Start time of event")
  ends_at = models.TimeField("End time of event")
  location = models.CharField(max_length=254)
  description = models.CharField(max_length=254)
  price = models.IntegerField()
  capacity = models.PositiveIntegerField(
    null=True, blank=True,
    help_text="Deja en blanco para capacidad ilimitada."
  )
  attendees = models.ManyToManyField(
    settings.AUTH_USER_MODEL,
    related_name='events_attending',
    blank=True
  )
  
  is_featured = models.BooleanField(
    "Evento Destacado",
    default=False,
    help_text="Solo puede haber un evento destacado a la vez"
  )
  image_base64 = models.TextField(
    "Imagen del Evento",
    blank=True,
    null=True,
    help_text="Imagen en formato base64"
  )

  def __str__(self):
    return self.event_name

  @property
  def remaining_slots(self):
    if self.capacity is None:
        return None  # ilimitado
    used = self.attendees.count()
    return max(0, self.capacity - used)

  def clean(self):
    # Evita guardar una capacidad menor a los asistentes actuales
    # Solo valida si el evento ya existe (tiene pk) porque attendees es ManyToMany
    if self.pk and self.capacity is not None:
        if self.attendees.exists() and self.capacity < self.attendees.count():
            raise ValidationError(
                {"capacity": "La capacidad no puede ser menor al número actual de asistentes."}
            )
    
    # Valida que solo haya un evento destacado
    if self.is_featured:
        featured_events = Event.objects.filter(is_featured=True)
        if self.pk:
            featured_events = featured_events.exclude(pk=self.pk)
        if featured_events.exists():
            raise ValidationError(
                {"is_featured": "Ya existe un evento destacado. Debes quitarle el destacado al otro evento primero."}
            )
  
  def save(self, *args, **kwargs):
    # Si se marca como destacado, quita el destacado de los demás
    if self.is_featured:
        Event.objects.filter(is_featured=True).exclude(pk=self.pk).update(is_featured=False)
    super().save(*args, **kwargs)


