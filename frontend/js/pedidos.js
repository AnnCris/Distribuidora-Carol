let paginaActual = 1;
let productosSeleccionados = [];
let clientesData = [];
let productosData = [];
let pedidoActualId = null;

function obtenerFechaLocal() {
    const ahora = new Date();
    const año = ahora.getFullYear();
    const mes = String(ahora.getMonth() + 1).padStart(2, '0');
    const dia = String(ahora.getDate()).padStart(2, '0');
    return `${año}-${mes}-${dia}`;
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Pedidos cargado');

    // PRIMERO: Verificar autenticación
    const autenticado = await verificarAuth();
    if (!autenticado) {
        console.log('❌ No autenticado');
        return;
    }

    console.log('✅ Autenticado, cargando pedidos...');

    // Cargar información del usuario
    cargarInfoUsuario();

    // Cargar datos iniciales
    await Promise.all([
        cargarPedidos(),
        cargarClientes(),
        cargarProductos()
    ]);

    // Filtros
    document.getElementById('buscar').addEventListener('input', debounce(cargarPedidos, 500));
    document.getElementById('filtroEstado').addEventListener('change', cargarPedidos);
    document.getElementById('fechaDesde').addEventListener('change', cargarPedidos);
    document.getElementById('fechaHasta').addEventListener('change', cargarPedidos);

    // Paginación
    document.getElementById('btnAnterior').addEventListener('click', () => {
        if (paginaActual > 1) {
            paginaActual--;
            cargarPedidos();
        }
    });

    document.getElementById('btnSiguiente').addEventListener('click', () => {
        paginaActual++;
        cargarPedidos();
    });

    document.getElementById('productoSelect').addEventListener('change', (e) => {
        const productoId = e.target.value;
        if (productoId) {
            const producto = productosData.find(p => p.id == productoId);
            if (producto) {
                document.getElementById('productoPrecio').value = producto.precio_venta;
                
                // Si es kg, mostrar campo de peso y ocultar cantidad normal
                if (producto.unidad_medida === 'kg') {
                    document.getElementById('filaCantidadNormal').style.display = 'none';
                    document.getElementById('filaPesoKg').style.display = 'block';
                    document.getElementById('productoSubtotalPreview').style.display = 'block';
                    document.getElementById('productoPeso').value = '';
                    document.getElementById('productoSubtotalPreview').textContent = 'Subtotal: Bs. 0.00';
                } else {
                    document.getElementById('filaCantidadNormal').style.display = 'block';
                    document.getElementById('filaPesoKg').style.display = 'none';
                    document.getElementById('productoSubtotalPreview').style.display = 'none';
                    document.getElementById('productoCantidad').value = '';
                }
            }
        } else {
            document.getElementById('filaCantidadNormal').style.display = 'block';
            document.getElementById('filaPesoKg').style.display = 'none';
            document.getElementById('productoSubtotalPreview').style.display = 'none';
            document.getElementById('productoPrecio').value = '';
        }
    });

    document.getElementById('productoPeso').addEventListener('input', () => {
        const peso = parseFloat(document.getElementById('productoPeso').value) || 0;
        const precio = parseFloat(document.getElementById('productoPrecio').value) || 0;
        const subtotal = Math.round(peso * precio * 100) / 100;
        document.getElementById('productoSubtotalPreview').textContent = 
            `Subtotal: Bs. ${subtotal.toFixed(2)}`;
    });

    // Cambio de cliente
    document.getElementById('pedidoCliente').addEventListener('change', async (e) => {
        const clienteId = e.target.value;
        if (clienteId) {
            await verificarDevolucionesPendientes(clienteId);
        }
    });

    // Menu toggle
    document.getElementById('menuToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('active');
    });
});

function cargarInfoUsuario() {
    const usuario = getUsuario();
    if (usuario) {
        document.getElementById('userName').textContent = usuario.nombre;
        document.getElementById('userRole').textContent = usuario.rol === 'admin' ? 'Administrador' : 'Vendedor';
        document.getElementById('userAvatar').textContent = usuario.nombre.charAt(0).toUpperCase();

        const menuUsuarios = document.getElementById('menuUsuarios');
        if (usuario.rol !== 'admin') {
            menuUsuarios.style.display = 'none';
        }
    }
}

