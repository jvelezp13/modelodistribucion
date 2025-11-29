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

from .models import Marca, Escenario, Zona, VentaMunicipio, Municipio


@staff_member_required
def distribucion_ventas(request):
    """
    Vista para distribuir ventas proyectadas entre zonas y municipios
    """
    from .admin_site import dxv_admin_site

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

            # Obtener ventas por municipio (listado plano, independiente de zonas)
            municipios = VentaMunicipio.objects.filter(
                marca=marca_seleccionada,
                escenario=escenario_seleccionado
            ).select_related('municipio').order_by('municipio__departamento', 'municipio__nombre')

            total_venta_municipios = sum(m.venta_proyectada for m in municipios)

        except (Marca.DoesNotExist, Escenario.DoesNotExist):
            pass

    # Obtener municipios disponibles para agregar (que no estén ya en VentaMunicipio)
    municipios_disponibles = []
    if marca_seleccionada and escenario_seleccionado:
        municipios_ya_agregados = VentaMunicipio.objects.filter(
            marca=marca_seleccionada,
            escenario=escenario_seleccionado
        ).values_list('municipio_id', flat=True)

        municipios_disponibles = Municipio.objects.filter(
            activo=True
        ).exclude(
            id__in=municipios_ya_agregados
        ).order_by('departamento', 'nombre')

    # Obtener contexto base del admin (incluye app_list para sidebar)
    context = dxv_admin_site.each_context(request)
    context.update({
        'title': 'Distribución de Ventas',
        'marcas': marcas,
        'escenarios': escenarios,
        'marca_seleccionada': marca_seleccionada,
        'escenario_seleccionado': escenario_seleccionado,
        'zonas': zonas,
        'municipios': municipios,
        'municipios_disponibles': municipios_disponibles,
        'total_venta_zonas': total_venta_zonas,
        'total_venta_municipios': total_venta_municipios,
    })

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
            for item in items:
                vm_id = item.get('id')
                venta = Decimal(str(item.get('venta', 0)))
                VentaMunicipio.objects.filter(pk=vm_id).update(venta_proyectada=venta)

            # Recalcular participaciones
            if items:
                primer_vm = VentaMunicipio.objects.get(pk=items[0]['id'])
                primer_vm._recalcular_participaciones()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_member_required
@require_POST
def agregar_municipios_venta(request):
    """
    API para agregar municipios a VentaMunicipio
    """
    try:
        data = json.loads(request.body)
        marca_id = data.get('marca_id')
        escenario_id = data.get('escenario_id')
        municipio_ids = data.get('municipio_ids', [])

        marca = Marca.objects.get(pk=marca_id)
        escenario = Escenario.objects.get(pk=escenario_id)

        creados = 0
        for mun_id in municipio_ids:
            municipio = Municipio.objects.get(pk=mun_id)
            _, created = VentaMunicipio.objects.get_or_create(
                marca=marca,
                escenario=escenario,
                municipio=municipio,
                defaults={'venta_proyectada': 0}
            )
            if created:
                creados += 1

        return JsonResponse({'success': True, 'creados': creados})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
