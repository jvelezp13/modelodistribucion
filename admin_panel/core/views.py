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

from .models import (
    Marca, Escenario, Zona, ZonaMunicipio, Municipio,
    Operacion, MarcaOperacion, ProyeccionVentasConfig
)


@staff_member_required
def distribucion_ventas(request):
    """
    Vista para distribuir ventas proyectadas entre operaciones, zonas y municipios.

    Flujo de configuración:
    1. ProyeccionVentasConfig → Venta total mensual de la marca
    2. MarcaOperacion.participacion_ventas → % por operación
    3. Zona.participacion_ventas → % dentro de la operación
    4. ZonaMunicipio.participacion_ventas → % dentro de la zona

    Las ventas se calculan automáticamente en cascada.
    """
    from .admin_site import dxv_admin_site

    marcas = Marca.objects.filter(activa=True).order_by('nombre')
    escenarios = Escenario.objects.filter(activo=True).order_by('-anio', 'nombre')

    # Obtener filtros seleccionados
    marca_id = request.GET.get('marca')
    escenario_id = request.GET.get('escenario')
    operacion_id = request.GET.get('operacion')

    marca_seleccionada = None
    escenario_seleccionado = None
    operacion_seleccionada = None
    operaciones = []  # Operaciones disponibles para el escenario
    marcas_operacion = []  # MarcaOperacion para distribución por operación
    zonas = []
    zonas_municipios = []  # Lista de zonas con sus municipios

    # Totales
    venta_total_marca = Decimal('0')  # Venta mensual de ProyeccionVentasConfig
    total_participacion_operaciones = Decimal('0')
    total_participacion_zonas = Decimal('0')
    total_venta_zonas = Decimal('0')
    total_venta_zonas_municipios = Decimal('0')

    if marca_id and escenario_id:
        try:
            marca_seleccionada = Marca.objects.get(pk=marca_id)
            escenario_seleccionado = Escenario.objects.get(pk=escenario_id)

            # Obtener operaciones del escenario
            operaciones = Operacion.objects.filter(
                escenario=escenario_seleccionado,
                activa=True
            ).order_by('nombre')

            # Obtener venta total mensual de la marca desde ProyeccionVentasConfig
            try:
                config = ProyeccionVentasConfig.objects.get(
                    marca=marca_seleccionada,
                    escenario=escenario_seleccionado,
                    anio=escenario_seleccionado.anio
                )
                ventas_mensuales = config.calcular_ventas_mensuales()
                if ventas_mensuales:
                    venta_total_marca = sum(ventas_mensuales.values()) / len(ventas_mensuales)
            except ProyeccionVentasConfig.DoesNotExist:
                pass

            # Obtener MarcaOperacion para distribución por operación
            marcas_operacion = list(MarcaOperacion.objects.filter(
                marca=marca_seleccionada,
                operacion__escenario=escenario_seleccionado,
                activo=True
            ).select_related('operacion').order_by('operacion__nombre'))

            # Debug: imprimir valores cargados
            for mo in marcas_operacion:
                print(f"DEBUG MarcaOperacion id={mo.id}, operacion={mo.operacion.nombre}, participacion={mo.participacion_ventas}")

            total_participacion_operaciones = sum(mo.participacion_ventas for mo in marcas_operacion)

            # Si hay operación seleccionada, filtrar zonas por ella
            if operacion_id:
                try:
                    operacion_seleccionada = Operacion.objects.get(pk=operacion_id)
                except Operacion.DoesNotExist:
                    operacion_seleccionada = None

            # Obtener zonas (filtradas por operación si está seleccionada)
            zonas_qs = Zona.objects.filter(
                marca=marca_seleccionada,
                escenario=escenario_seleccionado,
                activo=True
            ).select_related('operacion').order_by('operacion__nombre', 'nombre')

            if operacion_seleccionada:
                zonas_qs = zonas_qs.filter(operacion=operacion_seleccionada)

            zonas = list(zonas_qs)
            total_participacion_zonas = sum(z.participacion_ventas for z in zonas)
            total_venta_zonas = sum(z.venta_proyectada for z in zonas)

            # Obtener zonas con sus municipios (ZonaMunicipio)
            for zona in zonas:
                zona_municipios = ZonaMunicipio.objects.filter(
                    zona=zona
                ).select_related('municipio').order_by('municipio__nombre')

                total_participacion_zona = sum(zm.participacion_ventas for zm in zona_municipios)
                total_venta_zona = sum(zm.venta_proyectada for zm in zona_municipios)
                total_venta_zonas_municipios += total_venta_zona

                zonas_municipios.append({
                    'zona': zona,
                    'municipios': zona_municipios,
                    'total_participacion': total_participacion_zona,
                    'total_venta': total_venta_zona,
                })

        except (Marca.DoesNotExist, Escenario.DoesNotExist):
            pass

    # Obtener contexto base del admin (incluye app_list para sidebar)
    context = dxv_admin_site.each_context(request)
    context.update({
        'title': 'Distribución de Ventas',
        'marcas': marcas,
        'escenarios': escenarios,
        'operaciones': operaciones,
        'marca_seleccionada': marca_seleccionada,
        'escenario_seleccionado': escenario_seleccionado,
        'operacion_seleccionada': operacion_seleccionada,
        'venta_total_marca': venta_total_marca,
        'marcas_operacion': marcas_operacion,
        'total_participacion_operaciones': total_participacion_operaciones,
        'zonas': zonas,
        'zonas_municipios': zonas_municipios,
        'total_participacion_zonas': total_participacion_zonas,
        'total_venta_zonas': total_venta_zonas,
        'total_venta_zonas_municipios': total_venta_zonas_municipios,
    })

    return render(request, 'admin/core/distribucion_ventas.html', context)