async function cargarPedidos() {
    try {
        document.getElementById('loadingPedidos').classList.remove('hidden');
        document.getElementById('tablaPedidos').classList.add('hidden');
        document.getElementById('noPedidos').classList.add('hidden');

        const buscar = document.getElementById('buscar').value;
        const estado = document.getElementById('filtroEstado').value;
        const fechaDesde = document.getElementById('fechaDesde').value;
        const fechaHasta = document.getElementById('fechaHasta').value;

        let url = `/api/pedidos?page=${paginaActual}&per_page=20`;
        if (buscar) url += `&buscar=${buscar}`;
        if (estado) url += `&estado=${estado}`;
        if (fechaDesde) url += `&fecha_desde=${fechaDesde}`;
        if (fechaHasta) url += `&fecha_hasta=${fechaHasta}`;

        const response = await fetchAPI(url);

        document.getElementById('loadingPedidos').classList.add('hidden');

        if (response.success && response.data.pedidos && response.data.pedidos.length > 0) {
            document.getElementById('tablaPedidos').classList.remove('hidden');
            document.getElementById('paginacion').classList.remove('hidden');

            const hoy = obtenerFechaLocal();

            const tbody = document.getElementById('pedidosBody');
            tbody.innerHTML = response.data.pedidos.map(pedido => {
                // Verificar si el pedido es de hoy
                const fechaPedido = pedido.fecha_pedido; // "dd/mm/yyyy HH:MM"
                let esDehoy = false;
                if (fechaPedido && fechaPedido.includes('/')) {
                    const partes = fechaPedido.split(' ')[0].split('/');
                    const fechaISO = `${partes[2]}-${partes[1]}-${partes[0]}`;
                    esDehoy = fechaISO === hoy;
                }

                return `
                <tr>
                    <td><strong>${pedido.numero_pedido}</strong></td>
                    <td>${pedido.cliente_nombre}</td>
                    <td>${formatearFecha(pedido.fecha_pedido)}</td>
                    <td><strong>Bs. ${formatearPrecio(pedido.total)}</strong></td>
                    <td><span class="badge badge-${pedido.estado}">${pedido.estado.toUpperCase()}</span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="verPedido(${pedido.id})">Ver</button>
                        ${pedido.estado === 'pendiente' ? `
                            <button class="btn btn-secondary btn-sm" onclick="editarPedido(${pedido.id})">Editar</button>
                            <button class="btn btn-success btn-sm" onclick="cambiarEstado(${pedido.id}, 'entregado')">Entregar</button>
                            <button class="btn btn-danger btn-sm" onclick="cambiarEstado(${pedido.id}, 'cancelado')">Cancelar</button>
                        ` : ''}
                        ${esDehoy ? `
                            <button class="btn btn-secondary btn-sm" onclick="descargarPDF(${pedido.id})" title="Descargar PDF">🖨️ PDF</button>
                        ` : ''}
                    </td>
                </tr>
            `}).join('');

            document.getElementById('infoPagina').textContent =
                `Página ${response.data.pagina_actual} de ${response.data.total_paginas}`;

            document.getElementById('btnAnterior').disabled = paginaActual === 1;
            document.getElementById('btnSiguiente').disabled = paginaActual >= response.data.total_paginas;

        } else {
            document.getElementById('noPedidos').classList.remove('hidden');
            document.getElementById('paginacion').classList.add('hidden');
        }

    } catch (error) {
        document.getElementById('loadingPedidos').classList.add('hidden');
        document.getElementById('noPedidos').classList.remove('hidden');
        console.error('❌ Error al cargar pedidos:', error);
    }
}

async function cargarClientes() {
    try {
        const response = await fetchAPI('/api/clientes/todos');
        if (response.success) {
            clientesData = response.data.clientes;
            const select = document.getElementById('pedidoCliente');
            select.innerHTML = '<option value="">Seleccione un cliente</option>' +
                clientesData.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('');
        }
    } catch (error) {
        console.error('❌ Error al cargar clientes:', error);
    }
}

