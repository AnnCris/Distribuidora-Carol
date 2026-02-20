let paginaActual = 1;
let productosDevolucion = [];
let clientesData = [];
let productosData = [];
let devolucionActualId = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Devoluciones cargado');

    // PRIMERO: Verificar autenticación
    const autenticado = await verificarAuth();
    if (!autenticado) {
        console.log('❌ No autenticado');
        return;
    }

    console.log('✅ Autenticado, cargando devoluciones...');

    // Cargar información del usuario
    cargarInfoUsuario();

    // Cargar datos iniciales
    await Promise.all([
        cargarDevoluciones(),
        cargarClientes(),
        cargarProductos(),
        cargarMotivos()
    ]);

    // Filtros
    document.getElementById('buscar').addEventListener('input', debounce(cargarDevoluciones, 500));
    document.getElementById('filtroEstado').addEventListener('change', cargarDevoluciones);
    document.getElementById('filtroMotivo').addEventListener('change', cargarDevoluciones);
    document.getElementById('fechaDesde').addEventListener('change', cargarDevoluciones);

    // Paginación
    document.getElementById('btnAnterior').addEventListener('click', () => {
        if (paginaActual > 1) {
            paginaActual--;
            cargarDevoluciones();
        }
    });

    document.getElementById('btnSiguiente').addEventListener('click', () => {
        paginaActual++;
        cargarDevoluciones();
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

async function cargarDevoluciones() {
    try {
        document.getElementById('loadingDevoluciones').classList.remove('hidden');
        document.getElementById('tablaDevoluciones').classList.add('hidden');
        document.getElementById('noDevoluciones').classList.add('hidden');

        const buscar = document.getElementById('buscar').value;
        const estado = document.getElementById('filtroEstado').value;
        const motivo = document.getElementById('filtroMotivo').value;
        const fechaDesde = document.getElementById('fechaDesde').value;

        let url = `/api/devoluciones?page=${paginaActual}&per_page=20`;
        if (buscar) url += `&buscar=${buscar}`;
        if (estado) url += `&estado=${estado}`;
        if (motivo) url += `&motivo=${motivo}`;
        if (fechaDesde) url += `&fecha_desde=${fechaDesde}`;

        const response = await fetchAPI(url);

        document.getElementById('loadingDevoluciones').classList.add('hidden');

        if (response.success && response.data.devoluciones && response.data.devoluciones.length > 0) {
            document.getElementById('tablaDevoluciones').classList.remove('hidden');
            document.getElementById('paginacion').classList.remove('hidden');

            const tbody = document.getElementById('devolucionesBody');
            tbody.innerHTML = response.data.devoluciones.map(dev => `
                <tr>
                    <td><strong>${dev.numero_devolucion}</strong></td>
                    <td>${dev.cliente_nombre}</td>
                    <td>${formatearFecha(dev.fecha_devolucion)}</td>
                    <td>${traducirMotivo(dev.motivo)}</td>
                    <td><span class="badge badge-${dev.estado === 'pendiente' ? 'pendiente' : 'entregado'}">
                        ${dev.estado.toUpperCase()}
                    </span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="verDevolucion(${dev.id})">Ver</button>
                        ${dev.estado === 'pendiente' ? `
                            <button class="btn btn-danger btn-sm" onclick="eliminarDevolucion(${dev.id})">Eliminar</button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');

            document.getElementById('infoPagina').textContent = 
                `Página ${response.data.pagina_actual} de ${response.data.total_paginas}`;
            
            document.getElementById('btnAnterior').disabled = paginaActual === 1;
            document.getElementById('btnSiguiente').disabled = paginaActual >= response.data.total_paginas;

        } else {
            document.getElementById('noDevoluciones').classList.remove('hidden');
            document.getElementById('paginacion').classList.add('hidden');
        }

    } catch (error) {
        document.getElementById('loadingDevoluciones').classList.add('hidden');
        document.getElementById('noDevoluciones').classList.remove('hidden');
        console.error('❌ Error al cargar devoluciones:', error);
    }
}

async function cargarClientes() {
    try {
        const response = await fetchAPI('/api/clientes/todos');
        if (response.success) {
            clientesData = response.data.clientes;
            const select = document.getElementById('devolucionCliente');
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
            const selectDevuelto = document.getElementById('productoDevueltoSelect');
            const selectReemplazo = document.getElementById('productoReemplazoSelect');
            
            const options = productosData.map(p => 
                `<option value="${p.id}">${p.nombre}</option>`
            ).join('');
            
            selectDevuelto.innerHTML = '<option value="">Seleccione producto</option>' + options;
            selectReemplazo.innerHTML = '<option value="">Sin reemplazo</option>' + options;
        }
    } catch (error) {
        console.error('❌ Error al cargar productos:', error);
    }
}

async function cargarMotivos() {
    try {
        const response = await fetchAPI('/api/devoluciones/motivos');
        if (response.success) {
            const selectMotivo = document.getElementById('devolucionMotivo');
            const filtroMotivo = document.getElementById('filtroMotivo');
            
            const options = response.data.motivos.map(m => 
                `<option value="${m.valor}">${m.nombre}</option>`
            ).join('');
            
            selectMotivo.innerHTML += options;
            filtroMotivo.innerHTML += options;
        }
    } catch (error) {
        console.error('❌ Error al cargar motivos:', error);
    }
}

function abrirModalNuevaDevolucion() {
    productosDevolucion = [];
    document.getElementById('formNuevaDevolucion').reset();
    actualizarTablaProductosDevolucion();
    document.getElementById('modalNuevaDevolucion').style.display = 'block';
}

function agregarProductoDevolucion() {
    const productoId = document.getElementById('productoDevueltoSelect').value;
    const cantidad = parseInt(document.getElementById('productoCantidadDev').value); // CAMBIO
    const reemplazoId = document.getElementById('productoReemplazoSelect').value;

    if (!productoId || !cantidad || cantidad <= 0) {
        mostrarMensaje('Seleccione un producto y cantidad válida', 'error');
        return;
    }

    const producto = productosData.find(p => p.id == productoId);
    const reemplazo = reemplazoId ? productosData.find(p => p.id == reemplazoId) : null;

    productosDevolucion.push({
        producto_id: parseInt(productoId),
        nombre: producto.nombre,
        cantidad: cantidad,
        producto_reemplazo_id: reemplazoId ? parseInt(reemplazoId) : null,
        reemplazo_nombre: reemplazo ? reemplazo.nombre : 'Sin reemplazo'
    });

    document.getElementById('productoDevueltoSelect').value = '';
    document.getElementById('productoCantidadDev').value = '';
    document.getElementById('productoReemplazoSelect').value = '';

    actualizarTablaProductosDevolucion();
}

function eliminarProductoDevolucion(index) {
    productosDevolucion.splice(index, 1);
    actualizarTablaProductosDevolucion();
}

function actualizarTablaProductosDevolucion() {
    const tbody = document.getElementById('productosDevolucionBody');
    
    if (productosDevolucion.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay productos agregados</td></tr>';
        return;
    }

    tbody.innerHTML = productosDevolucion.map((prod, index) => `
        <tr>
            <td>${prod.nombre}</td>
            <td>${prod.cantidad}</td>
            <td>${prod.reemplazo_nombre}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="eliminarProductoDevolucion(${index})">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join('');
}

async function guardarDevolucion() {
    const clienteId = document.getElementById('devolucionCliente').value;
    const motivo = document.getElementById('devolucionMotivo').value;
    const descripcion = document.getElementById('devolucionDescripcion').value;
    const observaciones = document.getElementById('devolucionObservaciones').value;

    if (!clienteId || !motivo) {
        mostrarMensaje('Complete los campos requeridos', 'error');
        return;
    }

    if (productosDevolucion.length === 0) {
        mostrarMensaje('Agregue al menos un producto', 'error');
        return;
    }

    const data = {
        cliente_id: parseInt(clienteId),
        motivo: motivo,
        descripcion_motivo: descripcion || null,
        observaciones: observaciones || null,
        detalles: productosDevolucion.map(p => ({
            producto_id: p.producto_id,
            cantidad: p.cantidad,
            producto_reemplazo_id: p.producto_reemplazo_id
        }))
    };

    try {
        const response = await fetchAPI('/api/devoluciones', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        if (response.success) {
            mostrarMensaje('Devolución registrada exitosamente', 'success');
            cerrarModal('modalNuevaDevolucion');
            cargarDevoluciones();
        } else {
            mostrarMensaje(response.data.error || 'Error al registrar devolución', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al guardar devolución:', error);
    }
}

async function verDevolucion(id) {
    devolucionActualId = id;
    document.getElementById('modalVerDevolucion').style.display = 'block';
    document.getElementById('contenidoVerDevolucion').innerHTML = '<div class="spinner"></div>';
    document.getElementById('btnDescargarPDFDev').style.display = 'none';

    try {
        const response = await fetchAPI(`/api/devoluciones/${id}`);

        if (response.success) {
            const dev = response.data.devolucion;
            
            document.getElementById('tituloVerDevolucion').textContent = dev.numero_devolucion;
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <p><strong>Cliente:</strong> ${dev.cliente_nombre}</p>
                    <p><strong>Fecha:</strong> ${formatearFechaHora(dev.fecha_devolucion)}</p>
                    <p><strong>Estado:</strong> <span class="badge badge-${dev.estado === 'pendiente' ? 'pendiente' : 'entregado'}">
                        ${dev.estado.toUpperCase()}
                    </span></p>
                    <p><strong>Motivo:</strong> ${traducirMotivo(dev.motivo)}</p>
                    ${dev.descripcion_motivo ? `<p><strong>Descripción:</strong> ${dev.descripcion_motivo}</p>` : ''}
                    ${dev.observaciones ? `<p><strong>Observaciones:</strong> ${dev.observaciones}</p>` : ''}
                </div>

                <h3 style="color: #ef4444; margin-bottom: 10px;">Productos Devueltos</h3>
                <table style="margin-bottom: 20px;">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Cantidad</th>
                            <th>Producto Reemplazo</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${dev.detalles.map(det => `
                            <tr>
                                <td>${det.producto_nombre}</td>
                                <td>${det.cantidad}</td>
                                <td>${det.producto_reemplazo_nombre || 'Sin reemplazo'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                ${dev.fecha_compensacion ? `
                    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px;">
                        <p><strong>✅ Compensado el:</strong> ${formatearFechaHora(dev.fecha_compensacion)}</p>
                    </div>
                ` : `
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px;">
                        <p style="color: #856404;"><strong>⚠️ Pendiente de compensación</strong></p>
                        <p style="color: #856404; font-size: 14px;">Esta devolución debe ser compensada en el próximo pedido del cliente.</p>
                    </div>
                `}
            `;

            document.getElementById('contenidoVerDevolucion').innerHTML = html;
            
            document.getElementById('btnDescargarPDFDev').style.display = 'inline-block';
            document.getElementById('btnDescargarPDFDev').onclick = () => descargarPDFDevolucion(id);

        } else {
            document.getElementById('contenidoVerDevolucion').innerHTML = 
                '<p class="text-center">Error al cargar devolución</p>';
        }

    } catch (error) {
        document.getElementById('contenidoVerDevolucion').innerHTML = 
            '<p class="text-center">Error de conexión</p>';
        console.error('❌ Error al ver devolución:', error);
    }
}

async function eliminarDevolucion(id) {
    if (!confirm('¿Está seguro de eliminar esta devolución?')) return;

    try {
        const response = await fetchAPI(`/api/devoluciones/${id}`, {
            method: 'DELETE'
        });

        if (response.success) {
            mostrarMensaje('Devolución eliminada exitosamente', 'success');
            cargarDevoluciones();
        } else {
            mostrarMensaje(response.data.error || 'Error al eliminar devolución', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al eliminar devolución:', error);
    }
}

function descargarPDFDevolucion(id) {
    window.open(`${window.location.origin}/api/devoluciones/${id}/pdf`, '_blank');
}

function traducirMotivo(motivo) {
    const motivos = {
        'vencido': 'Producto Vencido',
        'mal_estado': 'Mal Estado',
        'error_entrega': 'Error en la Entrega',
        'otro': 'Otro'
    };
    return motivos[motivo] || motivo;
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function limpiarFiltros() {
    document.getElementById('buscar').value = '';
    document.getElementById('filtroEstado').value = 'pendiente';
    document.getElementById('filtroMotivo').value = '';
    document.getElementById('fechaDesde').value = '';
    paginaActual = 1;
    cargarDevoluciones();
}

function formatearFecha(fecha) {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-BO');
}

function formatearFechaHora(fecha) {
    const date = new Date(fecha);
    return date.toLocaleString('es-BO');
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