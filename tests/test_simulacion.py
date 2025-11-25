"""
Script de Prueba - Simulación Completa

Ejecuta una simulación completa del sistema y muestra los resultados.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from core.simulator import Simulator

print("=" * 80)
print("SIMULACIÓN COMPLETA DEL SISTEMA")
print("=" * 80)

# Crear simulator
print("\n[1/4] Inicializando simulator...")
simulator = Simulator()
print("✅ Simulator inicializado")

# Cargar marcas
print("\n[2/4] Cargando marcas...")
simulator.cargar_marcas()
print(f"✅ Cargadas {len(simulator.marcas)} marca(s)")
print(f"✅ {len(simulator.rubros_compartidos)} rubro(s) compartido(s)")

# Ejecutar simulación
print("\n[3/4] Ejecutando simulación...")
try:
    resultado = simulator.ejecutar_simulacion()
    print("✅ Simulación completada exitosamente")
except Exception as e:
    print(f"❌ Error en simulación: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Mostrar resultados
print("\n[4/4] Resultados de la simulación:")
print("=" * 80)

# Consolidado
print("\n📊 RESUMEN CONSOLIDADO")
print("-" * 80)
consolidado = resultado.consolidado
print(f"Ventas Mensuales:      ${consolidado['total_ventas_mensuales']:>15,.0f}")
print(f"Costos Mensuales:      ${consolidado['total_costos_mensuales']:>15,.0f}")
print(f"Margen:                {consolidado['margen_consolidado']*100:>15.2f}%")
print(f"Total Empleados:       {consolidado['total_empleados']:>15,}")

print(f"\nDesglose de Costos:")
print(f"  - Comercial:         ${consolidado['costo_comercial_total']:>15,.0f}")
print(f"  - Logístico:         ${consolidado['costo_logistico_total']:>15,.0f}")
print(f"  - Administrativo:    ${consolidado['costo_administrativo_total']:>15,.0f}")

# Por marca
print("\n" + "=" * 80)
print("📈 DETALLE POR MARCA")
print("=" * 80)

for marca in resultado.marcas:
    print(f"\n🏢 {marca.nombre}")
    print("-" * 80)
    print(f"Ventas Mensuales:      ${marca.ventas_mensuales:>15,.0f}")
    print(f"Costos Totales:        ${marca.costo_total:>15,.0f}")
    print(f"  - Comercial:         ${marca.costo_comercial:>15,.0f}")
    print(f"  - Logístico:         ${marca.costo_logistico:>15,.0f}")
    print(f"  - Administrativo:    ${marca.costo_administrativo:>15,.0f}")
    print(f"Margen:                {marca.margen_porcentaje:>15.2f}%")
    print(f"Empleados:             {marca.total_empleados:>15,}")
    print(f"Rubros Individuales:   {len(marca.rubros_individuales):>15,}")
    print(f"Rubros Compartidos:    {len(marca.rubros_compartidos_asignados):>15,}")

# Rubros compartidos
print("\n" + "=" * 80)
print("🔄 RUBROS COMPARTIDOS")
print("=" * 80)
print(f"\nTotal: {len(resultado.rubros_compartidos)} rubros")

for rubro in resultado.rubros_compartidos[:10]:  # Mostrar primeros 10
    criterio = rubro.criterio_prorrateo.value if rubro.criterio_prorrateo else 'N/A'
    print(f"  • {rubro.nombre:40s} ${rubro.valor_total:>12,.0f} [{criterio}]")

if len(resultado.rubros_compartidos) > 10:
    print(f"  ... y {len(resultado.rubros_compartidos) - 10} más")

print("\n" + "=" * 80)
print("✅ SIMULACIÓN COMPLETADA EXITOSAMENTE")
print("=" * 80)
print("\nPara ver los resultados en el dashboard web:")
print("  streamlit run panels/app.py")
print("=" * 80)
