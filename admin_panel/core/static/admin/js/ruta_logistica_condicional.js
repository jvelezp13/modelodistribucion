/**
 * JavaScript para ocultar/mostrar campos condicionales en formularios de Ruta Logística
 *
 * Maneja 3 tipos de condiciones:
 * 1. Asignación por Marca: oculta porcentaje_uso y criterio_prorrateo si es "individual"
 * 2. Asignación por Operación: oculta operacion si es "compartido", oculta criterio_prorrateo_operacion si es "individual"
 * 3. Pernocta: oculta noches_pernocta si no requiere pernocta
 */

(function() {
    'use strict';

    function initConditionalFields() {
        // =========================================
        // ASIGNACIÓN POR MARCA
        // =========================================
        const asignacionField = document.querySelector('#id_asignacion');
        const porcentajeUsoRow = document.querySelector('.field-porcentaje_uso');
        const criterioProrrateoRow = document.querySelector('.field-criterio_prorrateo');

        function updateAsignacionMarca() {
            if (!asignacionField) return;
            const isIndividual = asignacionField.value === 'individual';

            if (porcentajeUsoRow) {
                porcentajeUsoRow.style.display = isIndividual ? 'none' : '';
            }
            if (criterioProrrateoRow) {
                criterioProrrateoRow.style.display = isIndividual ? 'none' : '';
            }
        }

        if (asignacionField) {
            asignacionField.addEventListener('change', updateAsignacionMarca);
            updateAsignacionMarca();
        }

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
