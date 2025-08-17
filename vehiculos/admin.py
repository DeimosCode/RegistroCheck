from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Vehiculo,
    DetalleMotor, PuntoMotor,
    DetalleTransmision, PuntoTransmision,
    DetalleFrenos, PuntoFrenos,
    DetalleDireccionSuspension, PuntoDireccionSuspension,
    ImagenTexto,Empresa
)

# Inline para mostrar preview de imagen en cada Punto
class PuntoMotorInline(admin.TabularInline):
    model = PuntoMotor
    extra = 0
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height: 50px; max-width: 75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Imagen'


class PuntoTransmisionInline(admin.TabularInline):
    model = PuntoTransmision
    extra = 0
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height: 50px; max-width: 75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Imagen'


class PuntoFrenosInline(admin.TabularInline):
    model = PuntoFrenos
    extra = 0
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height: 50px; max-width: 75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Imagen'


class PuntoDireccionSuspensionInline(admin.TabularInline):
    model = PuntoDireccionSuspension
    extra = 0
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.imagen_base64:
            return format_html(
                '<img src="data:image/jpeg;base64,{}" style="max-height: 50px; max-width: 75px;" />',
                obj.imagen_base64
            )
        return "No hay imagen"
    image_preview.short_description = 'Imagen'

# Admin para modelos padre con inline de sus puntos
@admin.register(DetalleMotor)
class DetalleMotorAdmin(admin.ModelAdmin):
    inlines = [PuntoMotorInline]
    list_display = ('vehiculo', 'fecha_revision')

@admin.register(DetalleTransmision)
class DetalleTransmisionAdmin(admin.ModelAdmin):
    inlines = [PuntoTransmisionInline]
    list_display = ('vehiculo', 'fecha_revision')

@admin.register(DetalleFrenos)
class DetalleFrenosAdmin(admin.ModelAdmin):
    inlines = [PuntoFrenosInline]
    list_display = ('vehiculo', 'fecha_revision')

@admin.register(DetalleDireccionSuspension)
class DetalleDireccionSuspensionAdmin(admin.ModelAdmin):
    inlines = [PuntoDireccionSuspensionInline]
    list_display = ('vehiculo', 'fecha_revision')

# Admin simple para Vehiculo
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'patente', 'marca', 'modelo', 'color', 'tipo_bencina', 'numero_motor', 'fecha_registro')
    search_fields = ('patente', 'marca', 'modelo')

# Admin para ImagenTexto
@admin.register(ImagenTexto)
class ImagenTextoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

# admin.py
# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario, Empresa

# Opción 1: Mostrar PerfilUsuario inline con User
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfiles'

# Extender el UserAdmin
class CustomUserAdmin(UserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_empresa', 'get_cargo')
    
    def get_empresa(self, obj):
        return obj.perfilusuario.empresa
    get_empresa.short_description = 'Empresa'
    
    def get_cargo(self, obj):
        return obj.perfilusuario.get_cargo_display()
    get_cargo.short_description = 'Cargo'

# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Opción 2: Mostrar PerfilUsuario por separado
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'cargo')
    list_select_related = ('usuario', 'empresa')
    search_fields = ('usuario__username', 'empresa__nombre')
    list_filter = ('cargo', 'empresa')



@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')  # columnas visibles en el listado
    search_fields = ('nombre',)      # barra de búsqueda por nombre

