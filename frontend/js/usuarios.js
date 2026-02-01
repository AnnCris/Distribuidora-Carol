let usuarioActualId = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 Usuarios cargado');

    // PRIMERO: Verificar autenticación
    const autenticado = await verificarAuth();
    if (!autenticado) {
        console.log('❌ No autenticado');
        return;
    }

    console.log('✅ Autenticado, verificando permisos...');

    // SEGUNDO: Verificar que sea admin
    const usuario = getUsuario();
    if (usuario.rol !== 'admin') {
        console.log('❌ No es admin');
        mostrarMensaje('Acceso denegado. Solo administradores pueden acceder.', 'error');
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 2000);
        return;
    }

    console.log('✅ Admin verificado, cargando usuarios...');

    // Cargar información del usuario
    cargarInfoUsuario();

    // Cargar usuarios
    await cargarUsuarios();

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
    }
}

async function cargarUsuarios() {
    try {
        document.getElementById('loadingUsuarios').classList.remove('hidden');
        document.getElementById('tablaUsuarios').classList.add('hidden');
        document.getElementById('noUsuarios').classList.add('hidden');

        const response = await fetchAPI('/api/usuarios');

        document.getElementById('loadingUsuarios').classList.add('hidden');

        if (response.success && response.data.usuarios && response.data.usuarios.length > 0) {
            document.getElementById('tablaUsuarios').classList.remove('hidden');

            const tbody = document.getElementById('usuariosBody');
            const usuarioActual = getUsuario();

            tbody.innerHTML = response.data.usuarios.map(usuario => `
                <tr>
                    <td><strong>${usuario.nombre}</strong></td>
                    <td>${usuario.email}</td>
                    <td><span class="badge ${usuario.rol === 'admin' ? 'badge-entregado' : 'badge-pendiente'}">
                        ${usuario.rol === 'admin' ? 'ADMINISTRADOR' : 'VENDEDOR'}
                    </span></td>
                    <td>${formatearFecha(usuario.fecha_creacion)}</td>
                    <td><span class="badge badge-${usuario.activo ? 'activo' : 'inactivo'}">
                        ${usuario.activo ? 'ACTIVO' : 'INACTIVO'}
                    </span></td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="editarUsuario(${usuario.id})">Editar</button>
                        ${usuarioActual.id !== usuario.id ? `
                            <button class="btn btn-${usuario.activo ? 'danger' : 'success'} btn-sm" 
                                    onclick="toggleActivo(${usuario.id}, ${usuario.activo})">
                                ${usuario.activo ? 'Desactivar' : 'Activar'}
                            </button>
                        ` : '<small style="color: #666;">(Usuario actual)</small>'}
                    </td>
                </tr>
            `).join('');

        } else {
            document.getElementById('noUsuarios').classList.remove('hidden');
        }

    } catch (error) {
        document.getElementById('loadingUsuarios').classList.add('hidden');
        document.getElementById('noUsuarios').classList.remove('hidden');
        console.error('❌ Error al cargar usuarios:', error);
    }
}

function abrirModalNuevoUsuario() {
    usuarioActualId = null;
    document.getElementById('tituloModalUsuario').textContent = 'Nuevo Usuario';
    document.getElementById('formUsuario').reset();
    document.getElementById('usuarioId').value = '';
    document.getElementById('grupoPassword').style.display = 'block';
    document.getElementById('usuarioPassword').required = true;
    document.getElementById('modalUsuario').style.display = 'block';
}

async function editarUsuario(id) {
    usuarioActualId = id;
    document.getElementById('tituloModalUsuario').textContent = 'Editar Usuario';
    
    try {
        const response = await fetchAPI(`/api/usuarios/${id}`);
        
        if (response.success) {
            const usuario = response.data.usuario;
            
            document.getElementById('usuarioId').value = usuario.id;
            document.getElementById('usuarioNombre').value = usuario.nombre;
            document.getElementById('usuarioEmail').value = usuario.email;
            document.getElementById('usuarioRol').value = usuario.rol;
            
            // Ocultar campo de contraseña al editar
            document.getElementById('grupoPassword').style.display = 'none';
            document.getElementById('usuarioPassword').required = false;
            document.getElementById('usuarioPassword').value = '';
            
            document.getElementById('modalUsuario').style.display = 'block';
        } else {
            mostrarMensaje('Error al cargar usuario', 'error');
        }
        
    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al editar usuario:', error);
    }
}

async function guardarUsuario() {
    const id = document.getElementById('usuarioId').value;
    const nombre = document.getElementById('usuarioNombre').value.trim();
    const email = document.getElementById('usuarioEmail').value.trim();
    const password = document.getElementById('usuarioPassword').value;
    const rol = document.getElementById('usuarioRol').value;

    if (!nombre || !email || !rol) {
        mostrarMensaje('Complete todos los campos requeridos', 'error');
        return;
    }

    // Validar email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        mostrarMensaje('Email inválido', 'error');
        return;
    }

    // Validar contraseña solo al crear
    if (!id && (!password || password.length < 6)) {
        mostrarMensaje('La contraseña debe tener al menos 6 caracteres', 'error');
        return;
    }

    const data = {
        nombre,
        email,
        rol
    };

    // Solo incluir password al crear
    if (!id) {
        data.password = password;
    }

    try {
        let response;
        
        if (id) {
            // Actualizar
            response = await fetchAPI(`/api/usuarios/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        } else {
            // Crear
            response = await fetchAPI('/api/usuarios', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        if (response.success) {
            mostrarMensaje(id ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente', 'success');
            cerrarModal('modalUsuario');
            cargarUsuarios();
        } else {
            mostrarMensaje(response.data.error || 'Error al guardar usuario', 'error');
        }

    } catch (error) {
        mostrarMensaje('Error de conexión', 'error');
        console.error('❌ Error al guardar usuario:', error);
    }
}

async function toggleActivo(id, estadoActual) {
    const accion = estadoActual ? 'desactivar' : 'activar';
    
    if (!confirm(`¿Está seguro de ${accion} este usuario?`)) return;

    try {
        const response = await fetchAPI(`/api/usuarios/${id}/toggle-activo`, {
            method: 'PATCH'
        });

        if (response.success) {
            mostrarMensaje(`Usuario ${accion}do exitosamente`, 'success');
            cargarUsuarios();
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

function formatearFecha(fecha) {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-BO');
}