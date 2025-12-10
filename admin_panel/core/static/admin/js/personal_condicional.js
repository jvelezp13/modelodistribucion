/**
 * JavaScript para ocultar/mostrar campos condicionales en formularios de Personal y Gastos
 *
 * Maneja 3 niveles de asignación:
 * 1. Asignación por Marca: oculta porcentaje_dedicacion y criterio_prorrateo si es "individual"
 * 2. Asignación por Operación: oculta operacion si es "compartido", oculta criterio_prorrateo_operacion si es "individual"
 * 3. Asignación Geográfica: oculta zona si NO es "directo"
 */

(function() {
    'use strict';

    function initConditionalFields() {
        // =========================================
        // ASIGNACIÓN POR MARCA
        // =========================================
        const asignacionField = document.querySelector('#id_asignacion');
        const porcentajeDedicacionRow = document.querySelector('.field-porcentaje_dedicacion');
        const criterioProrrateoRow = document.querySelector('.field-criterio_prorrateo');

        function updateAsignacionMarca() {
            if (!asignacionField) return;
            const isIndividual = asignacionField.value === 'individual';

            if (porcentajeDedicacionRow) {
                porcentajeDedicacionRow.style.display = isIndividual ? 'none' : '';
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
        // ASIGNACIÓN GEOGRÁFICA
        // =========================================
        const tipoAsignacionGeoField = document.querySelector('#id_tipo_asignacion_geo');
        const zonaRow = document.querySelector('.field-zona');

        function updateAsignacionGeo() {
            if (!tipoAsignacionGeoField) return;
            const isDirecto = tipoAsignacionGeoField.value === 'directo';

            if (zonaRow) {
                zonaRow.style.display = isDirecto ? '' : 'none';
            }
        }

        if (tipoAsignacionGeoField) {
            tipoAsignacionGeoField.addEventListener('change', updateAsignacionGeo);
            updateAsignacionGeo();
        }

        // =========================================
        // PERNOCTA (Zona Comercial y Ruta Logística)
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
