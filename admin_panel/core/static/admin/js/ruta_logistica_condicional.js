/**
 * JavaScript para ocultar/mostrar campos condicionales en formularios de Ruta Logística
 *
 * Maneja 2 tipos de condiciones:
 * 1. Asignación por Operación: oculta operacion si es "compartido", oculta criterio_prorrateo_operacion si es "individual"
 * 2. Pernocta: oculta noches_pernocta si no requiere pernocta
 */

(function() {
    'use strict';

    function initConditionalFields() {
        // =========================================
        // ASIGNACIÓN POR OPERACIÓN
        // =========================================
        const tipoAsignacionOpField = document.querySelector('#id_tipo_asignacion_operacion');
        const operacionRow = document.querySelector('.field-operacion');
        const criterioProrrateoOpRow = document.querySelector('.field-criterio_prorrateo_operacion');

        function updateAsignacionOperacion() {
            if (!tipoAsignacionOpField) return;
            const isIndividual = tipoAsignacionOpField.value === 'individual';

            if (operacionRow) {
                operacionRow.style.display = isIndividual ? '' : 'none';
            }
            if (criterioProrrateoOpRow) {
                criterioProrrateoOpRow.style.display = isIndividual ? 'none' : '';
            }
        }

        if (tipoAsignacionOpField) {
            tipoAsignacionOpField.addEventListener('change', updateAsignacionOperacion);
            updateAsignacionOperacion();
        }

        // =========================================
        // PERNOCTA
        // =========================================
        const requierePernoctaField = document.querySelector('#id_requiere_pernocta');
        const nochesPernoctaRow = document.querySelector('.field-noches_pernocta');

        function updatePernocta() {
            if (!requierePernoctaField) return;
            const requiere = requierePernoctaField.checked;

            if (nochesPernoctaRow) {
                nochesPernoctaRow.style.display = requiere ? '' : 'none';
            }
        }

        if (requierePernoctaField) {
            requierePernoctaField.addEventListener('change', updatePernocta);
            updatePernocta();
        }
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConditionalFields);
    } else {
        initConditionalFields();
    }
})();
