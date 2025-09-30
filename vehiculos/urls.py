from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='vehiculos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('vehiculo/agregar/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('vehiculos/', views.listar_vehiculos, name='listar_vehiculos'),
    path('vehiculo/<int:id>/detalle-motor/', views.agregar_detalle_motor, name='detalle_motor'),

    path('vehiculo/<int:id>/reporte/', views.ver_reporte_vehiculo, name='ver_reporte_vehiculo'),
    path('vehiculo/<int:id>/detalle_transmision/', views.agregar_detalle_transmision, name='detalle_transmision'),
    path('vehiculo/<int:id>/detalle-frenos/', views.agregar_detalle_frenos, name='agregar_detalle_frenos'),

    path('vehiculo/<int:id>/detalle_direccion_suspension/', views.agregar_detalle_direccion_suspension, name='detalle_direccion_suspension'),
    path('vehiculo/<int:id>/detalle_carroceria/', views.agregar_detalle_carroceria, name='detalle_carroceria'),
    path('vehiculo/<int:id>/detalle_revision_general/', views.agregar_detalle_revision_general, name='detalle_revision_general'),
    path('vehiculo/<int:id>/detalle_interior/', views.agregar_detalle_interior, name='detalle_interior'),

    path('send-pdf-email/', views.send_pdf_email, name='send_pdf_email'),
]
