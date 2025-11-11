"""
Script de Prueba - Validación del Sistema

Este script ejecuta una simulación simple sin necesitar el dashboard web.
Útil para validar que el sistema funciona correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

print("=" * 80)
print("VALIDACIÓN DEL SISTEMA DE DISTRIBUCIÓN MULTIMARCAS")
print("=" * 80)

# Test 1: Imports
print("\n[1/5] Verificando imports...")
try:
    from utils.loaders import DataLoader, get_loader
    from core.calculator_nomina import CalculadoraNomina
    from core.calculator_vehiculos import CalculadoraVehiculos
    from core.rubro_manager import RubroManager
    from models.marca import Marca
    from models.rubro import Rubro
    print("✅ Todos los módulos se importaron correctamente")
except Exception as e:
    print(f"❌ Error en imports: {e}")
    sys.exit(1)

# Test 2: Cargar configuraciones
print("\n[2/5] Cargando configuraciones...")
try:
    loader = get_loader()
    params = loader.cargar_parametros_macro()
    factores = loader.cargar_factores_prestacionales()
    catalogo = loader.cargar_catalogo_rubros()
    print(f"✅ Configuraciones cargadas:")
    print(f"   - Salario mínimo 2025: ${params['parametros']['salario_minimo_legal_2025']:,}")
    print(f"   - Factor prestacional comercial: {factores['comercial']['factor_total']:.1%}")
    print(f"   - Rubros en catálogo: {len(catalogo['rubros_disponibles'])}")
except Exception as e:
    print(f"❌ Error cargando configuraciones: {e}")
    sys.exit(1)

# Test 3: Calculadora de Nómina
print("\n[3/5] Probando calculadora de nómina...")
try:
    calc_nomina = CalculadoraNomina()
    costo = calc_nomina.calcular_costo_empleado(
        salario_base=2150000,
        perfil='comercial'
    )
    print(f"✅ Calculadora de nómina funciona:")
    print(f"   - Salario base: ${costo.salario_base:,}")
    print(f"   - Prestaciones: ${costo.prestaciones:,}")
    print(f"   - Subsidio transporte: ${costo.subsidio_transporte:,}")
    print(f"   - Costo mensual total: ${costo.costo_mensual:,}")
except Exception as e:
    print(f"❌ Error en calculadora de nómina: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Calculadora de Vehículos
print("\n[4/5] Probando calculadora de vehículos...")
try:
    calc_vehiculos = CalculadoraVehiculos()
    costo_nhr = calc_vehiculos.calcular_costo_renting(
        tipo_vehiculo='nhr',
        cantidad=1
    )
    print(f"✅ Calculadora de vehículos funciona:")
    print(f"   - Vehículo: NHR (renting)")
    print(f"   - Costo mensual: ${costo_nhr.costo_unitario_mensual:,}")
    print(f"   - Desglose: Cánon ${costo_nhr.desglose['canon']:,}, "
          f"Combustible ${costo_nhr.desglose['combustible']:,}")
except Exception as e:
    print(f"❌ Error en calculadora de vehículos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Listar marcas disponibles
print("\n[5/5] Verificando marcas disponibles...")
try:
    marcas = loader.listar_marcas()
    print(f"✅ Marcas encontradas: {len(marcas)}")
    for marca_id in marcas:
        print(f"   - {marca_id}")
except Exception as e:
    print(f"❌ Error listando marcas: {e}")
    sys.exit(1)

# Resumen
print("\n" + "=" * 80)
print("✅ SISTEMA VALIDADO CORRECTAMENTE")
print("=" * 80)
print("\nTodos los componentes funcionan correctamente.")
print("\nPara ejecutar el dashboard web:")
print("  streamlit run panels/app.py")
print("\nO ejecuta una simulación completa:")
print("  python test_simulacion.py")
print("=" * 80)
