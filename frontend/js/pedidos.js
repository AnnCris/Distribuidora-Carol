let paginaActual = 1;
let productosSeleccionados = [];
let clientesData = [];
let productosData = [];
let pedidoActualId = null;

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

    // Cambio de producto
    document.getElementById('productoSelect').addEventListener('change', (e) => {
        const productoId = e.target.value;
        if (productoId) {
            const producto = productosData.find(p => p.id == productoId);
            if (producto) {
                document.getElementById('productoPrecio').value = producto.precio_venta;
            }
        } else {
            document.getElementById('productoPrecio').value = '';
        }
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

            const tbody = document.getElementById('pedidosBody');
            tbody.innerHTML = response.data.pedidos.map(pedido => `
                <tr>
                    <td><strong>${pedido.numero_pedido}</strong></td>
                    <td>${pedido.cliente_nombre}</td>
                    <td>${formatearFecha(pedido.fecha_pedido)}</td>
                    <td><strong>Bs. ${formatearPrecio(pedido.total)}</strong></td>
                    <td><span class="badge badge-${pedido.estado}">${pedido.estado.toUpperCase()}</span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="verPedido(${pedido.id})">Ver</button>
                        ${pedido.estado === 'pendiente' ? `
                            <button class="btn btn-success btn-sm" onclick="cambiarEstado(${pedido.id}, 'entregado')">Entregar</button>
                            <button class="btn btn-danger btn-sm" onclick="cambiarEstado(${pedido.id}, 'cancelado')">Cancelar</button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');

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
    productosSeleccionados = [];
    document.getElementById('formNuevoPedido').reset();
    actualizarTablaProductos();
    calcularTotal();
    document.getElementById('alertaDevolucionesPendientes').classList.add('hidden');
    document.getElementById('modalNuevoPedido').style.display = 'block';
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function agregarProducto() {
    const productoId = document.getElementById('productoSelect').value;
    const cantidad = parseInt(document.getElementById('productoCantidad').value); // CAMBIO: parseInt
    const precio = parseFloat(document.getElementById('productoPrecio').value);

    if (!productoId || !cantidad || cantidad <= 0) {
        mostrarMensaje('Seleccione un producto y cantidad válida', 'error');
        return;
    }

    const producto = productosData.find(p => p.id == productoId);
    
    if (cantidad > producto.stock_actual) {
        mostrarMensaje(`Stock insuficiente. Disponible: ${producto.stock_actual}`, 'error');
        return;
    }

    const index = productosSeleccionados.findIndex(p => p.producto_id == productoId);
    if (index >= 0) {
        productosSeleccionados[index].cantidad += cantidad;
    } else {
        productosSeleccionados.push({
            producto_id: parseInt(productoId),
            nombre: producto.nombre,
            cantidad: cantidad, // Ya es entero
            precio_unitario: precio
        });
    }

    document.getElementById('productoSelect').value = '';
    document.getElementById('productoCantidad').value = '';
    document.getElementById('productoPrecio').value = '';

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
        const subtotal = prod.cantidad * prod.precio_unitario;
        return `
            <tr>
                <td>${prod.nombre}</td>
                <td>${prod.cantidad}</td>
                <td>Bs. ${formatearPrecio(prod.precio_unitario)}</td>
                <td><strong>Bs. ${formatearPrecio(subtotal)}</strong></td>
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
    const date = new Date(fecha);
    return date.toLocaleDateString('es-BO');
}

function formatearFechaHora(fecha) {
    const date = new Date(fecha);
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