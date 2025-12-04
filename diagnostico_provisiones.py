#!/usr/bin/env python3
"""
Script de diagnóstico para verificar por qué las provisiones no aparecen en P&G por Zonas.
Ejecutar desde: python3 diagnostico_provisiones.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'admin_panel'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()

from admin_panel.core.models import (
    Escenario, Marca, PoliticaRecursosHumanos, ParametrosMacro,
    GastoComercial, GastoLogistico, GastoAdministrativo,
    PersonalComercial, PersonalLogistico, PersonalAdministrativo
)
from decimal import Decimal


def diagnosticar():
    print("=" * 80)
    print("DIAGNÓSTICO DE PROVISIONES EN P&G POR ZONAS")
    print("=" * 80)
    print()

    # 1. Verificar escenario activo
    print("1️⃣  ESCENARIOS ACTIVOS:")
    print("-" * 80)
    escenarios = Escenario.objects.filter(activo=True)
    if not escenarios:
        print("❌ No hay escenarios activos")
        return

    for esc in escenarios:
        print(f"   ✅ {esc.nombre} (Año: {esc.anio}, ID: {esc.id})")
    print()

    # Usar el primer escenario activo
    escenario = escenarios.first()
    print(f"📊 Usando escenario: {escenario.nombre} (Año: {escenario.anio})")
    print()

    # 2. Verificar Política de RRHH
    print("2️⃣  POLÍTICA DE RECURSOS HUMANOS:")
    print("-" * 80)
    try:
        politica = PoliticaRecursosHumanos.objects.get(anio=escenario.anio, activo=True)
        print(f"   ✅ Política RRHH encontrada para año {escenario.anio}")
        print(f"      - Dotación: ${politica.valor_dotacion_completa:,.0f} cada {politica.frecuencia_dotacion_meses} meses")
        print(f"      - EPP Comercial: ${politica.valor_epp_anual_comercial:,.0f} cada {politica.frecuencia_epp_meses} meses")
        print(f"      - Examen Ingreso Comercial: ${politica.costo_examen_ingreso_comercial:,.0f}")
        print(f"      - Examen Ingreso Operativo: ${politica.costo_examen_ingreso_operativo:,.0f}")
        print(f"      - Examen Periódico Comercial: ${politica.costo_examen_periodico_comercial:,.0f}")
        print(f"      - Examen Periódico Operativo: ${politica.costo_examen_periodico_operativo:,.0f}")
        print(f"      - Tasa Rotación Anual: {politica.tasa_rotacion_anual}%")
    except PoliticaRecursosHumanos.DoesNotExist:
        print(f"   ❌ NO existe Política RRHH para año {escenario.anio}")
        print(f"   💡 Solución: Crear PoliticaRecursosHumanos en Admin Panel para año {escenario.anio}")
        return
    print()

    # 3. Verificar ParametrosMacro
    print("3️⃣  PARÁMETROS MACRO:")
    print("-" * 80)
    try:
        macro = ParametrosMacro.objects.get(anio=escenario.anio, activo=True)
        print(f"   ✅ Parámetros Macro encontrados para año {escenario.anio}")
        print(f"      - SMLV: ${macro.salario_minimo_legal:,.0f}")
        print(f"      - Tope Dotación: {politica.tope_smlv_dotacion} SMLV = ${politica.tope_smlv_dotacion * macro.salario_minimo_legal:,.0f}")
    except ParametrosMacro.DoesNotExist:
        print(f"   ❌ NO existen ParametrosMacro para año {escenario.anio}")
        return
    print()

    # 4. Verificar Personal y Gastos por Marca
    print("4️⃣  PERSONAL Y GASTOS DE PROVISIONES POR MARCA:")
    print("-" * 80)

    marcas = Marca.objects.filter(activa=True)
    for marca in marcas:
        print(f"\n   📦 MARCA: {marca.nombre}")
        print("   " + "-" * 76)

        # Personal Comercial
        personal_com = PersonalComercial.objects.filter(escenario=escenario, marca=marca)
        count_com = sum(p.cantidad for p in personal_com)
        print(f"      Personal Comercial: {count_com} empleados")

        # Personal Logístico
        personal_log = PersonalLogistico.objects.filter(escenario=escenario, marca=marca)
        count_log = sum(p.cantidad for p in personal_log)
        print(f"      Personal Logístico: {count_log} empleados")

        # Personal Administrativo
        personal_adm = PersonalAdministrativo.objects.filter(escenario=escenario, marca=marca)
        count_adm = sum(p.cantidad for p in personal_adm)
        print(f"      Personal Administrativo: {count_adm} empleados")

        # Gastos de Provisiones
        print()
        print("      Gastos Comerciales (Provisiones):")
        gastos_com = GastoComercial.objects.filter(escenario=escenario, marca=marca, tipo__in=['dotacion', 'epp', 'examenes'])
        if gastos_com:
            for g in gastos_com:
                print(f"         ✅ {g.tipo.upper()}: {g.nombre} = ${g.valor_mensual:,.0f}/mes (asignación: {g.tipo_asignacion_geo})")
        else:
            print("         ❌ NO hay gastos de provisiones comerciales")
            print("         💡 Verifica que los signals se hayan ejecutado. Prueba guardar un PersonalComercial.")

        print()
        print("      Gastos Logísticos (Provisiones):")
        gastos_log = GastoLogistico.objects.filter(escenario=escenario, marca=marca, tipo__in=['dotacion', 'examenes'])
        if gastos_log:
            for g in gastos_log:
                print(f"         ✅ {g.tipo.upper()}: {g.nombre} = ${g.valor_mensual:,.0f}/mes (asignación: {g.tipo_asignacion_geo})")
        else:
            print("         ❌ NO hay gastos de provisiones logísticas")

        print()
        print("      Gastos Administrativos (Provisiones):")
        gastos_adm = GastoAdministrativo.objects.filter(escenario=escenario, marca=marca, tipo__in=['dotacion', 'examenes'])
        if gastos_adm:
            for g in gastos_adm:
                print(f"         ✅ {g.tipo.upper()}: {g.nombre} = ${g.valor_mensual:,.0f}/mes")
        else:
            print("         ❌ NO hay gastos de provisiones administrativas")

    print()
    print("=" * 80)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 80)
    print()
    print("💡 SOLUCIONES COMUNES:")
    print("   1. Si no existe PoliticaRecursosHumanos: Crearla en Admin Panel")
    print("   2. Si no hay gastos de provisiones: Ir al Admin Panel y guardar un PersonalComercial")
    print("      (esto disparará el signal que crea los gastos automáticamente)")
    print("   3. Si los valores están en $0: Verificar que PoliticaRecursosHumanos tenga valores > 0")
    print()


if __name__ == '__main__':
    diagnosticar()