async function cargarProductos() {
    try {
        const response = await fetchAPI('/api/productos/todos');
        if (response.success) {
            productosData = response.data.productos;
            const select = document.getElementById('productoSelect');
            select.innerHTML = '<option value="">Seleccione producto</option>' +
                productosData.map(p => 
                    `<option value="${p.id}">${p.nombre} - Bs. ${formatearPrecio(p.precio_venta)} (Stock: ${p.stock_actual})</option>`
                ).join('');
        }
    } catch (error) {
        console.error('❌ Error al cargar productos:', error);
    }
}

function abrirModalNuevoPedido() {
    pedidoActualId = null;
    productosSeleccionados = [];
    document.getElementById('formNuevoPedido').reset();
    actualizarTablaProductos();
    calcularTotal();
    document.getElementById('alertaDevolucionesPendientes').classList.add('hidden');

    // Restaurar título y botón al estado de "nuevo"
    document.querySelector('#modalNuevoPedido .modal-header h2').textContent = 'Nuevo Pedido';
    document.querySelector('#modalNuevoPedido .modal-footer .btn-primary').textContent = 'Guardar Pedido';
    document.querySelector('#modalNuevoPedido .modal-footer .btn-primary').setAttribute('onclick', 'guardarPedido()');

    const hoy = obtenerFechaLocal();
    const inputFecha = document.getElementById('pedidoFechaEntrega');
    inputFecha.min = hoy;
    inputFecha.value = hoy;

    document.getElementById('modalNuevoPedido').style.display = 'block';
}

async function editarPedido(id) {
    pedidoActualId = id;

    try {
        const response = await fetchAPI(`/api/pedidos/${id}`);
        if (!response.success) {
            mostrarMensaje('Error al cargar pedido', 'error');
            return;
        }

        const pedido = response.data.pedido;

        // Limpiar estado
        productosSeleccionados = [];
        document.getElementById('formNuevoPedido').reset();
        document.getElementById('alertaDevolucionesPendientes').classList.add('hidden');

        // Cambiar título del modal
        document.querySelector('#modalNuevoPedido .modal-header h2').textContent = 'Editar Pedido';
        document.querySelector('#modalNuevoPedido .modal-footer .btn-primary').textContent = 'Actualizar Pedido';
        document.querySelector('#modalNuevoPedido .modal-footer .btn-primary').setAttribute('onclick', `actualizarPedido(${id})`);

        // Llenar campos
        document.getElementById('pedidoCliente').value = pedido.cliente_id;
        document.getElementById('pedidoDescuento').value = pedido.descuento;
        document.getElementById('pedidoObservaciones').value = pedido.observaciones || '';

        // Fecha mínima hoy
        const hoy = obtenerFechaLocal();
        const inputFecha = document.getElementById('pedidoFechaEntrega');
        inputFecha.min = hoy;

        // Cargar fecha de entrega si existe
        if (pedido.fecha_entrega && pedido.fecha_entrega.includes('/')) {
            const partes = pedido.fecha_entrega.split('/');
            inputFecha.value = `${partes[2]}-${partes[1]}-${partes[0]}`;
        }

        // Cargar productos del pedido
        productosSeleccionados = pedido.detalles.map(det => ({
            producto_id: det.producto_id,
            nombre: det.producto_nombre,
            cantidad: parseFloat(det.cantidad),
            precio_unitario: parseFloat(det.precio_unitario)
        }));

        actualizarTablaProductos();
        calcularTotal();

        document.getElementById('modalNuevoPedido').style.display = 'block';

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al editar pedido:', error);
    }
}

