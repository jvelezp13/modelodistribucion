/**
 * JavaScript para ocultar/mostrar campos condicionales en formularios de Personal
 * - Oculta porcentaje_dedicacion y criterio_prorrateo cuando asignacion es "individual"
 * - Oculta zona cuando tipo_asignacion_geo NO es "directo"
 */

(function() {
    'use strict';

    function initConditionalFields() {
        // Campos de asignación por marca
        const asignacionField = document.querySelector('#id_asignacion');
        const porcentajeDedicacionRow = document.querySelector('.field-porcentaje_dedicacion');
        const criterioProrrateoRow = document.querySelector('.field-criterio_prorrateo');

        // Campos de asignación geográfica
        const tipoAsignacionGeoField = document.querySelector('#id_tipo_asignacion_geo');
        const zonaRow = document.querySelector('.field-zona');

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

        function updateAsignacionGeo() {
            if (!tipoAsignacionGeoField) return;

            const isDirecto = tipoAsignacionGeoField.value === 'directo';

            if (zonaRow) {
                zonaRow.style.display = isDirecto ? '' : 'none';
            }
        }

        // Event listeners
        if (asignacionField) {
            asignacionField.addEventListener('change', updateAsignacionMarca);
            updateAsignacionMarca(); // Ejecutar al cargar
        }

        if (tipoAsignacionGeoField) {
            tipoAsignacionGeoField.addEventListener('change', updateAsignacionGeo);
            updateAsignacionGeo(); // Ejecutar al cargar
        }
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConditionalFields);
    } else {
        initConditionalFields();
    }
})();
