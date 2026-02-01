let paginaActual = 1;
let clienteActualId = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Clientes cargado');

    // PRIMERO: Verificar autenticación
    const autenticado = await verificarAuth();
    if (!autenticado) {
        console.log('❌ No autenticado');
        return;
    }

    console.log('✅ Autenticado, cargando clientes...');

    // Cargar información del usuario
    cargarInfoUsuario();

    // Cargar datos iniciales
    await Promise.all([
        cargarClientes(),
        cargarZonas()
    ]);

    // Filtros
    document.getElementById('buscar').addEventListener('input', debounce(cargarClientes, 500));
    document.getElementById('filtroActivo').addEventListener('change', cargarClientes);
    document.getElementById('filtroZona').addEventListener('change', cargarClientes);

    // Paginación
    document.getElementById('btnAnterior').addEventListener('click', () => {
        if (paginaActual > 1) {
            paginaActual--;
            cargarClientes();
        }
    });

    document.getElementById('btnSiguiente').addEventListener('click', () => {
        paginaActual++;
        cargarClientes();
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

async function cargarClientes() {
    try {
        document.getElementById('loadingClientes').classList.remove('hidden');
        document.getElementById('tablaClientes').classList.add('hidden');
        document.getElementById('noClientes').classList.add('hidden');

        const buscar = document.getElementById('buscar').value;
        const activo = document.getElementById('filtroActivo').value;
        const zona = document.getElementById('filtroZona').value;

        let url = `/api/clientes?page=${paginaActual}&per_page=20`;
        if (buscar) url += `&buscar=${buscar}`;
        if (activo) url += `&activo=${activo}`;
        if (zona) url += `&zona=${zona}`;

        const response = await fetchAPI(url);

        document.getElementById('loadingClientes').classList.add('hidden');

        if (response.success && response.data.clientes && response.data.clientes.length > 0) {
            document.getElementById('tablaClientes').classList.remove('hidden');
            document.getElementById('paginacion').classList.remove('hidden');

            const tbody = document.getElementById('clientesBody');
            tbody.innerHTML = response.data.clientes.map(cliente => `
                <tr>
                    <td><strong>${cliente.nombre}</strong></td>
                    <td>${cliente.celular || '-'}</td>
                    <td>${cliente.zona || '-'}</td>
                    <td>${cliente.ciudad}</td>
                    <td><span class="badge badge-${cliente.activo ? 'activo' : 'inactivo'}">
                        ${cliente.activo ? 'ACTIVO' : 'INACTIVO'}
                    </span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="verCliente(${cliente.id})">Ver</button>
                        <button class="btn btn-secondary btn-sm" onclick="editarCliente(${cliente.id})">Editar</button>
                        <button class="btn btn-${cliente.activo ? 'danger' : 'success'} btn-sm" 
                                onclick="toggleActivo(${cliente.id}, ${cliente.activo})">
                            ${cliente.activo ? 'Desactivar' : 'Activar'}
                        </button>
                    </td>
                </tr>
            `).join('');

            document.getElementById('infoPagina').textContent = 
                `Página ${response.data.pagina_actual} de ${response.data.total_paginas}`;
            
            document.getElementById('btnAnterior').disabled = paginaActual === 1;
            document.getElementById('btnSiguiente').disabled = paginaActual >= response.data.total_paginas;

        } else {
            document.getElementById('noClientes').classList.remove('hidden');
            document.getElementById('paginacion').classList.add('hidden');
        }

    } catch (error) {
        document.getElementById('loadingClientes').classList.add('hidden');
        document.getElementById('noClientes').classList.remove('hidden');
        console.error('❌ Error al cargar clientes:', error);
    }
}

async function cargarZonas() {
    try {
        const response = await fetchAPI('/api/clientes/zonas');
        if (response.success) {
            const selectZona = document.getElementById('filtroZona');
            const datalist = document.getElementById('zonasDatalist');
            
            const zonasHTML = response.data.zonas.map(z => `<option value="${z}">${z}</option>`).join('');
            selectZona.innerHTML += zonasHTML;
            datalist.innerHTML = response.data.zonas.map(z => `<option value="${z}">`).join('');
        }
    } catch (error) {
        console.error('❌ Error al cargar zonas:', error);
    }
}

function abrirModalNuevoCliente() {
    clienteActualId = null;
    document.getElementById('tituloModalCliente').textContent = 'Nuevo Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = '';
    document.getElementById('clienteCiudad').value = 'La Paz';
    document.getElementById('modalCliente').style.display = 'block';
}

async function editarCliente(id) {
    clienteActualId = id;
    document.getElementById('tituloModalCliente').textContent = 'Editar Cliente';
    
    try {
        const response = await fetchAPI(`/api/clientes/${id}`);
        
        if (response.success) {
            const cliente = response.data.cliente;
            
            document.getElementById('clienteId').value = cliente.id;
            document.getElementById('clienteNombre').value = cliente.nombre;
            document.getElementById('clienteCelular').value = cliente.celular || '';
            document.getElementById('clienteDireccion').value = cliente.direccion || '';
            document.getElementById('clienteZona').value = cliente.zona || '';
            document.getElementById('clienteCiudad').value = cliente.ciudad;
            
            document.getElementById('modalCliente').style.display = 'block';
        } else {
            mostrarMensaje('Error al cargar cliente', 'error');
        }
        
    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al editar cliente:', error);
    }
}

async function guardarCliente() {
    const id = document.getElementById('clienteId').value;
    const nombre = document.getElementById('clienteNombre').value.trim();
    const celular = document.getElementById('clienteCelular').value.trim();
    const direccion = document.getElementById('clienteDireccion').value.trim();
    const zona = document.getElementById('clienteZona').value.trim();
    const ciudad = document.getElementById('clienteCiudad').value.trim();

    if (!nombre) {
        mostrarMensaje('El nombre es requerido', 'error');
        return;
    }

    // Validar celular si se proporciona
    if (celular && !/^[67]\d{7}$/.test(celular)) {
        mostrarMensaje('El celular debe tener 8 dígitos y empezar con 6 o 7', 'error');
        return;
    }

    const data = {
        nombre,
        celular: celular || null,
        direccion: direccion || null,
        zona: zona || null,
        ciudad: ciudad || 'La Paz'
    };

    try {
        let response;
        
        if (id) {
            // Actualizar
            response = await fetchAPI(`/api/clientes/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        } else {
            // Crear
            response = await fetchAPI('/api/clientes', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        if (response.success) {
            mostrarMensaje(id ? 'Cliente actualizado exitosamente' : 'Cliente creado exitosamente', 'success');
            cerrarModal('modalCliente');
            cargarClientes();
            if (!id) cargarZonas();
        } else {
            mostrarMensaje(response.data.error || 'Error al guardar cliente', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al guardar cliente:', error);
    }
}

async function verCliente(id) {
    document.getElementById('modalVerCliente').style.display = 'block';
    document.getElementById('contenidoVerCliente').innerHTML = '<div class="spinner"></div>';

    try {
        const response = await fetchAPI(`/api/clientes/${id}`);

        if (response.success) {
            const cliente = response.data.cliente;
            const stats = response.data.estadisticas;
            
            document.getElementById('tituloVerCliente').textContent = cliente.nombre;
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #3b82f6; margin-bottom: 10px;">Información General</h3>
                    <p><strong>Nombre:</strong> ${cliente.nombre}</p>
                    <p><strong>Celular:</strong> ${cliente.celular || 'No registrado'}</p>
                    <p><strong>Dirección:</strong> ${cliente.direccion || 'No registrada'}</p>
                    <p><strong>Zona:</strong> ${cliente.zona || 'No registrada'}</p>
                    <p><strong>Ciudad:</strong> ${cliente.ciudad}</p>
                    <p><strong>Estado:</strong> <span class="badge badge-${cliente.activo ? 'activo' : 'inactivo'}">
                        ${cliente.activo ? 'ACTIVO' : 'INACTIVO'}
                    </span></p>
                    <p><strong>Fecha de Registro:</strong> ${formatearFecha(cliente.fecha_registro)}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="color: #3b82f6; margin-bottom: 10px;">Estadísticas</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center;">
                            <p style="font-size: 24px; font-weight: bold; color: #3b82f6;">${stats.total_pedidos}</p>
                            <p style="font-size: 14px;">Pedidos</p>
                        </div>
                        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center;">
                            <p style="font-size: 24px; font-weight: bold; color: #ef4444;">${stats.total_devoluciones}</p>
                            <p style="font-size: 14px;">Devoluciones</p>
                        </div>
                        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center;">
                            <p style="font-size: 24px; font-weight: bold; color: #10b981;">Bs. ${formatearPrecio(stats.total_vendido)}</p>
                            <p style="font-size: 14px;">Total Vendido</p>
                        </div>
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="color: #3b82f6; margin-bottom: 10px;">Último Pedido</h3>
                    ${stats.ultimo_pedido ? `
                        <p><strong>N° Pedido:</strong> ${stats.ultimo_pedido.numero_pedido}</p>
                        <p><strong>Fecha:</strong> ${formatearFecha(stats.ultimo_pedido.fecha_pedido)}</p>
                        <p><strong>Total:</strong> Bs. ${formatearPrecio(stats.ultimo_pedido.total)}</p>
                        <p><strong>Estado:</strong> <span class="badge badge-${stats.ultimo_pedido.estado}">
                            ${stats.ultimo_pedido.estado.toUpperCase()}
                        </span></p>
                    ` : '<p>No hay pedidos registrados</p>'}
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <button class="btn btn-primary btn-sm" onclick="verHistorialPedidos(${id})">
                        Ver Historial de Pedidos
                    </button>
                </div>
            `;

            document.getElementById('contenidoVerCliente').innerHTML = html;

        } else {
            document.getElementById('contenidoVerCliente').innerHTML = 
                '<p class="text-center">Error al cargar cliente</p>';
        }

    } catch (error) {
        document.getElementById('contenidoVerCliente').innerHTML = 
            '<p class="text-center">Error de conexión</p>';
        console.error('❌ Error al ver cliente:', error);
    }
}

async function toggleActivo(id, estadoActual) {
    const accion = estadoActual ? 'desactivar' : 'activar';
    
    if (!confirm(`¿Está seguro de ${accion} este cliente?`)) return;

    try {
        const response = await fetchAPI(`/api/clientes/${id}/toggle-activo`, {
            method: 'PATCH'
        });

        if (response.success) {
            mostrarMensaje(`Cliente ${accion}do exitosamente`, 'success');
            cargarClientes();
        } else {
            mostrarMensaje(response.data.error || 'Error al cambiar estado', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al cambiar estado:', error);
    }
}

function verHistorialPedidos(clienteId) {
    window.location.href = `pedidos.html?cliente_id=${clienteId}`;
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function limpiarFiltros() {
    document.getElementById('buscar').value = '';
    document.getElementById('filtroActivo').value = 'true';
    document.getElementById('filtroZona').value = '';
    paginaActual = 1;
    cargarClientes();
}

function formatearFecha(fecha) {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-BO');
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