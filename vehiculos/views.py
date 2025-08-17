from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import (
    Vehiculo, DetalleMotor, PuntoMotor,
    DetalleTransmision, PuntoTransmision,
    DetalleFrenos, PuntoFrenos,
    DetalleDireccionSuspension, PuntoDireccionSuspension,DetalleCarroceria,PuntoCarroceria,PuntoRevisionGeneral,DetalleRevisionGeneral,DetalleInterior,PuntoInterior
)
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.db.models.functions import TruncDate
from django.db.models import Count


def obtener_empresa_usuario(user):
    """Obtiene la empresa asociada al usuario si existe"""
    if hasattr(user, 'perfil') and user.perfil.empresa:
        return user.perfil.empresa
    return None

def es_tecnico(user):
    return hasattr(user, 'perfil') and user.perfil.cargo.lower() == 'TECNICO'

def es_jefe(user):
    return hasattr(user, 'perfil') and user.perfil.cargo.lower() == 'jefe'

def es_gerente(user):
    return hasattr(user, 'perfil') and user.perfil.cargo.lower() == 'gerente'

# ------------------------------
# Login View
# ------------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Has iniciado sesión correctamente.")
            return redirect('index')
        else:
            messages.error(request, "Credenciales incorrectas, intenta de nuevo.")
            return render(request, 'vehiculos/login.html')
    return render(request, 'vehiculos/login.html')


# ------------------------------
# Página principal - muestra gráfico con conteo de vehículos por día
# ------------------------------
from django.utils import timezone
from django.db.models import Q

@login_required
def index(request):
    user = request.user
    hoy = timezone.now().date()
    
    # 1. Obtener vehículos según permisos
    if user.is_superuser:
        vehiculos = Vehiculo.objects.all()
    else:
        try:
            perfil = user.perfilusuario  # Cambiado de 'perfil' a 'perfilusuario'
            
            if perfil.cargo == 'TECNICO':
                # Técnicos solo ven sus propios vehículos
                vehiculos = Vehiculo.objects.filter(usuario=user)
            elif perfil.cargo in ['JEFE', 'GERENTE']:
                # Jefes y gerentes ven los vehículos de su empresa
                vehiculos = Vehiculo.objects.filter(
                    usuario__perfilusuario__empresa=perfil.empresa
                )
            else:
                vehiculos = Vehiculo.objects.none()
        except AttributeError:
            # Si no tiene perfil
            vehiculos = Vehiculo.objects.none()

    # 2. Datos para el gráfico (últimos 7 días)
    fecha_inicio = hoy - timezone.timedelta(days=6)
    registros_por_dia = (
        vehiculos.filter(fecha_registro__date__gte=fecha_inicio)
        .annotate(dia=TruncDate('fecha_registro'))
        .values('dia')
        .annotate(cantidad=Count('id'))
        .order_by('dia')
    )

    # 3. Crear un diccionario completo para los últimos 7 días
    datos_grafico = {fecha_inicio + timezone.timedelta(days=i): 0 for i in range(7)}
    
    for registro in registros_por_dia:
        datos_grafico[registro['dia']] = registro['cantidad']

    fechas = [dia.strftime('%Y-%m-%d') for dia in sorted(datos_grafico.keys())]
    cantidades = [datos_grafico[dia] for dia in sorted(datos_grafico.keys())]

    # 4. Calcular estadísticas
    total_vehiculos = vehiculos.count()
    revisiones_hoy = vehiculos.filter(fecha_registro__date=hoy).count()
    
    # Vehículos con problemas (ejemplo: aquellos con algún punto rechazado)
    mantenimientos_pendientes = vehiculos.filter(
        Q(detalle_motor__puntos__estado='RECHAZADO') |
        Q(detalle_transmision__puntos__estado='RECHAZADO') |
        Q(detalle_frenos__puntos__estado='RECHAZADO') |
        Q(detalle_direccion_suspension__puntos__estado='RECHAZADO')
    ).distinct().count()

    # 5. Obtener información del perfil para mostrar
    try:
        perfil = user.perfilusuario
        empresa = perfil.empresa.nombre if perfil.empresa else "Sin empresa asignada"
        cargo = perfil.get_cargo_display()
    except AttributeError:
        empresa = "Sin perfil configurado"
        cargo = "Sin cargo asignado"

    context = {
        'fechas': fechas,
        'cantidades': cantidades,
        'total_vehiculos': total_vehiculos,
        'revisiones_hoy': revisiones_hoy,
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'hoy': hoy.strftime('%Y-%m-%d'),
        'empresa_usuario': empresa,
        'cargo_usuario': cargo,
    }
    return render(request, 'vehiculos/index.html', context)


