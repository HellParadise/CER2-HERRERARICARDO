from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Event
from .services import join_event
from django.core.exceptions import ValidationError


def home(request):
    """Vista principal/home que muestra el evento destacado"""
    featured_event = Event.objects.filter(is_featured=True).first()
    return render(request, 'events/main.html', {'featured_event': featured_event})


def index(request):
    """Vista principal que muestra todos los eventos"""
    events = Event.objects.all().order_by('event_date')
    return render(request, 'events/events.html', {'events': events})


def event_detail(request, event_id):
    """Vista de detalle de un evento específico"""
    event = get_object_or_404(Event, pk=event_id)
    return render(request, 'events/event_detail.html', {'event': event})


@login_required
def join_event_view(request, event_id):
    """Vista para inscribirse a un evento"""
    if request.method == 'POST':
        try:
            event = join_event(event_id, request.user.id)
            messages.success(
                request, 
                f'¡Te has inscrito exitosamente en "{event.event_name}"! '
                f'Nos vemos el {event.event_date.strftime("%d/%m/%Y")} a las {event.starts_at.strftime("%H:%M")}.'
            )
        except Event.DoesNotExist:
            messages.error(request, 'El evento no existe.')
        except ValidationError as e:
            messages.error(request, str(e.message))
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
        
        return redirect('event_detail', event_id=event_id)
    
    # Si no es POST, redirigir al detalle
    return redirect('event_detail', event_id=event_id)


@login_required
def leave_event_view(request, event_id):
    """Vista para desinscribirse de un evento"""
    if request.method == 'POST':
        try:
            event = get_object_or_404(Event, pk=event_id)
            
            if request.user in event.attendees.all():
                event.attendees.remove(request.user)
                messages.success(
                    request,
                    f'Te has desinscrito de "{event.event_name}".'
                )
            else:
                messages.info(request, 'No estabas inscrito en este evento.')
                
        except Event.DoesNotExist:
            messages.error(request, 'El evento no existe.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
        
        return redirect('event_detail', event_id=event_id)
    
    # Si no es POST, redirigir al detalle
    return redirect('event_detail', event_id=event_id)