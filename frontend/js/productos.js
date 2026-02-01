let paginaActual = 1;
let productoActualId = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Productos cargado');

    // PRIMERO: Verificar autenticación
    const autenticado = await verificarAuth();
    if (!autenticado) {
        console.log('❌ No autenticado');
        return;
    }

    console.log('✅ Autenticado, cargando productos...');

    // Cargar información del usuario
    cargarInfoUsuario();

    // Cargar datos iniciales
    await Promise.all([
        cargarProductos(),
        cargarUnidades()
    ]);

    // Filtros
    document.getElementById('buscar').addEventListener('input', debounce(cargarProductos, 500));
    document.getElementById('filtroActivo').addEventListener('change', cargarProductos);
    document.getElementById('filtroStock').addEventListener('change', cargarProductos);
    document.getElementById('filtroUnidad').addEventListener('change', cargarProductos);

    // Paginación
    document.getElementById('btnAnterior').addEventListener('click', () => {
        if (paginaActual > 1) {
            paginaActual--;
            cargarProductos();
        }
    });

    document.getElementById('btnSiguiente').addEventListener('click', () => {
        paginaActual++;
        cargarProductos();
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

async function cargarProductos() {
    try {
        document.getElementById('loadingProductos').classList.remove('hidden');
        document.getElementById('tablaProductos').classList.add('hidden');
        document.getElementById('noProductos').classList.add('hidden');

        const buscar = document.getElementById('buscar').value;
        const activo = document.getElementById('filtroActivo').value;
        const stock = document.getElementById('filtroStock').value;
        const unidad = document.getElementById('filtroUnidad').value;

        let url = `/api/productos?page=${paginaActual}&per_page=20`;
        if (buscar) url += `&buscar=${buscar}`;
        if (activo) url += `&activo=${activo}`;
        if (stock === 'bajo') url += `&stock_bajo=true`;
        if (unidad) url += `&unidad_medida=${unidad}`;

        const response = await fetchAPI(url);

        document.getElementById('loadingProductos').classList.add('hidden');

        if (response.success && response.data.productos && response.data.productos.length > 0) {
            document.getElementById('tablaProductos').classList.remove('hidden');
            document.getElementById('paginacion').classList.remove('hidden');

            const tbody = document.getElementById('productosBody');
            tbody.innerHTML = response.data.productos.map(producto => `
                <tr>
                    <td><strong>${producto.codigo || '-'}</strong></td>
                    <td>${producto.nombre}</td>
                    <td><strong>Bs. ${formatearPrecio(producto.precio_venta)}</strong></td>
                    <td>
                        ${producto.stock_actual} 
                        ${producto.stock_bajo ? '<span style="color: #ef4444;">⚠️</span>' : ''}
                        <br>
                        <small style="color: #666;">Mín: ${producto.stock_minimo}</small>
                    </td>
                    <td>${producto.unidad_medida}</td>
                    <td><span class="badge badge-${producto.activo ? 'activo' : 'inactivo'}">
                        ${producto.activo ? 'ACTIVO' : 'INACTIVO'}
                    </span></td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editarProducto(${producto.id})">Editar</button>
                        <button class="btn btn-primary btn-sm" onclick="abrirModalAjustarStock(${producto.id}, '${producto.nombre}', ${producto.stock_actual})">Stock</button>
                        <button class="btn btn-${producto.activo ? 'danger' : 'success'} btn-sm" 
                                onclick="toggleActivo(${producto.id}, ${producto.activo})">
                            ${producto.activo ? 'Desactivar' : 'Activar'}
                        </button>
                    </td>
                </tr>
            `).join('');

            document.getElementById('infoPagina').textContent = 
                `Página ${response.data.pagina_actual} de ${response.data.total_paginas}`;
            
            document.getElementById('btnAnterior').disabled = paginaActual === 1;
            document.getElementById('btnSiguiente').disabled = paginaActual >= response.data.total_paginas;

        } else {
            document.getElementById('noProductos').classList.remove('hidden');
            document.getElementById('paginacion').classList.add('hidden');
        }

    } catch (error) {
        document.getElementById('loadingProductos').classList.add('hidden');
        document.getElementById('noProductos').classList.remove('hidden');
        console.error('❌ Error al cargar productos:', error);
    }
}

async function cargarUnidades() {
    try {
        const response = await fetchAPI('/api/productos/unidades-medida');
        if (response.success) {
            const select = document.getElementById('filtroUnidad');
            select.innerHTML += response.data.unidades_medida
                .map(u => `<option value="${u}">${u}</option>`).join('');
        }
    } catch (error) {
        console.error('❌ Error al cargar unidades:', error);
    }
}

function abrirModalNuevoProducto() {
    productoActualId = null;
    document.getElementById('tituloModalProducto').textContent = 'Nuevo Producto';
    document.getElementById('formProducto').reset();
    document.getElementById('productoId').value = '';
    document.getElementById('productoStock').value = '0';
    document.getElementById('productoStockMin').value = '5';
    document.getElementById('productoStock').disabled = false;
    document.getElementById('modalProducto').style.display = 'block';
}

async function editarProducto(id) {
    productoActualId = id;
    document.getElementById('tituloModalProducto').textContent = 'Editar Producto';
    
    try {
        const response = await fetchAPI(`/api/productos/${id}`);
        
        if (response.success) {
            const producto = response.data.producto;
            
            document.getElementById('productoId').value = producto.id;
            document.getElementById('productoCodigo').value = producto.codigo || '';
            document.getElementById('productoNombre').value = producto.nombre;
            document.getElementById('productoDescripcion').value = producto.descripcion || '';
            document.getElementById('productoUnidad').value = producto.unidad_medida;
            document.getElementById('productoPrecio').value = producto.precio_venta;
            document.getElementById('productoStock').value = producto.stock_actual;
            document.getElementById('productoStockMin').value = producto.stock_minimo;
            
            // Deshabilitar campo de stock al editar (usar el modal de ajuste)
            document.getElementById('productoStock').disabled = true;
            
            document.getElementById('modalProducto').style.display = 'block';
        } else {
            mostrarMensaje('Error al cargar producto', 'error');
        }
        
    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al editar producto:', error);
    }
}

async function guardarProducto() {
    const id = document.getElementById('productoId').value;
    const codigo = document.getElementById('productoCodigo').value.trim();
    const nombre = document.getElementById('productoNombre').value.trim();
    const descripcion = document.getElementById('productoDescripcion').value.trim();
    const unidad = document.getElementById('productoUnidad').value;
    const precio = parseFloat(document.getElementById('productoPrecio').value);
    const stock = parseInt(document.getElementById('productoStock').value);
    const stockMin = parseInt(document.getElementById('productoStockMin').value);

    if (!nombre || !precio || precio <= 0) {
        mostrarMensaje('Complete los campos requeridos correctamente', 'error');
        return;
    }

    const data = {
        codigo: codigo || null,
        nombre,
        descripcion: descripcion || null,
        unidad_medida: unidad,
        precio_venta: precio,
        stock_minimo: stockMin
    };

    // Solo incluir stock_actual al crear
    if (!id) {
        data.stock_actual = stock;
    }

    try {
        let response;
        
        if (id) {
            // Actualizar
            response = await fetchAPI(`/api/productos/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        } else {
            // Crear
            response = await fetchAPI('/api/productos', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        if (response.success) {
            mostrarMensaje(id ? 'Producto actualizado exitosamente' : 'Producto creado exitosamente', 'success');
            cerrarModal('modalProducto');
            
            // Rehabilitar campo stock
            document.getElementById('productoStock').disabled = false;
            
            cargarProductos();
        } else {
            mostrarMensaje(response.data.error || 'Error al guardar producto', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al guardar producto:', error);
    }
}

function abrirModalAjustarStock(id, nombre, stockActual) {
    document.getElementById('stockProductoId').value = id;
    document.getElementById('stockProductoInfo').innerHTML = `
        <strong>${nombre}</strong><br>
        Stock Actual: <strong>${stockActual}</strong>
    `;
    document.getElementById('stockCantidad').value = '';
    document.getElementById('modalAjustarStock').style.display = 'block';
}

async function guardarAjusteStock() {
    const id = document.getElementById('stockProductoId').value;
    const operacion = document.getElementById('stockOperacion').value;
    const cantidad = parseInt(document.getElementById('stockCantidad').value);

    if (!cantidad || cantidad <= 0) {
        mostrarMensaje('Ingrese una cantidad válida', 'error');
        return;
    }

    try {
        const response = await fetchAPI(`/api/productos/${id}/ajustar-stock`, {
            method: 'PATCH',
            body: JSON.stringify({ cantidad, operacion })
        });

        if (response.success) {
            mostrarMensaje('Stock ajustado exitosamente', 'success');
            cerrarModal('modalAjustarStock');
            cargarProductos();
        } else {
            mostrarMensaje(response.data.error || 'Error al ajustar stock', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al ajustar stock:', error);
    }
}

async function toggleActivo(id, estadoActual) {
    const accion = estadoActual ? 'desactivar' : 'activar';
    
    if (!confirm(`¿Está seguro de ${accion} este producto?`)) return;

    try {
        const response = await fetchAPI(`/api/productos/${id}/toggle-activo`, {
            method: 'PATCH'
        });

        if (response.success) {
            mostrarMensaje(`Producto ${accion}do exitosamente`, 'success');
            cargarProductos();
        } else {
            mostrarMensaje(response.data.error || 'Error al cambiar estado', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al cambiar estado:', error);
    }
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function limpiarFiltros() {
    document.getElementById('buscar').value = '';
    document.getElementById('filtroActivo').value = 'true';
    document.getElementById('filtroStock').value = '';
    document.getElementById('filtroUnidad').value = '';
    paginaActual = 1;
    cargarProductos();
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