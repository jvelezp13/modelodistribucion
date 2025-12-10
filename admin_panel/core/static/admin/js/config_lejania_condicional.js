/**
 * JavaScript para ocultar/mostrar campos condicionales en Configuración de Lejanías
 *
 * Maneja:
 * - Comité Comercial: oculta municipio_comite y frecuencia_comite si no tiene comité
 */

(function() {
    'use strict';

    function initConditionalFields() {
        // =========================================
        // COMITÉ COMERCIAL
        // =========================================
        const tieneComiteField = document.querySelector('#id_tiene_comite_comercial');
        const municipioComiteRow = document.querySelector('.field-municipio_comite');
        const frecuenciaComiteRow = document.querySelector('.field-frecuencia_comite');

        function updateComite() {
            if (!tieneComiteField) return;
            const tieneComite = tieneComiteField.checked;

            if (municipioComiteRow) {
                municipioComiteRow.style.display = tieneComite ? '' : 'none';
            }
            if (frecuenciaComiteRow) {
                frecuenciaComiteRow.style.display = tieneComite ? '' : 'none';
            }
        }

        if (tieneComiteField) {
            tieneComiteField.addEventListener('change', updateComite);
            updateComite();
        }
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initConditionalFields);
    } else {
        initConditionalFields();
    }
})();
