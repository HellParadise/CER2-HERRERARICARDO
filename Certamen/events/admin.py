from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Event
import base64


class EventAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(
        required=False,
        label="Subir Imagen",
        help_text="Selecciona una imagen para el evento (JPG, PNG, GIF)",
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    
    class Meta:
        model = Event
        fields = '__all__'
        widgets = {
            'image_base64': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya existe una imagen, no es obligatorio subir otra
        if self.instance and self.instance.image_base64:
            self.fields['image_upload'].help_text = "Imagen actual guardada. Sube una nueva para reemplazarla."
    
    def clean_image_upload(self):
        image = self.cleaned_data.get('image_upload')
        if image:
            # Validar tamaño (máximo 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen no puede ser mayor a 5MB')
            
            # Convertir a base64
            image_data = image.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determinar el tipo MIME
            content_type = image.content_type
            self.cleaned_data['image_base64_full'] = f"data:{content_type};base64,{base64_image}"
        
        return image
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Si se subió una nueva imagen, actualizar el campo base64
        if 'image_base64_full' in self.cleaned_data:
            instance.image_base64 = self.cleaned_data['image_base64_full']
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Configuración personalizada del panel de administración para Events
    """
    
    # Usar el formulario personalizado
    form = EventAdminForm
    
    # Columnas que se muestran en la lista de eventos
    list_display = [
        'image_thumbnail',
        'event_name',
        'featured_badge',
        'event_date',
        'time_range',
        'location',
        'price_display',
        'capacity_status',
        'attendees_count',
        'remaining_slots_display',
        'is_full',
        'income'
    ]
    
    # Filtros laterales
    list_filter = [
        'is_featured',
        'event_date',
        'pub_date',
        'location',
    ]
    
    # Búsqueda por nombre, ubicación y descripción
    search_fields = [
        'event_name',
        'location',
        'description',
    ]
    
    # Campos de solo lectura (calculados automáticamente)
    readonly_fields = [
        'attendees_count',
        'remaining_slots_display',
        'pub_date',
        'image_preview',
        'income'
    ]
    
    # Ordenamiento predeterminado
    ordering = ['-event_date', 'starts_at']
    
    # Permite seleccionar fechas desde un calendario
    date_hierarchy = 'event_date'
    
    # Organización de campos en el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('event_name', 'description', 'pub_date', 'is_featured')
        }),
        ('Imagen del Evento', {
            'fields': ('image_upload', 'image_preview'),
            'description': 'Sube una imagen para el evento (máximo 5MB)'
        }),
        ('Fecha y Hora', {
            'fields': ('event_date', 'starts_at', 'ends_at'),
            'description': 'Configura cuándo será el evento'
        }),
        ('Ubicación y Precio', {
            'fields': ('location', 'price')
        }),
        ('Capacidad y Asistentes', {
            'fields': ('capacity', 'attendees', 'attendees_count', 'remaining_slots_display'),
            'description': 'Gestiona la capacidad y los asistentes del evento'
        }),
    )
    
    # Mejora la selección de asistentes con un widget de selección múltiple
    filter_horizontal = ['attendees']
    
    # Número de eventos por página
    list_per_page = 25
    
    # ===================== MÉTODOS PERSONALIZADOS =====================
    
    @admin.display(description='Horario', ordering='starts_at')
    def time_range(self, obj):
        """Muestra el rango de horario del evento"""
        return f"{obj.starts_at.strftime('%H:%M')} - {obj.ends_at.strftime('%H:%M')}"
    
    @admin.display(description='Precio')
    def price_display(self, obj):
        """Muestra el precio con formato"""
        if obj.price == 0:
            return format_html('<span style="color: green; font-weight: bold;">GRATIS</span>')
        return f"${obj.price:,}"
    
    @admin.display(description='N° Asistentes', ordering='attendees')
    def attendees_count(self, obj):
        """Muestra la cantidad de asistentes"""
        count = obj.attendees.count()
        if count == 0:
            return format_html('<span style="color: gray;">0</span>')
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-weight: bold;">{}</span>',
            count
        )
    
    @admin.display(description='Estado de Capacidad')
    def capacity_status(self, obj):
        """Muestra visualmente el estado de la capacidad"""
        if obj.capacity is None:
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 5px 12px; '
                'border-radius: 15px; font-weight: bold;">∞ ILIMITADO</span>'
            )
        
        current = obj.attendees.count()
        percentage = (current / obj.capacity * 100) if obj.capacity > 0 else 0
        
        # Color según el porcentaje de ocupación
        if percentage >= 100:
            color = '#dc3545'  # Rojo - Completo
            status = 'COMPLETO'
        elif percentage >= 80:
            color = '#fd7e14'  # Naranja - Casi lleno
            status = 'CASI LLENO'
        elif percentage >= 50:
            color = '#ffc107'  # Amarillo - Medio lleno
            status = 'MEDIO'
        else:
            color = '#28a745'  # Verde - Disponible
            status = 'DISPONIBLE'
        
        return format_html(
            '<div style="text-align: center;">'
            '<span style="background: {}; color: white; padding: 5px 12px; '
            'border-radius: 15px; font-weight: bold;">{}</span>'
            '<br><small>{}/{}</small>'
            '</div>',
            color, status, current, obj.capacity
        )
    
    @admin.display(description='Plazas Disponibles')
    def remaining_slots_display(self, obj):
        """Muestra las plazas restantes"""
        remaining = obj.remaining_slots
        
        if remaining is None:
            return format_html(
                '<span style="color: #17a2b8; font-weight: bold; font-size: 1.2em;">∞</span>'
            )
        
        if remaining == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold; font-size: 1.2em;">0</span> '
                '<span style="color: #dc3545;">❌ Completo</span>'
            )
        elif remaining <= 5:
            return format_html(
                '<span style="color: #fd7e14; font-weight: bold; font-size: 1.2em;">{}</span> '
                '<span style="color: #fd7e14;">⚠️ Últimas plazas</span>',
                remaining
            )
        else:
            return format_html(
                '<span style="color: #28a745; font-weight: bold; font-size: 1.2em;">{}</span> '
                '<span style="color: #28a745;">✅ Disponibles</span>',
                remaining
            )
    
    @admin.display(description='¿Lleno?', boolean=True)
    def is_full(self, obj):
        """Indica si el evento está lleno"""
        if obj.capacity is None:
            return False
        return obj.attendees.count() >= obj.capacity
    
    @admin.display(description='Imagen')
    def image_thumbnail(self, obj):
        """Muestra una miniatura de la imagen en la lista"""
        if obj.image_base64:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; '
                'border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" />',
                obj.image_base64
            )
        return format_html(
            '<div style="width: 60px; height: 60px; background: #e9ecef; '
            'border-radius: 8px; display: flex; align-items: center; justify-content: center; '
            'color: #6c757d;">Sin img</div>'
        )
    
    @admin.display(description='⭐')
    def featured_badge(self, obj):
        """Muestra si el evento está destacado"""
        if obj.is_featured:
            return format_html(
                '<span style="background: linear-gradient(135deg, #ffd700, #ffed4e); '
                'color: #000; padding: 6px 12px; border-radius: 20px; font-weight: bold; '
                'box-shadow: 0 4px 8px rgba(255, 215, 0, 0.4); font-size: 0.85rem;">'
                '⭐ DESTACADO</span>'
            )
        return format_html('<span style="color: #ccc;">—</span>')
    
    @admin.display(description='Vista Previa de Imagen')
    def image_preview(self, obj):
        if obj.image_base64:
            return format_html(
                '<div style="margin: 15px 0;">'
                '<p><strong>Imagen actual:</strong></p>'
                '<img src="{}" style="max-width: 400px; max-height: 300px; '
                'border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); '
                'display: block; margin-top: 10px;" />'
                '<p style="margin-top: 10px; color: #666; font-size: 0.9rem;">'
                '<em>Para cambiar la imagen, selecciona una nueva en el campo "Subir Imagen" arriba.</em></p>'
                '</div>',
                obj.image_base64
            )
        return format_html(
            '<div style="padding: 15px; background: #f8f9fa; border-radius: 8px; '
            'border-left: 4px solid #ffc107;">'
            '<p style="margin: 0; color: #856404;"><strong>⚠️ Sin imagen</strong></p>'
            '<p style="margin: 5px 0 0 0; color: #666;">Sube una imagen usando el campo de arriba.</p>'
            '</div>'
        )
    
    @admin.display(description='Recaudación')
    def income(self, obj):
        return f"${obj.price * obj.attendees.count():,}"
    
    def save_model(self, request, obj, form, change):
        if not change: 
            from django.utils import timezone
            obj.pub_date = timezone.now()
        super().save_model(request, obj, form, change)