from django.db import models
from django.conf import settings  # Para obtener el modelo User configurado
from django.utils import timezone


# models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class Empresa(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    
    CARGO_CHOICES = [
        ('GERENTE', 'Gerente'),
        ('JEFE', 'Jefe'),
        ('TECNICO', 'Técnico'),
    ]
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)

    def __str__(self):
        return f"{self.usuario.username} - {self.empresa}"


# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth.models import User
# from .models import PerfilUsuario

# @receiver(post_save, sender=User)
# def crear_perfil_usuario(sender, instance, created, **kwargs):
#     if created:
#         PerfilUsuario.objects.create(usuario=instance)




ESTADOS = [
    ('BUENO', 'Bueno'),
    ('REVISION', 'En Revisión'),
    ('RECHAZADO', 'Rechazado'),
]


# --------------------------------------------
# Modelo principal: Vehículo
# --------------------------------------------
class Vehiculo(models.Model):
    patente = models.CharField(max_length=10, unique=False, blank=True, null=True)
    numero_orden = models.PositiveIntegerField(unique=True, editable=False, null=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100, default='Sin modelo')
    color = models.CharField(max_length=50, default='Sin color')
    tipo_bencina = models.CharField(max_length=50, default='Sin especificar')
    numero_motor = models.CharField(max_length=100, default='Desconocido')
    imagen_base64 = models.TextField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos_registrados'
    )
    fecha_registro = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.numero_orden is None:
            last = Vehiculo.objects.order_by('-numero_orden').first()
            self.numero_orden = (last.numero_orden + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.numero_orden} - {self.marca} {self.modelo}"

    # Métodos para el reporte PDF
    def get_total_puntos(self):
        """Retorna el total de puntos revisados para este vehículo"""
        total = 0
        sistemas = [
            'detalle_motor', 'detalle_transmision', 'detalle_frenos',
            'detalle_direccion_suspension', 'detalle_carroceria',
            'detalle_revision_general', 'detalle_interior'
        ]
        
        for sistema in sistemas:
            detalle = getattr(self, sistema, None)
            if detalle and hasattr(detalle, 'puntos'):
                total += detalle.puntos.count()
        return total

    def get_puntos_aprobados(self):
        """Retorna la cantidad de puntos en estado BUENO"""
        return self._contar_puntos_por_estado('BUENO')

    def get_puntos_revision(self):
        """Retorna la cantidad de puntos en estado REVISION"""
        return self._contar_puntos_por_estado('REVISION')

    def get_puntos_rechazados(self):
        """Retorna la cantidad de puntos en estado RECHAZADO"""
        return self._contar_puntos_por_estado('RECHAZADO')

    def _contar_puntos_por_estado(self, estado):
        count = 0
        sistemas = [
            'detalle_motor', 'detalle_transmision', 'detalle_frenos',
            'detalle_direccion_suspension', 'detalle_carroceria',
            'detalle_revision_general', 'detalle_interior'
        ]
        
        for sistema in sistemas:
            detalle = getattr(self, sistema, None)
            if detalle and hasattr(detalle, 'puntos'):
                count += detalle.puntos.filter(estado=estado).count()
        return count

    def get_sistemas(self):
        """Retorna lista de sistemas con su estado general"""
        sistemas_info = [
            {'nombre': 'Motor', 'attr': 'detalle_motor', 'icono': 'gear'},
            {'nombre': 'Transmisión', 'attr': 'detalle_transmision', 'icono': 'gear-wide-connected'},
            {'nombre': 'Frenos', 'attr': 'detalle_frenos', 'icono': 'stop-circle'},
            {'nombre': 'Dirección/Suspensión', 'attr': 'detalle_direccion_suspension', 'icono': 'sliders'},
            {'nombre': 'Carrocería', 'attr': 'detalle_carroceria', 'icono': 'car-front'},
            {'nombre': 'Revisión General', 'attr': 'detalle_revision_general', 'icono': 'clipboard-check'},
            {'nombre': 'Interior', 'attr': 'detalle_interior', 'icono': 'cup-hot'}
        ]
        
        sistemas = []
        for info in sistemas_info:
            detalle = getattr(self, info['attr'], None)
            if detalle:
                sistemas.append({
                    'nombre': info['nombre'],
                    'estado': self._get_estado_general_sistema(detalle),
                    'estado_color': self._get_color_estado_general(detalle),
                    'icono': info['icono']
                })
        return sistemas

    def get_sistemas_con_puntos(self):
        """Retorna sistemas con sus puntos para mostrar en detalle"""
        sistemas_info = [
            {'nombre': 'Motor', 'attr': 'detalle_motor', 'icono': 'gear'},
            {'nombre': 'Transmisión', 'attr': 'detalle_transmision', 'icono': 'gear-wide-connected'},
            {'nombre': 'Frenos', 'attr': 'detalle_frenos', 'icono': 'stop-circle'},
            {'nombre': 'Dirección/Suspensión', 'attr': 'detalle_direccion_suspension', 'icono': 'sliders'},
            {'nombre': 'Carrocería', 'attr': 'detalle_carroceria', 'icono': 'car-front'},
            {'nombre': 'Revisión General', 'attr': 'detalle_revision_general', 'icono': 'clipboard-check'},
            {'nombre': 'Interior', 'attr': 'detalle_interior', 'icono': 'cup-hot'}
        ]
        
        sistemas_con_puntos = []
        for info in sistemas_info:
            detalle = getattr(self, info['attr'], None)
            if detalle and hasattr(detalle, 'puntos'):
                sistemas_con_puntos.append({
                    'nombre': info['nombre'],
                    'icono': info['icono'],
                    'puntos': detalle.puntos.all()
                })
        return sistemas_con_puntos

    def _get_estado_general_sistema(self, detalle):
        if not hasattr(detalle, 'puntos'):
            return 'No revisado'
            
        puntos = detalle.puntos.all()
        if not puntos.exists():
            return 'No revisado'
        if all(p.estado == 'BUENO' for p in puntos):
            return 'Aprobado'
        if any(p.estado == 'RECHAZADO' for p in puntos):
            return 'Rechazado'
        return 'En revisión'

    def _get_color_estado_general(self, detalle):
        estado = self._get_estado_general_sistema(detalle)
        return {
            'Aprobado': 'success',
            'En revisión': 'warning',
            'Rechazado': 'danger',
            'No revisado': 'secondary'
        }.get(estado, 'secondary')

    @property
    def porcentaje_aprobacion(self):
        """Retorna el porcentaje de puntos aprobados"""
        total = self.get_total_puntos()
        if total == 0:
            return 0
        return (self.get_puntos_aprobados() / total) * 100