async function actualizarPedido(id) {
    const clienteId = document.getElementById('pedidoCliente').value;
    const fechaEntrega = document.getElementById('pedidoFechaEntrega').value;
    const observaciones = document.getElementById('pedidoObservaciones').value;
    const descuento = parseFloat(document.getElementById('pedidoDescuento').value) || 0;

    if (!clienteId) {
        mostrarMensaje('Seleccione un cliente', 'error');
        return;
    }

    if (fechaEntrega) {
        const hoy = obtenerFechaLocal();
        if (fechaEntrega < hoy) {
            mostrarMensaje('La fecha de entrega no puede ser anterior a hoy', 'error');
            return;
        }
    }

    if (productosSeleccionados.length === 0) {
        mostrarMensaje('Agregue al menos un producto', 'error');
        return;
    }

    const data = {
        fecha_entrega: fechaEntrega || null,
        observaciones: observaciones,
        descuento: descuento,
        detalles: productosSeleccionados
    };

    try {
        const response = await fetchAPI(`/api/pedidos/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });

        if (response.success) {
            mostrarMensaje('Pedido actualizado exitosamente', 'success');
            cerrarModal('modalNuevoPedido');
            // Restaurar botón original
            document.querySelector('#modalNuevoPedido .modal-header h2').textContent = 'Nuevo Pedido';
            document.querySelector('#modalNuevoPedido .modal-footer .btn-primary').textContent = 'Guardar Pedido';
            document.querySelector('#modalNuevoPedido .modal-footer .btn-primary').setAttribute('onclick', 'guardarPedido()');
            cargarPedidos();
        } else {
            mostrarMensaje(response.data.error || 'Error al actualizar pedido', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al actualizar pedido:', error);
    }
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function agregarProducto() {
    const productoId = document.getElementById('productoSelect').value;
    const precio = parseFloat(document.getElementById('productoPrecio').value);

    if (!productoId) {
        mostrarMensaje('Seleccione un producto', 'error');
        return;
    }

    const producto = productosData.find(p => p.id == productoId);

    let cantidad;

    if (producto.unidad_medida === 'kg') {
        // Usar peso como cantidad
        cantidad = parseFloat(document.getElementById('productoPeso').value);
        if (!cantidad || cantidad <= 0) {
            mostrarMensaje('Ingrese el peso del producto', 'error');
            return;
        }
    } else {
        cantidad = parseInt(document.getElementById('productoCantidad').value);
        if (!cantidad || cantidad <= 0) {
            mostrarMensaje('Ingrese una cantidad válida', 'error');
            return;
        }
        if (cantidad > producto.stock_actual) {
            mostrarMensaje(`Stock insuficiente. Disponible: ${producto.stock_actual}`, 'error');
            return;
        }
    }

    // Calcular subtotal con 2 decimales (redondeo matemático)
    const subtotal = Math.round(cantidad * precio * 100) / 100;

    // Si ya existe el producto, actualizar
    const index = productosSeleccionados.findIndex(p => p.producto_id == productoId);
    if (index >= 0 && producto.unidad_medida !== 'kg') {
        // Para kg siempre agregar nueva línea (pueden ser pesos distintos)
        productosSeleccionados[index].cantidad += cantidad;
    } else {
        productosSeleccionados.push({
            producto_id: parseInt(productoId),
            nombre: producto.nombre,
            unidad_medida: producto.unidad_medida,
            cantidad: cantidad,
            precio_unitario: precio
        });
    }

    // Limpiar campos
    document.getElementById('productoSelect').value = '';
    document.getElementById('productoCantidad').value = '';
    document.getElementById('productoPeso').value = '';
    document.getElementById('productoPrecio').value = '';
    document.getElementById('filaCantidadNormal').style.display = 'block';
    document.getElementById('filaPesoKg').style.display = 'none';
    document.getElementById('productoSubtotalPreview').style.display = 'none';

    actualizarTablaProductos();
    calcularTotal();
}

function eliminarProducto(index) {
    productosSeleccionados.splice(index, 1);
    actualizarTablaProductos();
    calcularTotal();
}

function actualizarTablaProductos() {
    const tbody = document.getElementById('productosBody');
    
    if (productosSeleccionados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay productos agregados</td></tr>';
        return;
    }

    tbody.innerHTML = productosSeleccionados.map((prod, index) => {
        const subtotal = Math.round(prod.cantidad * prod.precio_unitario * 100) / 100;
        const esKg = prod.unidad_medida === 'kg';
        const cantidadDisplay = esKg 
            ? `${prod.cantidad.toFixed(3)} kg` 
            : prod.cantidad;
        const precioDisplay = esKg
            ? `Bs. ${parseFloat(prod.precio_unitario).toFixed(2)}/kg`
            : `Bs. ${parseFloat(prod.precio_unitario).toFixed(2)}`;

        return `
            <tr>
                <td>${prod.nombre}</td>
                <td>${cantidadDisplay}</td>
                <td>${precioDisplay}</td>
                <td><strong>Bs. ${subtotal.toFixed(2)}</strong></td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="eliminarProducto(${index})">
                        Eliminar
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function calcularTotal() {
    const subtotal = productosSeleccionados.reduce((sum, prod) => {
        return sum + (prod.cantidad * prod.precio_unitario);
    }, 0);

    const descuento = parseFloat(document.getElementById('pedidoDescuento').value) || 0;
    const total = subtotal - descuento;

    document.getElementById('pedidoSubtotal').textContent = `Bs. ${formatearPrecio(subtotal)}`;
    document.getElementById('pedidoTotal').textContent = `Bs. ${formatearPrecio(total)}`;
}

async function guardarPedido() {
    const clienteId = document.getElementById('pedidoCliente').value;
    const fechaEntrega = document.getElementById('pedidoFechaEntrega').value;
    const observaciones = document.getElementById('pedidoObservaciones').value;
    const descuento = parseFloat(document.getElementById('pedidoDescuento').value) || 0;

    if (!clienteId) {
        mostrarMensaje('Seleccione un cliente', 'error');
        return;
    }

    if (fechaEntrega) {
        const hoy = obtenerFechaLocal();
        if (fechaEntrega < hoy) {
            mostrarMensaje('La fecha de entrega no puede ser anterior a hoy', 'error');
            return;
        }
    }

    if (productosSeleccionados.length === 0) {
        mostrarMensaje('Agregue al menos un producto', 'error');
        return;
    }

    const data = {
        cliente_id: parseInt(clienteId),
        fecha_entrega: fechaEntrega || null,
        observaciones: observaciones,
        descuento: descuento,
        detalles: productosSeleccionados
    };

    try {
        const response = await fetchAPI('/api/pedidos', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        if (response.success) {
            mostrarMensaje('Pedido creado exitosamente', 'success');
            cerrarModal('modalNuevoPedido');
            cargarPedidos();
        } else {
            mostrarMensaje(response.data.error || 'Error al crear pedido', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al guardar pedido:', error);
    }
}

async function verPedido(id) {
    pedidoActualId = id;
    document.getElementById('modalVerPedido').style.display = 'block';
    document.getElementById('contenidoVerPedido').innerHTML = '<div class="spinner"></div>';

    try {
        const response = await fetchAPI(`/api/pedidos/${id}`);

        if (response.success) {
            const pedido = response.data.pedido;
            
            document.getElementById('tituloVerPedido').textContent = `Pedido ${pedido.numero_pedido}`;
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <p><strong>Cliente:</strong> ${pedido.cliente_nombre}</p>
                    <p><strong>Fecha:</strong> ${formatearFechaHora(pedido.fecha_pedido)}</p>
                    <p><strong>Estado:</strong> <span class="badge badge-${pedido.estado}">${pedido.estado.toUpperCase()}</span></p>
                    ${pedido.fecha_entrega ? `<p><strong>Fecha de Entrega:</strong> ${formatearFecha(pedido.fecha_entrega)}</p>` : ''}
                    ${pedido.observaciones ? `<p><strong>Observaciones:</strong> ${pedido.observaciones}</p>` : ''}
                </div>

                <h3 style="color: #3b82f6; margin-bottom: 10px;">Productos</h3>
                <table style="margin-bottom: 20px;">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Cantidad</th>
                            <th>Precio Unit.</th>
                            <th>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${pedido.detalles.map(det => `
                            <tr>
                                <td>${det.producto_nombre}</td>
                                <td>${det.cantidad}</td>
                                <td>Bs. ${formatearPrecio(det.precio_unitario)}</td>
                                <td><strong>Bs. ${formatearPrecio(det.subtotal)}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div style="text-align: right; background: #f3f4f6; padding: 15px; border-radius: 8px;">
                    <p><strong>Subtotal:</strong> Bs. ${formatearPrecio(pedido.subtotal)}</p>
                    <p><strong>Descuento:</strong> Bs. ${formatearPrecio(pedido.descuento)}</p>
                    <p style="font-size: 18px; color: #3b82f6;"><strong>TOTAL:</strong> Bs. ${formatearPrecio(pedido.total)}</p>
                </div>
            `;

            document.getElementById('contenidoVerPedido').innerHTML = html;
            document.getElementById('btnDescargarPDF').onclick = () => descargarPDF(id);

        } else {
            document.getElementById('contenidoVerPedido').innerHTML = 
                '<p class="text-center">Error al cargar pedido</p>';
        }

    } catch (error) {
        document.getElementById('contenidoVerPedido').innerHTML = 
            '<p class="text-center">Error de conexión</p>';
        console.error('❌ Error al ver pedido:', error);
    }
}

async function cambiarEstado(id, nuevoEstado) {
    const mensaje = nuevoEstado === 'entregado' 
        ? '¿Marcar este pedido como entregado?' 
        : '¿Está seguro de cancelar este pedido?';

    if (!confirm(mensaje)) return;

    try {
        const response = await fetchAPI(`/api/pedidos/${id}/cambiar-estado`, {
            method: 'PATCH',
            body: JSON.stringify({ estado: nuevoEstado })
        });

        if (response.success) {
            mostrarMensaje(`Pedido ${nuevoEstado} exitosamente`, 'success');
            cargarPedidos();
        } else {
            mostrarMensaje(response.data.error || 'Error al cambiar estado', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al cambiar estado:', error);
    }
}

async function descargarPDF(id) {
    try {
        window.open(`${window.location.origin}/api/pedidos/${id}/pdf`, '_blank');
    } catch (error) {
        mostrarMensaje('Error al descargar PDF', 'error');
        console.error('❌ Error al descargar PDF:', error);
    }
}

async function verificarDevolucionesPendientes(clienteId) {
    try {
        const response = await fetchAPI(`/api/devoluciones/cliente/${clienteId}/pendientes-alerta`);
        
        if (response.success && response.data.tiene_devoluciones_pendientes) {
            document.getElementById('alertaDevolucionesPendientes').classList.remove('hidden');
        } else {
            document.getElementById('alertaDevolucionesPendientes').classList.add('hidden');
        }

    } catch (error) {
        console.error('❌ Error al verificar devoluciones:', error);
    }
}

function limpiarFiltros() {
    document.getElementById('buscar').value = '';
    document.getElementById('filtroEstado').value = '';
    document.getElementById('fechaDesde').value = '';
    document.getElementById('fechaHasta').value = '';
    paginaActual = 1;
    cargarPedidos();
}

function formatearFecha(fecha) {
    if (!fecha) return '-';
    // Si ya viene en formato dd/mm/yyyy o dd/mm/yyyy HH:MM (del backend)
    if (fecha.includes('/')) {
        return fecha.split(' ')[0]; // Retorna solo la parte de fecha
    }
    const date = new Date(fecha);
    if (isNaN(date)) return '-';
    return date.toLocaleDateString('es-BO');
}

function formatearFechaHora(fecha) {
    if (!fecha) return '-';
    if (fecha.includes('/')) {
        return fecha; // Ya viene formateado del backend
    }
    const date = new Date(fecha);
    if (isNaN(date)) return '-';
    return date.toLocaleString('es-BO');
}

function formatearPrecio(precio) {
    return parseFloat(precio).toFixed(2);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function imprimirPedido() {
    const contenido = document.getElementById('contenidoVerPedido').innerHTML;
    const titulo = document.getElementById('tituloVerPedido').textContent;
    
    const ventana = window.open('', '_blank');
    ventana.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>${titulo}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; color: #333; }
                h3 { color: #3b82f6; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                th { background: #2c3e50; color: white; padding: 8px; text-align: left; }
                td { padding: 8px; border-bottom: 1px solid #ddd; }
                .badge { padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold; }
                div[style*="text-align: right"] { background: #f3f4f6; padding: 15px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <h2>DISTRIBUIDORA DE QUESOS CAROLINA</h2>
            <h3>${titulo}</h3>
            ${contenido}
        </body>
        </html>
    `);
    ventana.document.close();
    ventana.focus();
    setTimeout(() => { ventana.print(); ventana.close(); }, 500);
}

async function generarListaDia() {
    document.getElementById('modalListaDia').style.display = 'block';
    document.getElementById('contenidoListaDia').innerHTML = '<div class="spinner"></div><p class="text-center">Cargando...</p>';

    try {
        const hoy = obtenerFechaLocal();
        const response = await fetchAPI(`/api/pedidos/resumen-dia?fecha=${hoy}`);

        if (!response.success) {
            document.getElementById('contenidoListaDia').innerHTML = '<p class="text-center">Error al cargar pedidos</p>';
            return;
        }

        const data = response.data;

        if (!data.resumen || data.resumen.length === 0) {
            document.getElementById('contenidoListaDia').innerHTML = `
                <p class="text-center" style="color: #666; padding: 20px;">
                    No hay pedidos registrados para hoy
                </p>`;
            return;
        }

        const fechaFormateada = new Date().toLocaleDateString('es-BO', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });

        let html = `
            <div style="background: #f8f9fa; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2c3e50;">
                <strong>📅 ${fechaFormateada}</strong> &nbsp;|&nbsp;
                ${data.total_clientes} clientes &nbsp;|&nbsp;
                ${data.total_pedidos} pedidos &nbsp;|&nbsp;
                <strong style="color: #10b981;">Total: Bs. ${formatearPrecio(data.total_general)}</strong>
            </div>
            <div id="listaClientesDia">
        `;

        data.resumen.forEach((cliente, index) => {
            // Armar línea de productos: "4 Queso Mozzarella, 5 Queso Gouda"
            const productosLinea = cliente.productos.map(p => {
                const cantidad = parseFloat(p.cantidad) === parseInt(p.cantidad)
                    ? parseInt(p.cantidad)
                    : parseFloat(p.cantidad).toFixed(2);
                return `${cantidad} ${p.nombre}`;
            }).join(', ');

            html += `
                <div style="
                    display: flex;
                    align-items: baseline;
                    gap: 10px;
                    padding: 12px 0;
                    border-bottom: 1px solid #e5e7eb;
                    ${index === data.resumen.length - 1 ? 'border-bottom: none;' : ''}
                ">
                    <span style="
                        min-width: 220px;
                        font-weight: bold;
                        color: #2c3e50;
                        font-size: 15px;
                    ">${cliente.cliente_nombre}:</span>
                    <span style="color: #444; font-size: 14px; flex: 1;">${productosLinea}</span>
                    <span style="color: #10b981; font-weight: bold; white-space: nowrap; font-size: 13px;">
                        Bs. ${formatearPrecio(cliente.total)}
                    </span>
                </div>
            `;
        });

        html += `</div>`;
        document.getElementById('contenidoListaDia').innerHTML = html;

    } catch (error) {
        document.getElementById('contenidoListaDia').innerHTML = '<p class="text-center">Error de conexión</p>';
        console.error('❌ Error al generar lista:', error);
    }
}

function imprimirListaDia() {
    const contenido = document.getElementById('contenidoListaDia').innerHTML;
    const fechaFormateada = new Date().toLocaleDateString('es-BO', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });

    const ventana = window.open('', '_blank');
    ventana.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Lista de Pedidos del Día</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    padding: 30px; 
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                }
                h1 { color: #2c3e50; font-size: 20px; margin-bottom: 5px; }
                h2 { color: #555; font-size: 16px; font-weight: normal; margin-bottom: 20px; }
                .resumen { 
                    background: #f8f9fa; 
                    padding: 10px 15px; 
                    border-left: 4px solid #2c3e50;
                    margin-bottom: 20px;
                    font-size: 14px;
                }
                .fila {
                    display: flex;
                    gap: 10px;
                    padding: 10px 0;
                    border-bottom: 1px solid #ddd;
                    font-size: 14px;
                    align-items: baseline;
                }
                .cliente { min-width: 200px; font-weight: bold; color: #2c3e50; }
                .productos { flex: 1; color: #444; }
                .total { color: #10b981; font-weight: bold; white-space: nowrap; }
                @media print {
                    body { padding: 15px; }
                    button { display: none; }
                }
            </style>
        </head>
        <body>
            <h1>DISTRIBUIDORA DE QUESOS CAROLINA</h1>
            <h2>Lista de Pedidos — ${fechaFormateada}</h2>
            ${contenido}
        </body>
        </html>
    `);
    ventana.document.close();
    ventana.focus();
    setTimeout(() => { ventana.print(); ventana.close(); }, 500);
}

function descargarPDFListaDia() {
    const hoy = obtenerFechaLocal();
    window.open(`${window.location.origin}/api/pedidos/resumen-dia/pdf?fecha=${hoy}`, '_blank');
}