/**
 * Botón "Distribuir Equitativo" para inlines de asignación de marcas
 * Distribuye automáticamente el 100% equitativamente entre todas las marcas asignadas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Buscar todos los inlines que contienen campos de porcentaje
    const inlineGroups = document.querySelectorAll('.inline-group');

    inlineGroups.forEach(function(inlineGroup) {
        // Verificar si este inline tiene campos de porcentaje (es un inline de marca)
        const porcentajeInputs = inlineGroup.querySelectorAll('input[name*="porcentaje"]');
        if (porcentajeInputs.length === 0) return;

        // Crear el botón
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = 'Distribuir Equitativo';
        btn.className = 'button default';
        btn.style.marginLeft = '10px';
        btn.style.fontSize = '11px';
        btn.style.padding = '5px 10px';

        // Agregar tooltip
        btn.title = 'Distribuir el 100% equitativamente entre todas las marcas asignadas';

        btn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            distribuirEquitativo(inlineGroup);
            return false;
        };

        // Agregar el botón al header del inline
        const header = inlineGroup.querySelector('h2');
        if (header) {
            header.style.display = 'flex';
            header.style.alignItems = 'center';
            header.style.justifyContent = 'space-between';
            header.appendChild(btn);
        }
    });

    function distribuirEquitativo(inlineGroup) {
        // Buscar todas las filas del inline - usar múltiples selectores para compatibilidad
        // Django admin usa diferentes estructuras para TabularInline
        let rows = inlineGroup.querySelectorAll('tbody tr.form-row:not(.empty-form)');

        // Si no encuentra con tbody tr.form-row, intentar con .inline-related
        if (rows.length === 0) {
            rows = inlineGroup.querySelectorAll('.inline-related:not(.empty-form)');
        }

        // También buscar en la tabla directamente
        if (rows.length === 0) {
            rows = inlineGroup.querySelectorAll('tr:not(.empty-form):not(:first-child)');
        }

        console.log('Filas encontradas:', rows.length);

        // Filtrar filas activas (no marcadas para eliminar y con marca seleccionada)
        const activeRows = Array.from(rows).filter(function(row) {
            // Ignorar filas que son headers o vacías
            if (row.classList.contains('add-row')) return false;

            // Verificar que no esté marcada para eliminar
            const deleteCheckbox = row.querySelector('input[type="checkbox"][name*="DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) return false;

            // Verificar que tenga una marca seleccionada
            const marcaSelect = row.querySelector('select[name*="marca"]');
            console.log('Marca select:', marcaSelect, 'Value:', marcaSelect ? marcaSelect.value : 'N/A');
            if (!marcaSelect || !marcaSelect.value) return false;

            return true;
        });

        console.log('Filas activas con marca:', activeRows.length);

        if (activeRows.length === 0) {
            alert('No hay marcas asignadas para distribuir. Asegúrate de seleccionar las marcas primero.');
            return;
        }

        // Calcular porcentaje equitativo
        const porcentaje = (100 / activeRows.length).toFixed(2);

        // Asignar porcentaje a cada fila activa
        activeRows.forEach(function(row) {
            const porcentajeInput = row.querySelector('input[name*="porcentaje"]');
            console.log('Porcentaje input:', porcentajeInput);
            if (porcentajeInput) {
                porcentajeInput.value = porcentaje;
                // Trigger change event para actualizar cualquier validación
                porcentajeInput.dispatchEvent(new Event('change', { bubbles: true }));
                porcentajeInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });

        // Mostrar mensaje de confirmación
        const msg = 'Distribuido: ' + porcentaje + '% para cada una de las ' + activeRows.length + ' marca(s)';

        // Crear notificación temporal
        const notification = document.createElement('div');
        notification.textContent = msg;
        notification.style.cssText = 'position:fixed; top:10px; right:10px; background:#166534; color:white; padding:10px 20px; border-radius:4px; z-index:9999; font-size:13px;';
        document.body.appendChild(notification);

        setTimeout(function() {
            notification.remove();
        }, 3000);
    }
});