# --------------------------------------------
# Modelo para almacenar imágenes como texto
# --------------------------------------------
class ImagenTexto(models.Model):
    nombre = models.CharField(max_length=100)
    imagen_base64 = models.TextField()  # Guarda la imagen como texto

    def __str__(self):
        return self.nombre


# --------------------------------------------
# Detalle Motor y sus puntos con usuario y fecha
# --------------------------------------------
class DetalleMotor(models.Model):
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='detalle_motor')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_motor_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revisión motor de {self.vehiculo}'


class PuntoMotor(models.Model):
    NOMBRES_PUNTOS = [
        ('ruidos', 'Presencia de ruidos anormales en motor'),
        ('fugas', 'Fugas presentes en motor'),
        ('respuesta', 'Respuesta del motor'),
    ]

    detalle = models.ForeignKey(DetalleMotor, on_delete=models.CASCADE, related_name='puntos')
    nombre = models.CharField(max_length=20, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_motor_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"


# --------------------------------------------
# Detalle Transmisión y puntos con usuario y fecha
# --------------------------------------------
class DetalleTransmision(models.Model):
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='detalle_transmision')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_transmision_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revisión transmisión de {self.vehiculo}'


class PuntoTransmision(models.Model):
    NOMBRES_PUNTOS = [
        ('paso_marchas', 'Paso de marchas'),
        ('fugas_caja', 'Fugas presentes en caja'),
        ('estado_embrague', 'Estado de embrague'),
    ]

    detalle = models.ForeignKey(DetalleTransmision, on_delete=models.CASCADE, related_name='puntos')
    nombre = models.CharField(max_length=30, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_transmision_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"


# --------------------------------------------
# Detalle Frenos y puntos con usuario y fecha
# --------------------------------------------
class DetalleFrenos(models.Model):
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='detalle_frenos')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_frenos_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Revisión frenos de {self.vehiculo}'


