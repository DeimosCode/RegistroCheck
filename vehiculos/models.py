from django.db import models
from django.conf import settings
from django.utils import timezone
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


ESTADOS = [
    ('BUENO', 'Bueno'),
    ('OBSERVACION', 'Con Observación'),
    ('RECHAZADO', 'Rechazado'),
]


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

    def get_total_puntos(self):
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
        return self._contar_puntos_por_estado('BUENO')

    def get_puntos_revision(self):
        return self._contar_puntos_por_estado('REVISION')

    def get_puntos_rechazados(self):
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
        total = self.get_total_puntos()
        if total == 0:
            return 0
        return (self.get_puntos_aprobados() / total) * 100


class ImagenTexto(models.Model):
    nombre = models.CharField(max_length=100)
    imagen_base64 = models.TextField()

    def __str__(self):
        return self.nombre


# --------------------------------------------
# Modelo Base Abstracto para Imágenes
# --------------------------------------------
class ImagenPuntoBase(models.Model):
    imagen_base64 = models.TextField()
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"Imagen - {self.fecha_subida.strftime('%Y-%m-%d %H:%M')}"


# --------------------------------------------
# Detalle Motor
# --------------------------------------------
class DetalleMotor(models.Model):
    vehiculo = models.OneToOneField(
        Vehiculo,
        on_delete=models.CASCADE,
        related_name='detalle_motor'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalle_motor_registrados'
    )
    fecha_revision = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revisión motor de {self.vehiculo}"


class PuntoMotor(models.Model):
    NOMBRES_PUNTOS = [
        ('ruidos', 'Presencia de ruidos anormales en motor'),
        ('fugas', 'Fugas presentes en motor'),
        ('respuesta', 'Respuesta del motor'),
    ]

    detalle = models.ForeignKey(
        DetalleMotor,
        on_delete=models.CASCADE,
        related_name='puntos'
    )
    nombre = models.CharField(max_length=20, choices=NOMBRES_PUNTOS)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoMotorImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoMotor,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Motor: {self.punto.get_nombre_display()}"


# --------------------------------------------
# Detalle Transmisión
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
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoTransmisionImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoTransmision,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Transmisión: {self.punto.get_nombre_display()}"


# --------------------------------------------
# Detalle Frenos
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
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoFrenosImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoFrenos,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Frenos: {self.punto.get_nombre_display()}"


# --------------------------------------------
# Detalle Dirección y Suspensión
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
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoDireccionSuspensionImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoDireccionSuspension,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Dirección/Suspensión: {self.punto.get_nombre_display()}"


# --------------------------------------------
# Detalle Carrocería
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
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoCarroceriaImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoCarroceria,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Carrocería: {self.punto.get_nombre_display()}"


# --------------------------------------------
# Detalle Revisión General
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
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoRevisionGeneralImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoRevisionGeneral,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Revisión General: {self.punto.get_nombre_display()}"


# --------------------------------------------
# Detalle Interior
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
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')  # Cambiado a 15
    observacion = models.TextField(blank=True, null=True)
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

    def tiene_imagenes(self):
        return self.imagenes.exists()
    
    def cantidad_imagenes(self):
        return self.imagenes.count()


class PuntoInteriorImagen(ImagenPuntoBase):
    punto = models.ForeignKey(
        PuntoInterior,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )

    def __str__(self):
        return f"Interior: {self.punto.get_nombre_display()}"