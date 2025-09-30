from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Vehiculo, Empresa, PerfilUsuario, ImagenTexto,
    DetalleMotor, PuntoMotor, PuntoMotorImagen,
    DetalleTransmision, PuntoTransmision, PuntoTransmisionImagen,
    DetalleFrenos, PuntoFrenos, PuntoFrenosImagen,
    DetalleDireccionSuspension, PuntoDireccionSuspension, PuntoDireccionSuspensionImagen,
    DetalleCarroceria, PuntoCarroceria, PuntoCarroceriaImagen,
    DetalleRevisionGeneral, PuntoRevisionGeneral, PuntoRevisionGeneralImagen,
    DetalleInterior, PuntoInterior, PuntoInteriorImagen
)

# --------------------------------------------------
# Inlines para Imágenes de cada tipo de punto
# --------------------------------------------------
class PuntoMotorImagenInline(admin.TabularInline):
    model = PuntoMotorImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

class PuntoTransmisionImagenInline(admin.TabularInline):
    model = PuntoTransmisionImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

class PuntoFrenosImagenInline(admin.TabularInline):
    model = PuntoFrenosImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

class PuntoDireccionSuspensionImagenInline(admin.TabularInline):
    model = PuntoDireccionSuspensionImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

class PuntoCarroceriaImagenInline(admin.TabularInline):
    model = PuntoCarroceriaImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

class PuntoRevisionGeneralImagenInline(admin.TabularInline):
    model = PuntoRevisionGeneralImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

class PuntoInteriorImagenInline(admin.TabularInline):
    model = PuntoInteriorImagen
    extra = 0
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:50px; max-width:75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'

# --------------------------------------------------
# Inlines para Puntos de cada sistema
# --------------------------------------------------
class PuntoMotorInline(admin.TabularInline):
    model = PuntoMotor
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

class PuntoTransmisionInline(admin.TabularInline):
    model = PuntoTransmision
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

class PuntoFrenosInline(admin.TabularInline):
    model = PuntoFrenos
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

class PuntoDireccionSuspensionInline(admin.TabularInline):
    model = PuntoDireccionSuspension
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

class PuntoCarroceriaInline(admin.TabularInline):
    model = PuntoCarroceria
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

class PuntoRevisionGeneralInline(admin.TabularInline):
    model = PuntoRevisionGeneral
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

class PuntoInteriorInline(admin.TabularInline):
    model = PuntoInterior
    extra = 0
    readonly_fields = ('usuario', 'fecha_registro')
    fields = ('nombre', 'estado', 'observacion', 'usuario', 'fecha_registro')

# --------------------------------------------------
# Admins para Detalles (sistemas principales)
# --------------------------------------------------
@admin.register(DetalleMotor)
class DetalleMotorAdmin(admin.ModelAdmin):
    inlines = [PuntoMotorInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

@admin.register(DetalleTransmision)
class DetalleTransmisionAdmin(admin.ModelAdmin):
    inlines = [PuntoTransmisionInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

@admin.register(DetalleFrenos)
class DetalleFrenosAdmin(admin.ModelAdmin):
    inlines = [PuntoFrenosInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

@admin.register(DetalleDireccionSuspension)
class DetalleDireccionSuspensionAdmin(admin.ModelAdmin):
    inlines = [PuntoDireccionSuspensionInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

@admin.register(DetalleCarroceria)
class DetalleCarroceriaAdmin(admin.ModelAdmin):
    inlines = [PuntoCarroceriaInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

@admin.register(DetalleRevisionGeneral)
class DetalleRevisionGeneralAdmin(admin.ModelAdmin):
    inlines = [PuntoRevisionGeneralInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

@admin.register(DetalleInterior)
class DetalleInteriorAdmin(admin.ModelAdmin):
    inlines = [PuntoInteriorInline]
    list_display = ('vehiculo', 'usuario', 'fecha_revision')
    list_select_related = ('vehiculo', 'usuario')
    readonly_fields = ('fecha_revision',)

# --------------------------------------------------
# Admins para Puntos individuales (con imágenes)
# --------------------------------------------------
@admin.register(PuntoMotor)
class PuntoMotorAdmin(admin.ModelAdmin):
    inlines = [PuntoMotorImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

@admin.register(PuntoTransmision)
class PuntoTransmisionAdmin(admin.ModelAdmin):
    inlines = [PuntoTransmisionImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

@admin.register(PuntoFrenos)
class PuntoFrenosAdmin(admin.ModelAdmin):
    inlines = [PuntoFrenosImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

@admin.register(PuntoDireccionSuspension)
class PuntoDireccionSuspensionAdmin(admin.ModelAdmin):
    inlines = [PuntoDireccionSuspensionImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

@admin.register(PuntoCarroceria)
class PuntoCarroceriaAdmin(admin.ModelAdmin):
    inlines = [PuntoCarroceriaImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

@admin.register(PuntoRevisionGeneral)
class PuntoRevisionGeneralAdmin(admin.ModelAdmin):
    inlines = [PuntoRevisionGeneralImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

@admin.register(PuntoInterior)
class PuntoInteriorAdmin(admin.ModelAdmin):
    inlines = [PuntoInteriorImagenInline]
    list_display = ('nombre', 'estado', 'detalle', 'usuario', 'fecha_registro')
    list_filter = ('estado', 'nombre')
    readonly_fields = ('fecha_registro',)
    list_select_related = ('detalle', 'usuario')

# --------------------------------------------------
# Admin para Vehículo
# --------------------------------------------------
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'patente', 'marca', 'modelo', 'usuario', 'fecha_registro', 'image_preview')
    list_display_links = ('numero_orden', 'patente')
    search_fields = ('patente', 'marca', 'modelo', 'numero_orden')
    list_filter = ('marca', 'fecha_registro')
    readonly_fields = ('numero_orden', 'fecha_registro', 'image_preview_large')
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:30px; max-width:45px;" />',
                obj.imagen_base64
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista Previa'
    
    def image_preview_large(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:200px; max-width:300px;" />',
                obj.imagen_base64
            )
        return "Sin imagen"
    image_preview_large.short_description = 'Imagen del Vehículo'

# --------------------------------------------------
# Admins para modelos auxiliares
# --------------------------------------------------
@admin.register(ImagenTexto)
class ImagenTextoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'image_preview')
    readonly_fields = ('image_preview_large',)
    
    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:30px; max-width:45px;" />',
                obj.imagen_base64
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista Previa'
    
    def image_preview_large(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height:200px; max-width:300px;" />',
                obj.imagen_base64
            )
        return "Sin imagen"
    image_preview_large.short_description = 'Imagen Completa'

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

# --------------------------------------------------
# Configuración de Usuario con Perfil
# --------------------------------------------------
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'

class CustomUserAdmin(UserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_empresa', 'get_cargo', 'is_staff')
    list_select_related = ('perfilusuario', 'perfilusuario__empresa')
    
    def get_empresa(self, obj):
        if hasattr(obj, 'perfilusuario') and obj.perfilusuario.empresa:
            return obj.perfilusuario.empresa.nombre
        return "Sin empresa"
    get_empresa.short_description = 'Empresa'
    
    def get_cargo(self, obj):
        if hasattr(obj, 'perfilusuario'):
            return obj.perfilusuario.get_cargo_display()
        return "Sin cargo"
    get_cargo.short_description = 'Cargo'

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'cargo')
    list_select_related = ('usuario', 'empresa')
    search_fields = ('usuario__username', 'empresa__nombre')
    list_filter = ('cargo', 'empresa')

# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)