class PuntoFrenos(models.Model):
    NOMBRES_PUNTOS = [
        ('frenado_correcto', 'Frenado correcto a distancia adecuada'),
        ('sonidos_frenar', 'Sonidos al momento de frenar'),
        ('olgura_freno_mano', 'Olgura de freno de mano'),
    ]

    detalle = models.ForeignKey(DetalleFrenos, on_delete=models.CASCADE, related_name='puntos')
    nombre = models.CharField(max_length=30, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_frenos_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"


# --------------------------------------------
# Detalle Dirección y Suspensión y puntos con usuario y fecha
# --------------------------------------------
class DetalleDireccionSuspension(models.Model):
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='detalle_direccion_suspension')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_direccion_suspension_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revisión Dirección y Suspensión de {self.vehiculo}"


class PuntoDireccionSuspension(models.Model):
    NOMBRES_PUNTOS = [
        ('amortiguadores', 'Amortiguadores en buen estado'),
        ('alineacion', 'Alineación'),
        ('balanceo', 'Balanceo'),
        ('ruidos_tren_delantero', 'Ruidos en tren delantero'),
        ('ruidos_tren_trasero', 'Ruidos en tren trasero'),
    ]

    detalle = models.ForeignKey(DetalleDireccionSuspension, on_delete=models.CASCADE, related_name='puntos')
    nombre = models.CharField(max_length=50, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_direccion_suspension_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"

# --------------------------------------------
# Detalle Carrocería y puntos con usuario y fecha
# --------------------------------------------
class DetalleCarroceria(models.Model):
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name='detalle_carroceria')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_carroceria_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revisión carrocería de {self.vehiculo}"


class PuntoCarroceria(models.Model):
    NOMBRES_PUNTOS = [
        ('estado_pintura', 'Estado de pintura'),
        ('abolladuras', 'Abolladuras o daños en carrocería'),
        ('estado_vidrios', 'Estado de vidrios'),
        ('alineacion_piezas', 'Alineación de piezas de carrocería'),
    ]

    detalle = models.ForeignKey(DetalleCarroceria, on_delete=models.CASCADE, related_name='puntos')
    nombre = models.CharField(max_length=50, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_carroceria_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"

# --------------------------------------------
# Detalle revision general con usuario y fecha
# --------------------------------------------

class DetalleRevisionGeneral(models.Model):
    vehiculo = models.OneToOneField(
        Vehiculo, 
        on_delete=models.CASCADE, 
        related_name='detalle_revision_general'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revisiones_generales_registradas'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revisión General de {self.vehiculo}"

class PuntoRevisionGeneral(models.Model):
    NOMBRES_PUNTOS = [
        ('estado_luces', 'Estado de luces'),
        ('nivel_liquidos', 'Nivel de líquidos'),
        ('kit_emergencia', 'Existencia de kit de emergencia'),
        ('bateria_alternador', 'Estado de batería y alternador'),
        ('presencia_dtc', 'Presencia de DTC'),
        ('estado_ruedas', 'Estado de rueda y profundidad'),
        ('rueda_repuesto', 'Rueda de repuesto'),
    ]

    detalle = models.ForeignKey(
        DetalleRevisionGeneral, 
        on_delete=models.CASCADE, 
        related_name='puntos'
    )
    nombre = models.CharField(max_length=50, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_revision_general_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"


# --------------------------------------------
# Detalle revision general con usuario y fecha
# --------------------------------------------


class DetalleInterior(models.Model):
    vehiculo = models.OneToOneField(
        Vehiculo, 
        on_delete=models.CASCADE, 
        related_name='detalle_interior'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_interior_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revisión Interior de {self.vehiculo}"

class PuntoInterior(models.Model):
    NOMBRES_PUNTOS = [
        ('estado_tapiz_butacas', 'Estado de tapiz y butacas'),
        ('funcionamiento_radio', 'Funcionamiento de radio'),
        ('desgaste_plasticos', 'Desgaste de plásticos'),
        ('accesorios_electricos', 'Estado de accesorios eléctricos'),
        ('estado_maleta', 'Estado de maleta'),
    ]

    detalle = models.ForeignKey(
        DetalleInterior, 
        on_delete=models.CASCADE, 
        related_name='puntos'
    )
    nombre = models.CharField(max_length=50, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='REVISION')
    observacion = models.TextField(blank=True, null=True)
    imagen_base64 = models.TextField(blank=True, null=True)
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puntos_interior_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('detalle', 'nombre')

    def __str__(self):
        return f"{self.get_nombre_display()} - {self.estado}"
    

# models.py (añade al final)
from django.db.models.signals import post_save
from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def crear_perfil_usuario(sender, instance, created, **kwargs):
#     if created:
#         PerfilUsuario.objects.create(usuario=instance)