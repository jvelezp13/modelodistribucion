#!/usr/bin/env python3
"""
Script para diagnosticar diferencias entre P&G Detallado y P&G por Zonas.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'admin_panel'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()

from admin_panel.core.models import (
    Escenario, Marca, Zona,
    PersonalComercial, GastoComercial
)
from decimal import Decimal

escenario = Escenario.objects.filter(activo=True).first()
if not escenario:
    print("❌ No hay escenario activo")
    exit(1)

marca = Marca.objects.filter(activa=True).first()
if not marca:
    print("❌ No hay marca activa")
    exit(1)

print(f"📊 Escenario: {escenario.nombre}")
print(f"📦 Marca: {marca.nombre}")
print("=" * 100)

# 1. TOTAL P&G DETALLADO (Personal + Gastos Comerciales)
print("\n1️⃣  TOTAL P&G DETALLADO (COMERCIAL):")
print("-" * 100)

personal_comercial = PersonalComercial.objects.filter(escenario=escenario, marca=marca)
total_personal = sum(p.calcular_costo_mensual() for p in personal_comercial)
print(f"   Personal Comercial: ${total_personal:,.0f}")

gastos_comerciales = GastoComercial.objects.filter(escenario=escenario, marca=marca)
total_gastos = sum(g.valor_mensual for g in gastos_comerciales)
print(f"   Gastos Comerciales: ${total_gastos:,.0f}")

total_detallado = total_personal + total_gastos
print(f"   ✅ TOTAL COMERCIAL DETALLADO: ${total_detallado:,.0f}")

# 2. TOTAL P&G POR ZONAS (Suma de distribución a zonas)
print("\n2️⃣  TOTAL P&G POR ZONAS (COMERCIAL):")
print("-" * 100)

from api.pyg_service import calcular_pyg_todas_zonas

zonas_pyg = calcular_pyg_todas_zonas(escenario, marca)
total_zonas = sum(z['comercial']['total'] for z in zonas_pyg)
print(f"   ✅ TOTAL COMERCIAL EN ZONAS: ${total_zonas:,.0f}")

# 3. DIFERENCIA
print("\n3️⃣  DIFERENCIA:")
print("-" * 100)
diferencia = total_detallado - total_zonas
print(f"   📊 Diferencia: ${diferencia:,.0f}")
print(f"   📊 Porcentaje: {(diferencia / total_detallado * 100):.2f}%")

# 4. ANÁLISIS DE CAUSAS
print("\n4️⃣  ANÁLISIS DE POSIBLES CAUSAS:")
print("-" * 100)

# Verificar suma de participaciones
zonas_activas = Zona.objects.filter(escenario=escenario, marca=marca, activo=True)
suma_participaciones = sum(z.participacion_ventas or Decimal('0') for z in zonas_activas)
print(f"\n   📌 Suma de participaciones de zonas activas: {suma_participaciones}%")
if suma_participaciones < 100:
    falta = 100 - suma_participaciones
    print(f"   ⚠️  Falta {falta}% de participación → puede causar subdistribución de costos compartidos")

# Verificar personal/gastos compartidos o proporcionales
print(f"\n   📌 Personal Comercial por tipo de asignación:")
for tipo in ['directo', 'proporcional', 'compartido']:
    personal_tipo = personal_comercial.filter(tipo_asignacion_geo=tipo)
    count = personal_tipo.count()
    total_tipo = sum(p.calcular_costo_mensual() for p in personal_tipo)
    print(f"      - {tipo}: {count} registros → ${total_tipo:,.0f}")

print(f"\n   📌 Gastos Comerciales por tipo de asignación:")
for tipo in ['directo', 'proporcional', 'compartido']:
    gastos_tipo = gastos_comerciales.filter(tipo_asignacion_geo=tipo)
    count = gastos_tipo.count()
    total_tipo = sum(g.valor_mensual for g in gastos_tipo)
    print(f"      - {tipo}: {count} registros → ${total_tipo:,.0f}")

# Verificar gastos sin zona para tipo 'directo'
gastos_directos_sin_zona = gastos_comerciales.filter(tipo_asignacion_geo='directo', zona__isnull=True)
if gastos_directos_sin_zona.count() > 0:
    print(f"\n   ⚠️  Gastos con tipo='directo' pero sin zona asignada: {gastos_directos_sin_zona.count()}")
    for g in gastos_directos_sin_zona:
        print(f"      - {g.nombre}: ${g.valor_mensual:,.0f}")

# Verificar personal sin zona para tipo 'directo'
personal_directo_sin_zona = personal_comercial.filter(tipo_asignacion_geo='directo', zona__isnull=True)
if personal_directo_sin_zona.count() > 0:
    print(f"\n   ⚠️  Personal con tipo='directo' pero sin zona asignada: {personal_directo_sin_zona.count()}")
    for p in personal_directo_sin_zona:
        print(f"      - {p.cargo}: ${p.calcular_costo_mensual():,.0f}")

print("\n" + "=" * 100)
print("💡 CAUSAS COMUNES DE DIFERENCIA:")
print("   1. Participaciones de zonas no suman 100% → costos compartidos/proporcionales se subdistribuyen")
print("   2. Registros con tipo='directo' pero sin zona asignada → no se distribuyen a ninguna zona")
print("   3. Zonas inactivas con costos directos → no se incluyen en el total por zonas")
print("=" * 100)
