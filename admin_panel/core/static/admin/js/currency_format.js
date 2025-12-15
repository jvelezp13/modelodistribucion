/**
 * Formateo de campos de moneda en el admin de Django
 * Muestra valores con separador de miles (puntos) para mejor legibilidad
 */
(function() {
    'use strict';

    // Formatear número con puntos como separador de miles
    function formatCurrency(value) {
        if (!value || value === '0' || value === '0.00') return '';

        var strValue = value.toString().trim();
        var num;

        // Detectar formato de entrada
        // Si tiene punto decimal (ej: 50000000.00), es formato con punto decimal
        // Si tiene coma (ej: 50.000.000,00), es formato colombiano
        if (strValue.indexOf(',') > -1) {
            // Formato colombiano: remover puntos de miles, cambiar coma por punto
            num = parseFloat(strValue.replace(/\./g, '').replace(',', '.'));
        } else {
            // Formato con punto decimal (viene de Django): usar directamente
            num = parseFloat(strValue);
        }

        if (isNaN(num)) return value;

        // Redondear a entero (sin decimales para moneda)
        num = Math.round(num);

        // Formatear con puntos como separador de miles
        var formatted = num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');

        return formatted;
    }

    // Convertir valor formateado a número para el input
    function unformatCurrency(value) {
        if (!value) return '';
        // Remover puntos de miles y cambiar coma decimal por punto
        return value.toString().replace(/\./g, '').replace(',', '.');
    }

    // Aplicar formato a un input
    function applyFormat(input) {
        var value = input.value;
        if (value) {
            input.value = formatCurrency(value);
        }
    }

    // Remover formato para edición
    function removeFormat(input) {
        var value = input.value;
        if (value) {
            input.value = unformatCurrency(value);
        }
    }

    // Inicializar cuando el DOM esté listo
    function init() {
        // Seleccionar inputs de los meses en ProyeccionManual
        var meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                     'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

        meses.forEach(function(mes) {
            // Buscar inputs que contengan el nombre del mes
            var inputs = document.querySelectorAll('input[name$="-' + mes + '"], input[name="' + mes + '"]');

            inputs.forEach(function(input) {
                if (input.type === 'number') {
                    // Cambiar a tipo text para permitir formato
                    input.type = 'text';
                    input.style.textAlign = 'right';
                }

                // Formatear valor inicial
                applyFormat(input);

                // Al enfocar: remover formato para edición
                input.addEventListener('focus', function() {
                    removeFormat(this);
                    this.select();
                });

                // Al perder foco: aplicar formato
                input.addEventListener('blur', function() {
                    applyFormat(this);
                });
            });
        });

        // También aplicar a campos de ticket_promedio en tipologías
        var ticketInputs = document.querySelectorAll('input[name$="-ticket_promedio"]');
        ticketInputs.forEach(function(input) {
            if (input.type === 'number') {
                input.type = 'text';
                input.style.textAlign = 'right';
            }
            applyFormat(input);
            input.addEventListener('focus', function() {
                removeFormat(this);
                this.select();
            });
            input.addEventListener('blur', function() {
                applyFormat(this);
            });
        });

        console.log('Currency format JS loaded');
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // También reinicializar cuando se agreguen nuevos inlines
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                setTimeout(init, 100);
            }
        });
    });

    // Observar cambios en el formulario (para inlines dinámicos)
    document.addEventListener('DOMContentLoaded', function() {
        var form = document.querySelector('#proyeccionventasconfig_form, form');
        if (form) {
            observer.observe(form, { childList: true, subtree: true });
        }
    });
})();
