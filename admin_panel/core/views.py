"""
Vistas custom para el panel de administración DxV
"""
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import Marca, Escenario, Zona, ZonaMunicipio


@staff_member_required
def distribucion_ventas(request):
    """
    Vista para distribuir ventas proyectadas entre zonas y municipios
    """
    marcas = Marca.objects.filter(activa=True).order_by('nombre')
    escenarios = Escenario.objects.filter(activo=True).order_by('-anio', 'nombre')

    # Obtener filtros seleccionados
    marca_id = request.GET.get('marca')
    escenario_id = request.GET.get('escenario')

    marca_seleccionada = None
    escenario_seleccionado = None
    zonas = []
    municipios = []
    total_venta_zonas = Decimal('0')
    total_venta_municipios = Decimal('0')

    if marca_id and escenario_id:
        try:
            marca_seleccionada = Marca.objects.get(pk=marca_id)
            escenario_seleccionado = Escenario.objects.get(pk=escenario_id)

            # Obtener zonas de esta marca y escenario
            zonas = Zona.objects.filter(
                marca=marca_seleccionada,
                escenario=escenario_seleccionado,
                activo=True
            ).order_by('nombre')

            total_venta_zonas = sum(z.venta_proyectada for z in zonas)

            # Obtener todos los municipios de las zonas
            municipios = ZonaMunicipio.objects.filter(
                zona__marca=marca_seleccionada,
                zona__escenario=escenario_seleccionado,
                zona__activo=True
            ).select_related('zona', 'municipio').order_by('zona__nombre', 'municipio__nombre')

            total_venta_municipios = sum(m.venta_proyectada for m in municipios)

        except (Marca.DoesNotExist, Escenario.DoesNotExist):
            pass

    context = {
        'title': 'Distribución de Ventas',
        'marcas': marcas,
        'escenarios': escenarios,
        'marca_seleccionada': marca_seleccionada,
        'escenario_seleccionado': escenario_seleccionado,
        'zonas': zonas,
        'municipios': municipios,
        'total_venta_zonas': total_venta_zonas,
        'total_venta_municipios': total_venta_municipios,
        # Para el admin template
        'site_header': 'Sistema DxV - Panel de Administración',
        'has_permission': True,
    }

    return render(request, 'admin/core/distribucion_ventas.html', context)


@staff_member_required
@require_POST
def guardar_distribucion_ventas(request):
    """
    API para guardar los cambios de distribución de ventas
    """
    try:
        data = json.loads(request.body)
        tipo = data.get('tipo')  # 'zonas' o 'municipios'
        items = data.get('items', [])

        if tipo == 'zonas':
            for item in items:
                zona_id = item.get('id')
                venta = Decimal(str(item.get('venta', 0)))
                Zona.objects.filter(pk=zona_id).update(venta_proyectada=venta)

            # Recalcular participaciones
            if items:
                primera_zona = Zona.objects.get(pk=items[0]['id'])
                primera_zona._recalcular_participaciones_marca()

        elif tipo == 'municipios':
            zonas_afectadas = set()
            for item in items:
                mun_id = item.get('id')
                venta = Decimal(str(item.get('venta', 0)))
                zm = ZonaMunicipio.objects.select_related('zona').get(pk=mun_id)
                zm.venta_proyectada = venta
                zm.save(update_fields=['venta_proyectada'])
                zonas_afectadas.add(zm.zona_id)

            # Recalcular participaciones por zona
            for zona_id in zonas_afectadas:
                zona = Zona.objects.get(pk=zona_id)
                ZonaMunicipio._recalcular_participaciones_zona(zona)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
