from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.db.models.functions import TruncDate
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Vehiculo, DetalleMotor, PuntoMotor, PuntoMotorImagen,
    DetalleTransmision, PuntoTransmision, PuntoTransmisionImagen,
    DetalleFrenos, PuntoFrenos, PuntoFrenosImagen,
    DetalleDireccionSuspension, PuntoDireccionSuspension, PuntoDireccionSuspensionImagen,
    DetalleCarroceria, PuntoCarroceria, PuntoCarroceriaImagen,
    DetalleRevisionGeneral, PuntoRevisionGeneral, PuntoRevisionGeneralImagen,
    DetalleInterior, PuntoInterior, PuntoInteriorImagen
)

ESTADOS = [
    ('BUENO', 'Bueno'),
    ('OBSERVACION', 'Con Observación'),
    ('RECHAZADO', 'Rechazado'),
]

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
# Página principal
# ------------------------------
@login_required
def index(request):
    user = request.user
    hoy = timezone.now().date()
    
    # Obtener vehículos según permisos
    if user.is_superuser:
        vehiculos = Vehiculo.objects.all()
    else:
        try:
            perfil = user.perfilusuario
            
            if perfil.cargo == 'TECNICO':
                vehiculos = Vehiculo.objects.filter(usuario=user)
            elif perfil.cargo in ['JEFE', 'GERENTE']:
                vehiculos = Vehiculo.objects.filter(
                    usuario__perfilusuario__empresa=perfil.empresa
                )
            else:
                vehiculos = Vehiculo.objects.none()
        except AttributeError:
            vehiculos = Vehiculo.objects.none()

    # Datos para el gráfico (últimos 7 días)
    fecha_inicio = hoy - timezone.timedelta(days=6)
    registros_por_dia = (
        vehiculos.filter(fecha_registro__date__gte=fecha_inicio)
        .annotate(dia=TruncDate('fecha_registro'))
        .values('dia')
        .annotate(cantidad=Count('id'))
        .order_by('dia')
    )

    # Crear diccionario para los últimos 7 días
    datos_grafico = {fecha_inicio + timezone.timedelta(days=i): 0 for i in range(7)}
    
    for registro in registros_por_dia:
        datos_grafico[registro['dia']] = registro['cantidad']

    fechas = [dia.strftime('%Y-%m-%d') for dia in sorted(datos_grafico.keys())]
    cantidades = [datos_grafico[dia] for dia in sorted(datos_grafico.keys())]

    # Calcular estadísticas
    total_vehiculos = vehiculos.count()
    revisiones_hoy = vehiculos.filter(fecha_registro__date=hoy).count()
    
    mantenimientos_pendientes = vehiculos.filter(
        Q(detalle_motor__puntos__estado='RECHAZADO') |
        Q(detalle_transmision__puntos__estado='RECHAZADO') |
        Q(detalle_frenos__puntos__estado='RECHAZADO') |
        Q(detalle_direccion_suspension__puntos__estado='RECHAZADO')
    ).distinct().count()

    # Obtener información del perfil
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
            perfil = user.perfilusuario
            
            if perfil.cargo == 'TECNICO':
                vehiculos = Vehiculo.objects.filter(usuario=user)
            elif perfil.cargo in ['JEFE', 'GERENTE']:
                vehiculos = Vehiculo.objects.filter(
                    usuario__perfilusuario__empresa=perfil.empresa
                )
            else:
                vehiculos = Vehiculo.objects.none()
        except AttributeError:
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

    # Obtener información del perfil
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
# Función auxiliar para procesar puntos con múltiples imágenes
# ------------------------------
def procesar_punto_con_imagenes(detalle, punto_model, punto_imagen_model, clave, request):
    """Procesa un punto con sus múltiples imágenes"""
    estado = request.POST.get(f'estado_{clave}')
    observacion = request.POST.get(f'observaciones_{clave}')
    imagenes_base64 = request.POST.getlist(f'imagenes_{clave}[]')

    if estado or observacion is not None or imagenes_base64:
        punto, _ = punto_model.objects.get_or_create(
            detalle=detalle, 
            nombre=clave, 
            defaults={'usuario': request.user}
        )

        punto.estado = estado or punto.estado
        punto.observacion = observacion if observacion is not None else punto.observacion
        punto.usuario = request.user
        punto.save()

        # Procesar imágenes
        for imagen_base64 in imagenes_base64:
            if imagen_base64.strip():
                punto_imagen_model.objects.create(
                    punto=punto,
                    imagen_base64=imagen_base64,
                    usuario=request.user
                )

    return punto