@staff_member_required
@require_POST
def guardar_distribucion_ventas(request):
    """
    API para guardar los cambios de distribución de ventas (participaciones %).

    Flujo:
    - Usuario edita participacion_ventas (%)
    - Validación estricta: la suma debe ser exactamente 100%
    - Al guardar, se actualiza participacion_ventas
    - El modelo.save() calcula automáticamente venta_proyectada
    - La cascada propaga los cambios hacia abajo
    """
    try:
        data = json.loads(request.body)
        tipo = data.get('tipo')  # 'operaciones', 'zonas', 'zonas_municipios'
        items = data.get('items', [])

        if tipo == 'operaciones':
            # Validar que la suma sea exactamente 100%
            total = sum(Decimal(str(item.get('participacion', 0))) for item in items)
            if abs(total - Decimal('100')) > Decimal('0.01'):
                return JsonResponse({
                    'success': False,
                    'error': f'Las participaciones de operaciones deben sumar 100%. Actual: {total}%'
                }, status=400)

            # Guardar participaciones de MarcaOperacion
            for item in items:
                mo_id = item.get('id')
                participacion = Decimal(str(item.get('participacion', 0)))
                print(f"DEBUG Guardando MarcaOperacion id={mo_id}, participacion={participacion}")
                mo = MarcaOperacion.objects.get(pk=mo_id)
                mo.participacion_ventas = participacion
                mo.save()
                # Verificar que se guardó
                mo.refresh_from_db()
                print(f"DEBUG Después de guardar: id={mo.id}, participacion={mo.participacion_ventas}")

        elif tipo == 'zonas':
            # Agrupar zonas por operación y validar que cada grupo sume 100%
            zonas_por_operacion = {}
            for item in items:
                zona = Zona.objects.get(pk=item.get('id'))
                op_id = zona.operacion_id if zona.operacion_id else 'sin_operacion'
                if op_id not in zonas_por_operacion:
                    zonas_por_operacion[op_id] = {
                        'nombre': zona.operacion.nombre if zona.operacion else 'Sin operación',
                        'items': []
                    }
                zonas_por_operacion[op_id]['items'].append(item)

            # Validar cada operación
            for op_id, op_data in zonas_por_operacion.items():
                total = sum(Decimal(str(item.get('participacion', 0))) for item in op_data['items'])
                if abs(total - Decimal('100')) > Decimal('0.01'):
                    return JsonResponse({
                        'success': False,
                        'error': f'Las zonas de "{op_data["nombre"]}" deben sumar 100%. Actual: {total}%'
                    }, status=400)

            # Guardar participaciones de Zona
            for item in items:
                zona_id = item.get('id')
                participacion = Decimal(str(item.get('participacion', 0)))
                zona = Zona.objects.get(pk=zona_id)
                zona.participacion_ventas = participacion
                zona.save()

        elif tipo == 'zonas_municipios':
            # Validar que la suma de municipios de la zona sea 100%
            zona_id = data.get('zona_id')
            total = sum(Decimal(str(item.get('participacion', 0))) for item in items)
            if abs(total - Decimal('100')) > Decimal('0.01'):
                zona = Zona.objects.get(pk=zona_id)
                return JsonResponse({
                    'success': False,
                    'error': f'Los municipios de "{zona.nombre}" deben sumar 100%. Actual: {total}%'
                }, status=400)

            # Guardar participaciones de ZonaMunicipio
            for item in items:
                zm_id = item.get('id')
                participacion = Decimal(str(item.get('participacion', 0)))
                zm = ZonaMunicipio.objects.get(pk=zm_id)
                zm.participacion_ventas = participacion
                zm.save()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


