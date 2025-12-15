/**
 * Script para mostrar/ocultar inlines según el tipo de proyección seleccionado.
 * - Tipo 'simple': muestra ProyeccionManual, oculta ListaPreciosProducto
 * - Tipo 'lista_precios': muestra ListaPreciosProducto, oculta ProyeccionManual
 */
(function($) {
    'use strict';

    function toggleInlinesByTipo() {
        var tipoSelect = document.getElementById('id_tipo');
        if (!tipoSelect) return;

        var tipo = tipoSelect.value;

        // Buscar los inlines por su ID o clase
        var inlineManual = document.querySelector('.inline-group:has([id*="proyeccionmanual"])') ||
                           document.getElementById('proyeccionmanual_set-group');
        var inlineListaPrecios = document.querySelector('.inline-group:has([id*="listapreciosproducto"])') ||
                                  document.getElementById('listapreciosproducto_set-group');

        // Buscar por h2 que contenga el texto del modelo
        if (!inlineManual || !inlineListaPrecios) {
            var inlineGroups = document.querySelectorAll('.inline-group');
            inlineGroups.forEach(function(group) {
                var header = group.querySelector('h2');
                if (header) {
                    var text = header.textContent.toLowerCase();
                    if (text.includes('manual') || text.includes('proyección manual')) {
                        inlineManual = group;
                    } else if (text.includes('lista') || text.includes('precios')) {
                        inlineListaPrecios = group;
                    }
                }
            });
        }

        // Aplicar visibilidad según el tipo
        if (tipo === 'simple') {
            if (inlineManual) {
                inlineManual.style.display = '';
                inlineManual.style.opacity = '1';
            }
            if (inlineListaPrecios) {
                inlineListaPrecios.style.display = 'none';
            }
        } else if (tipo === 'lista_precios') {
            if (inlineManual) {
                inlineManual.style.display = 'none';
            }
            if (inlineListaPrecios) {
                inlineListaPrecios.style.display = '';
                inlineListaPrecios.style.opacity = '1';
            }
        } else {
            // Mostrar ambos si no hay tipo seleccionado
            if (inlineManual) inlineManual.style.display = '';
            if (inlineListaPrecios) inlineListaPrecios.style.display = '';
        }
    }

    // Ejecutar al cargar la página
    document.addEventListener('DOMContentLoaded', function() {
        toggleInlinesByTipo();

        // Ejecutar cuando cambie el tipo
        var tipoSelect = document.getElementById('id_tipo');
        if (tipoSelect) {
            tipoSelect.addEventListener('change', toggleInlinesByTipo);
        }
    });

    // Compatibilidad con Django admin que puede cargar después
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).ready(function() {
            toggleInlinesByTipo();
            django.jQuery('#id_tipo').on('change', toggleInlinesByTipo);
        });
    }

})(django.jQuery || jQuery);
