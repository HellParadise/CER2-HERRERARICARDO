# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Solo puede haber un evento destacado a la vez', verbose_name='Evento Destacado'),
        ),
        migrations.AddField(
            model_name='event',
            name='image_base64',
            field=models.TextField(blank=True, help_text='Imagen en formato base64', null=True, verbose_name='Imagen del Evento'),
        ),
    ]