# ------------------------------
# Detalle Motor
# ------------------------------
@login_required
def agregar_detalle_motor(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_motor, created = DetalleMotor.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_motor = [
        ('ruidos', 'Presencia de ruidos anormales en motor'),
        ('fugas', 'Fugas presentes en motor'),
        ('respuesta', 'Respuesta del motor'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_motor:
            procesar_punto_con_imagenes(
                detalle_motor, PuntoMotor, PuntoMotorImagen, clave, request
            )

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
# Detalle Transmisión
# ------------------------------
@login_required
def agregar_detalle_transmision(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_transmision, created = DetalleTransmision.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_transmision = [
        ('paso_marchas', 'Paso de marchas'),
        ('fugas_caja', 'Fugas presentes en caja'),
        ('estado_embrague', 'Estado de embrague'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_transmision:
            procesar_punto_con_imagenes(
                detalle_transmision, PuntoTransmision, PuntoTransmisionImagen, clave, request
            )

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
# Detalle Frenos
# ------------------------------
@login_required
def agregar_detalle_frenos(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_frenos, created = DetalleFrenos.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_frenos = [
        ('frenado_correcto', 'Frenado correcto a distancia adecuada'),
        ('sonidos_frenar', 'Sonidos al momento de frenar'),
        ('olgura_freno_mano', 'Olgura de freno de mano'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_frenos:
            procesar_punto_con_imagenes(
                detalle_frenos, PuntoFrenos, PuntoFrenosImagen, clave, request
            )

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
# Detalle Dirección y Suspensión
# ------------------------------
@login_required
def agregar_detalle_direccion_suspension(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    detalle_direccion_suspension, created = DetalleDireccionSuspension.objects.get_or_create(
        vehiculo=vehiculo, 
        defaults={'usuario': request.user}
    )

    puntos_direccion_suspension = [
        ('amortiguadores', 'Amortiguadores en buen estado'),
        ('alineacion', 'Alineación'),
        ('balanceo', 'Balanceo'),
        ('ruidos_tren_delantero', 'Ruidos en tren delantero'),
        ('ruidos_tren_trasero', 'Ruidos en tren trasero'),
    ]

    if request.method == 'POST':
        for clave, label in puntos_direccion_suspension:
            procesar_punto_con_imagenes(
                detalle_direccion_suspension, PuntoDireccionSuspension, 
                PuntoDireccionSuspensionImagen, clave, request
            )

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
# Detalle Carrocería
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

    if request.method == 'POST':
        for clave, label in puntos_carroceria:
            procesar_punto_con_imagenes(
                detalle_carroceria, PuntoCarroceria, PuntoCarroceriaImagen, clave, request
            )

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
# Revisión General
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

    if request.method == 'POST':
        for clave, label in puntos_revision:
            procesar_punto_con_imagenes(
                detalle_revision, PuntoRevisionGeneral, PuntoRevisionGeneralImagen, clave, request
            )

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

    if request.method == 'POST':
        for clave, label in puntos_interior:
            procesar_punto_con_imagenes(
                detalle_interior, PuntoInterior, PuntoInteriorImagen, clave, request
            )

        messages.success(request, "Detalle del interior guardado correctamente.")
        return redirect('ver_reporte_vehiculo', id=vehiculo.id)

    puntos = {p.nombre: p for p in detalle_interior.puntos.all()}

    return render(request, 'vehiculos/detalle_interior.html', {
        'vehiculo': vehiculo,
        'puntos_interior': puntos_interior,
        'puntos': puntos,
        'ESTADOS': ESTADOS,
    })


# ------------------------------
# Ver reporte completo del vehículo
# ------------------------------
@login_required
def ver_reporte_vehiculo(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    
    # Obtener todos los detalles y puntos
    detalles = {}
    sistemas = [
        ('detalle_motor', 'puntos_motor'),
        ('detalle_transmision', 'puntos_transmision'),
        ('detalle_frenos', 'puntos_frenos'),
        ('detalle_direccion_suspension', 'puntos_direccion_suspension'),
        ('detalle_carroceria', 'puntos_carroceria'),
        ('detalle_revision_general', 'puntos_revision_general'),
        ('detalle_interior', 'puntos_interior'),
    ]

    # Obtener todos los puntos organizados por sistema para la sección de detalles avanzados
    sistemas_con_puntos = []
    todos_los_puntos = []  # Lista para almacenar todos los puntos
    
    for detalle_attr, puntos_attr in sistemas:
        detalle = getattr(vehiculo, detalle_attr, None)
        puntos = detalle.puntos.all() if detalle else []
        puntos_dict = {p.nombre: p for p in puntos}
        
        detalles[detalle_attr] = detalle
        detalles[puntos_attr] = puntos_dict
        
        # Agregar a la lista de todos los puntos
        todos_los_puntos.extend(puntos)
        
        # Para la sección de detalles avanzados
        if detalle and puntos:
            sistema_info = {
                'nombre': detalle_attr.replace('detalle_', '').replace('_', ' ').title(),
                'icono': get_sistema_icon(detalle_attr),
                'puntos': puntos
            }
            sistemas_con_puntos.append(sistema_info)

    # Calcular estadísticas para el resumen usando la lista de todos los puntos
    total_puntos = len(todos_los_puntos)
    puntos_buenos = sum(1 for p in todos_los_puntos if p.estado == 'BUENO')
    puntos_observacion = sum(1 for p in todos_los_puntos if p.estado == 'OBSERVACION')
    puntos_rechazados = sum(1 for p in todos_los_puntos if p.estado == 'RECHAZADO')

    return render(request, 'vehiculos/ver_reporte.html', {
        'vehiculo': vehiculo,
        'sistemas_con_puntos': sistemas_con_puntos,
        'total_puntos': total_puntos,
        'puntos_buenos': puntos_buenos,
        'puntos_observacion': puntos_observacion,
        'puntos_rechazados': puntos_rechazados,
        **detalles
    })

def get_sistema_icon(detalle_attr):
    """Devuelve el ícono correspondiente para cada sistema"""
    iconos = {
        'detalle_motor': 'gear',
        'detalle_transmision': 'gear-wide-connected',
        'detalle_frenos': 'stop-circle',
        'detalle_direccion_suspension': 'sliders',
        'detalle_carroceria': 'car-front',
        'detalle_revision_general': 'clipboard-check',
        'detalle_interior': 'cup-hot'
    }
    return iconos.get(detalle_attr, 'circle')



# views.py
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def send_pdf_email(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del formulario
            pdf_file = request.FILES['pdf']
            email = request.POST['email']
            subject = request.POST['subject']
            message = request.POST['message']
            
            # Crear el email
            email_msg = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,  # Desde
                [email],  # Para
            )
            
            # Adjuntar el PDF
            email_msg.attach(
                pdf_file.name,
                pdf_file.read(),
                'application/pdf'
            )
            
            # Enviar el correo
            email_msg.send()
            
            return JsonResponse({'success': True, 'message': 'Correo enviado correctamente'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})