/**
 * JavaScript para ocultar/mostrar campos condicionales en formularios de Vehículo
 *
 * Maneja 3 tipos de condiciones:
 * 1. Asignación por Marca: oculta porcentaje_uso y criterio_prorrateo si es "individual"
 * 2. Asignación por Operación: oculta operacion si es "compartido", oculta criterio_prorrateo_operacion si es "individual"
 * 3. Esquema: muestra/oculta secciones según Propio/Renting/Tercero
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
        // ESQUEMA (Propio/Renting/Tercero)
        // =========================================
        const esquemaField = document.querySelector('#id_esquema');

        // Buscar fieldsets por su título
        function findFieldsetByTitle(title) {
            const fieldsets = document.querySelectorAll('fieldset');
            for (const fs of fieldsets) {
                const legend = fs.querySelector('h2');
                if (legend && legend.textContent.includes(title)) {
                    return fs;
                }
            }
            return null;
        }

        const rentingFieldset = findFieldsetByTitle('Esquema: Renting');
        const propioFieldset = findFieldsetByTitle('Esquema: Propio');
        const otrosCostosPropioFieldset = findFieldsetByTitle('Otros Costos Operativos');

        function updateEsquema() {
            if (!esquemaField) return;
            const esquema = esquemaField.value;

            const isRenting = esquema === 'renting';
            const isPropio = esquema === 'tradicional';
            const isTercero = esquema === 'tercero';

            // Mostrar/ocultar sección Renting
            if (rentingFieldset) {
                if (isRenting) {
                    rentingFieldset.style.display = '';
                    rentingFieldset.classList.remove('collapsed');
                } else {
                    rentingFieldset.style.display = 'none';
                }
            }

            // Mostrar/ocultar sección Propio
            if (propioFieldset) {
                if (isPropio) {
                    propioFieldset.style.display = '';
                    propioFieldset.classList.remove('collapsed');
                } else {
                    propioFieldset.style.display = 'none';
                }
            }

            // Mostrar/ocultar Otros Costos Operativos (solo Propio y Renting)
            if (otrosCostosPropioFieldset) {
                if (isPropio || isRenting) {
                    otrosCostosPropioFieldset.style.display = '';
                } else {
                    otrosCostosPropioFieldset.style.display = 'none';
                }
            }
        }

        if (esquemaField) {
            esquemaField.addEventListener('change', updateEsquema);
            updateEsquema();
        }
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConditionalFields);
    } else {
        initConditionalFields();
    }
})();
