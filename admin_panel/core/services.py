from django.db import transaction
from .models import (
    Escenario, ParametrosMacro, PersonalComercial, PersonalLogistico,
    PersonalAdministrativo, Vehiculo, GastoComercial, GastoLogistico,
    GastoAdministrativo, ProyeccionVentas
)

class EscenarioService:
    @staticmethod
    def get_incremento_valor(indice_nombre, macros):
        """
        Obtiene el valor decimal del incremento basado en el nombre del índice
        y los parámetros macroeconómicos del año destino.
        """
        if not macros:
            return 0
            
        if indice_nombre == 'fijo':
            return 0
            
        mapping = {
            'salarios': macros.incremento_salarios,
            'salario_minimo': macros.incremento_salario_minimo,
            'ipc': macros.ipc,
            'ipt': macros.ipt,
            'combustible': macros.incremento_combustible,
            'arriendos': macros.incremento_arriendos,
            'personalizado_1': macros.incremento_personalizado_1,
            'personalizado_2': macros.incremento_personalizado_2,
        }
        
        # Los valores en BD están en decimal (ej: 0.05 para 5%)
        # Si estuvieran en entero (5 para 5%), habría que dividir por 100.
        # En ParametrosMacro definimos decimal_places=5, así que asumimos que se guardan como 0.05
        return mapping.get(indice_nombre, 0)

    @classmethod
    def proyectar_escenario(cls, escenario_id, nuevo_anio, nuevo_nombre=None):
        """
        Crea un nuevo escenario basado en uno existente, proyectando los valores
        según los índices macroeconómicos del año destino.
        """
        source_scenario = Escenario.objects.get(pk=escenario_id)
        
        # Determinar nombre
        if not nuevo_nombre:
            nuevo_nombre = f"{source_scenario.nombre} (Proyección {nuevo_anio})"
            
        # Verificar si ya existen macros para el año destino
        try:
            macros = ParametrosMacro.objects.get(anio=nuevo_anio)
        except ParametrosMacro.DoesNotExist:
            # Si no existen macros, se crea el escenario pero sin aplicar incrementos (factor 0)
            macros = None
            
        with transaction.atomic():
            # 1. Crear nuevo escenario
            new_scenario = Escenario.objects.create(
                nombre=nuevo_nombre,
                tipo='planeado', # Las proyecciones siempre nacen como planeadas
                anio=nuevo_anio,
                periodo_tipo=source_scenario.periodo_tipo,
                periodo_numero=source_scenario.periodo_numero,
                activo=False,
                aprobado=False,
                notas=f"Proyectado desde: {source_scenario.nombre} ({source_scenario.anio})"
            )
            
            # 2. Proyectar Personal Comercial
            for item in source_scenario.personal_comercial_items.all():
                incremento = cls.get_incremento_valor(item.indice_incremento, macros)
                
                # Clonar objeto
                item.pk = None
                item.escenario = new_scenario
                item.salario_base = item.salario_base * (1 + incremento)
                if item.auxilio_adicional:
                    item.auxilio_adicional = item.auxilio_adicional * (1 + incremento)
                item.save()

            # 3. Proyectar Personal Logístico
            for item in source_scenario.personal_logistico_items.all():
                incremento = cls.get_incremento_valor(item.indice_incremento, macros)
                
                item.pk = None
                item.escenario = new_scenario
                item.salario_base = item.salario_base * (1 + incremento)
                item.save()

            # 4. Proyectar Personal Administrativo
            for item in source_scenario.personal_administrativo_items.all():
                incremento = cls.get_incremento_valor(item.indice_incremento, macros)
                
                item.pk = None
                item.escenario = new_scenario
                if item.salario_base:
                    item.salario_base = item.salario_base * (1 + incremento)
                if item.honorarios_mensuales:
                    item.honorarios_mensuales = item.honorarios_mensuales * (1 + incremento)
                item.save()

            # 5. Proyectar Vehículos (Solo se copian, no tienen valor monetario directo)
            for item in source_scenario.vehiculo_items.all():
                # Vehículos no tienen costo directo aquí, solo cantidad y km
                # Se copian tal cual
                item.pk = None
                item.escenario = new_scenario
                item.save()

            # 6. Proyectar Gastos Comerciales
            for item in source_scenario.gasto_comercial_items.all():
                incremento = cls.get_incremento_valor(item.indice_incremento, macros)
                
                item.pk = None
                item.escenario = new_scenario
                item.valor_mensual = item.valor_mensual * (1 + incremento)
                item.save()

            # 7. Proyectar Gastos Logísticos
            for item in source_scenario.gasto_logistico_items.all():
                incremento = cls.get_incremento_valor(item.indice_incremento, macros)
                
                item.pk = None
                item.escenario = new_scenario
                item.valor_mensual = item.valor_mensual * (1 + incremento)
                item.save()

            # 8. Proyectar Gastos Administrativos
            for item in source_scenario.gasto_administrativo_items.all():
                incremento = cls.get_incremento_valor(item.indice_incremento, macros)
                
                item.pk = None
                item.escenario = new_scenario
                item.valor_mensual = item.valor_mensual * (1 + incremento)
                item.save()

            # 9. Proyectar Ventas (Usamos IPC por defecto si no hay lógica específica)
            ipc_incremento = cls.get_incremento_valor('ipc', macros)
            for item in source_scenario.proyeccion_ventas_items.all():
                item.pk = None
                item.escenario = new_scenario
                item.anio = new_anio # Actualizar año de la proyección
                item.ventas = item.ventas * (1 + ipc_incremento)
                item.save()

            return new_scenario