# ------------------------------
# Agregar vehículo
# ------------------------------
@login_required
def agregar_vehiculo(request):
    if request.method == 'POST' and request.POST.get('imagen_base64'):
        imagen_base64 = request.POST['imagen_base64']
        patente = request.POST.get('patente')
        marca = request.POST['marca']
        modelo = request.POST['modelo']
        color = request.POST['color']
        tipo_bencina = request.POST['tipo_bencina']
        numero_motor = request.POST['numero_motor']

        ultimo = Vehiculo.objects.order_by('-numero_orden').first()
        numero_orden = (ultimo.numero_orden + 1) if ultimo else 1

        nuevo_vehiculo = Vehiculo.objects.create(
            numero_orden=numero_orden,
            patente=patente,
            marca=marca,
            modelo=modelo,
            color=color,
            tipo_bencina=tipo_bencina,
            numero_motor=numero_motor,
            imagen_base64=imagen_base64,
            usuario=request.user
        )

        return redirect('ver_reporte_vehiculo', id=nuevo_vehiculo.id)

    return render(request, 'vehiculos/agregar_vehiculo.html')



# ------------------------------
# Listar vehículos con filtro y paginación
# ------------------------------
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from .models import Vehiculo



@login_required
def listar_vehiculos(request):
    user = request.user
    query = request.GET.get('buscar')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    # Determinar el conjunto inicial de vehículos según permisos
    if user.is_superuser:
        vehiculos = Vehiculo.objects.all()
    else:
        try:
            perfil = user.perfilusuario  # Cambiado de 'perfil' a 'perfilusuario'
            
            if perfil.cargo == 'TECNICO':
                # Técnicos solo ven sus propios vehículos
                vehiculos = Vehiculo.objects.filter(usuario=user)
            elif perfil.cargo in ['JEFE', 'GERENTE']:
                # Jefes y gerentes ven los vehículos de su empresa
                vehiculos = Vehiculo.objects.filter(
                    usuario__perfilusuario__empresa=perfil.empresa
                )
            else:
                vehiculos = Vehiculo.objects.none()
        except AttributeError:
            # Si no tiene perfil
            vehiculos = Vehiculo.objects.none()

    # Aplicar filtros adicionales
    if query:
        vehiculos = vehiculos.filter(
            Q(patente__icontains=query) |
            Q(marca__icontains=query) |
            Q(modelo__icontains=query) |
            Q(numero_orden__icontains=query)
        )

    if fecha_desde:
        try:
            fecha_desde_parsed = parse_date(fecha_desde)
            if fecha_desde_parsed:
                vehiculos = vehiculos.filter(fecha_registro__date__gte=fecha_desde_parsed)
        except:
            pass

    if fecha_hasta:
        try:
            fecha_hasta_parsed = parse_date(fecha_hasta)
            if fecha_hasta_parsed:
                vehiculos = vehiculos.filter(fecha_registro__date__lte=fecha_hasta_parsed)
        except:
            pass

    # Paginación
    paginator = Paginator(vehiculos.order_by('-fecha_registro'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Determinar si el usuario puede ver opciones adicionales
    try:
        perfil = user.perfilusuario
        puede_ver_opciones = user.is_superuser or perfil.cargo in ['JEFE', 'GERENTE']
    except AttributeError:
        puede_ver_opciones = False

    # Obtener información del perfil para mostrar en template
    try:
        empresa_usuario = user.perfilusuario.empresa.nombre if user.perfilusuario.empresa else "Sin empresa"
        cargo_usuario = user.perfilusuario.get_cargo_display()
    except AttributeError:
        empresa_usuario = "Sin perfil"
        cargo_usuario = "Sin cargo"

    return render(request, 'vehiculos/listar_vehiculos.html', {
        'page_obj': page_obj,
        'buscar': query,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'puede_ver_opciones': puede_ver_opciones,
        'empresa_usuario': empresa_usuario,
        'cargo_usuario': cargo_usuario,
    })

# ------------------------------
# Agregar / editar detalle motor con usuario y fecha
# ------------------------------
@login_required
def agregar_detalle_motor(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_motor, created = DetalleMotor.objects.get_or_create(vehiculo=vehiculo, defaults={'usuario': request.user})

    puntos_motor = [
        ('ruidos', 'Presencia de ruidos anormales en motor'),
        ('fugas', 'Fugas presentes en motor'),
        ('respuesta', 'Respuesta del motor'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_motor:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoMotor.objects.get_or_create(detalle=detalle_motor, nombre=clave, defaults={'usuario': request.user})

                # Actualizar datos y usuario que modifica
                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle del motor guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_motor.puntos.all()}

    return render(request, 'vehiculos/detalle_motor.html', {
        'vehiculo': vehiculo,
        'puntos_motor': puntos_motor,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })


# ------------------------------
# Agregar / editar detalle transmisión
# ------------------------------
@login_required
def agregar_detalle_transmision(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_transmision, created = DetalleTransmision.objects.get_or_create(vehiculo=vehiculo, defaults={'usuario': request.user})

    puntos_transmision = [
        ('paso_marchas', 'Paso de marchas'),
        ('fugas_caja', 'Fugas presentes en caja'),
        ('estado_embrague', 'Estado de embrague'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_transmision:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoTransmision.objects.get_or_create(detalle=detalle_transmision, nombre=clave, defaults={'usuario': request.user})

                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle de transmisión guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_transmision.puntos.all()}

    return render(request, 'vehiculos/detalle_transmision.html', {
        'vehiculo': vehiculo,
        'puntos_transmision': puntos_transmision,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })


# ------------------------------
# Agregar / editar detalle frenos
# ------------------------------
@login_required
def agregar_detalle_frenos(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_frenos, created = DetalleFrenos.objects.get_or_create(vehiculo=vehiculo, defaults={'usuario': request.user})

    puntos_frenos = [
        ('frenado_correcto', 'Frenado correcto a distancia adecuada'),
        ('sonidos_frenar', 'Sonidos al momento de frenar'),
        ('olgura_freno_mano', 'Olgura de freno de mano'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_frenos:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoFrenos.objects.get_or_create(detalle=detalle_frenos, nombre=clave, defaults={'usuario': request.user})

                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle de frenos guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_frenos.puntos.all()}

    return render(request, 'vehiculos/detalle_frenos.html', {
        'vehiculo': vehiculo,
        'puntos_frenos': puntos_frenos,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })


# ------------------------------
# Agregar / editar detalle dirección y suspensión
# ------------------------------
@login_required
def agregar_detalle_direccion_suspension(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_direccion_suspension, created = DetalleDireccionSuspension.objects.get_or_create(vehiculo=vehiculo, defaults={'usuario': request.user})

    puntos_direccion_suspension = [
        ('amortiguadores', 'Amortiguadores en buen estado'),
        ('alineacion', 'Alineación'),
        ('balanceo', 'Balanceo'),
        ('ruidos_tren_delantero', 'Ruidos en tren delantero'),
        ('ruidos_tren_trasero', 'Ruidos en tren trasero'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_direccion_suspension:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoDireccionSuspension.objects.get_or_create(detalle=detalle_direccion_suspension, nombre=clave, defaults={'usuario': request.user})

                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle de Dirección y Suspensión guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_direccion_suspension.puntos.all()}

    return render(request, 'vehiculos/detalle_direccion_suspension.html', {
        'vehiculo': vehiculo,
        'puntos_direccion_suspension': puntos_direccion_suspension,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })


# ------------------------------
# Ver reporte completo del vehículo con todos los detalles y puntos
# ------------------------------
@login_required
def ver_reporte_vehiculo(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    
    # Detalles existentes
    detalle_motor = getattr(vehiculo, 'detalle_motor', None)
    puntos_motor = detalle_motor.puntos.all() if detalle_motor else []
    puntos_motor_dict = {p.nombre: p for p in puntos_motor}

    detalle_transmision = getattr(vehiculo, 'detalle_transmision', None)
    puntos_transmision = detalle_transmision.puntos.all() if detalle_transmision else []
    puntos_transmision_dict = {p.nombre: p for p in puntos_transmision}

    detalle_frenos = getattr(vehiculo, 'detalle_frenos', None)
    puntos_frenos = detalle_frenos.puntos.all() if detalle_frenos else []
    puntos_frenos_dict = {p.nombre: p for p in puntos_frenos}

    detalle_direccion_suspension = getattr(vehiculo, 'detalle_direccion_suspension', None)
    puntos_direccion_suspension = detalle_direccion_suspension.puntos.all() if detalle_direccion_suspension else []
    puntos_direccion_suspension_dict = {p.nombre: p for p in puntos_direccion_suspension}

    detalle_carroceria = getattr(vehiculo, 'detalle_carroceria', None)
    puntos_carroceria = detalle_carroceria.puntos.all() if detalle_carroceria else []
    puntos_carroceria_dict = {p.nombre: p for p in puntos_carroceria}

    # Revisión General
    detalle_revision_general = getattr(vehiculo, 'detalle_revision_general', None)
    puntos_revision_general = detalle_revision_general.puntos.all() if detalle_revision_general else []
    puntos_revision_general_dict = {p.nombre: p for p in puntos_revision_general}

    # Nuevo: Interior
    detalle_interior = getattr(vehiculo, 'detalle_interior', None)
    puntos_interior = detalle_interior.puntos.all() if detalle_interior else []
    puntos_interior_dict = {p.nombre: p for p in puntos_interior}

    return render(request, 'vehiculos/ver_reporte.html', {
        'vehiculo': vehiculo,
        'detalle_motor': detalle_motor,
        'puntos_motor': puntos_motor_dict,
        'detalle_transmision': detalle_transmision,
        'puntos_transmision': puntos_transmision_dict,
        'detalle_frenos': detalle_frenos,
        'puntos_frenos': puntos_frenos_dict,
        'detalle_direccion_suspension': detalle_direccion_suspension,
        'puntos_direccion_suspension': puntos_direccion_suspension_dict,
        'detalle_carroceria': detalle_carroceria,
        'puntos_carroceria': puntos_carroceria_dict,
        'detalle_revision_general': detalle_revision_general,
        'puntos_revision_general': puntos_revision_general_dict,
        'detalle_interior': detalle_interior,
        'puntos_interior': puntos_interior_dict,
    })
# ------------------------------
# Detalle Carroceria
# ------------------------------

@login_required
def agregar_detalle_carroceria(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_carroceria, created = DetalleCarroceria.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_carroceria = [
        ('estado_pintura', 'Estado de pintura'),
        ('abolladuras', 'Abolladuras o daños en carrocería'),
        ('estado_vidrios', 'Estado de vidrios'),
        ('alineacion_piezas', 'Alineación de piezas de carrocería'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_carroceria:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoCarroceria.objects.get_or_create(
                    detalle=detalle_carroceria, 
                    nombre=clave, 
                    defaults={'usuario': request.user}
                )

                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle de carrocería guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_carroceria.puntos.all()}

    return render(request, 'vehiculos/detalle_carroceria.html', {
        'vehiculo': vehiculo,
        'puntos_carroceria': puntos_carroceria,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })


# ------------------------------
# Revision General
# ------------------------------

@login_required
def agregar_detalle_revision_general(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_revision, created = DetalleRevisionGeneral.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_revision = [
        ('estado_luces', 'Estado de luces'),
        ('nivel_liquidos', 'Nivel de líquidos'),
        ('kit_emergencia', 'Existencia de kit de emergencia'),
        ('bateria_alternador', 'Estado de batería y alternador'),
        ('presencia_dtc', 'Presencia de DTC'),
        ('estado_ruedas', 'Estado de rueda y profundidad'),
        ('rueda_repuesto', 'Rueda de repuesto'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_revision:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoRevisionGeneral.objects.get_or_create(
                    detalle=detalle_revision, 
                    nombre=clave, 
                    defaults={'usuario': request.user}
                )

                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle de revisión general guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_revision.puntos.all()}

    return render(request, 'vehiculos/detalle_revision_general.html', {
        'vehiculo': vehiculo,
        'puntos_revision': puntos_revision,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })

# ------------------------------
# Detalle Interior
# ------------------------------


@login_required
def agregar_detalle_interior(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_interior, created = DetalleInterior.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_interior = [
        ('estado_tapiz_butacas', 'Estado de tapiz y butacas'),
        ('funcionamiento_radio', 'Funcionamiento de radio'),
        ('desgaste_plasticos', 'Desgaste de plásticos'),
        ('accesorios_electricos', 'Estado de accesorios eléctricos'),
        ('estado_maleta', 'Estado de maleta'),
    ]

    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REVISION', 'Requiere Revisión'),
        ('RECHAZADO', 'Rechazado'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_interior:
            estado = request.POST.get(f'estado_{clave}')
            observacion = request.POST.get(f'observaciones_{clave}')
            imagen_base64 = request.POST.get(f'imagen_{clave}')

            if estado or observacion is not None or imagen_base64:
                punto, _ = PuntoInterior.objects.get_or_create(
                    detalle=detalle_interior, 
                    nombre=clave, 
                    defaults={'usuario': request.user}
                )

                punto.estado = estado or punto.estado
                punto.observacion = observacion if observacion is not None else punto.observacion
                punto.imagen_base64 = imagen_base64 or punto.imagen_base64
                punto.usuario = request.user
                punto.save()

        messages.success(request, "Detalle del interior guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_interior.puntos.all()}

    return render(request, 'vehiculos/detalle_interior.html', {
        'vehiculo': vehiculo,
        'puntos_interior': puntos_interior,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })