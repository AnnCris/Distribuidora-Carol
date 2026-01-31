let usuarioActualId = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAuth()) {
        window.location.href = 'login.html';
        return;
    }

    const user = getUser();
    if (user.rol !== 'admin') {
        mostrarAlerta('Acceso denegado. Solo administradores pueden acceder.', 'error');
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 2000);
        return;
    }

    cargarInfoUsuario();
    await cargarUsuarios();

    // Menu toggle
    document.getElementById('menuToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('active');
    });
});

async function cargarUsuarios() {
    try {
        document.getElementById('loadingUsuarios').classList.remove('hidden');
        document.getElementById('tablaUsuarios').classList.add('hidden');
        document.getElementById('noUsuarios').classList.add('hidden');

        const response = await fetchAPI('/usuarios');

        document.getElementById('loadingUsuarios').classList.add('hidden');

        if (response.success && response.data.usuarios.length > 0) {
            document.getElementById('tablaUsuarios').classList.remove('hidden');

            const tbody = document.getElementById('usuariosBody');
            const usuarioActual = getUser();

            tbody.innerHTML = response.data.usuarios.map(usuario => `
                <tr>
                    <td><strong>${usuario.nombre_completo}</strong></td>
                    <td>${usuario.usuario}</td>
                    <td><span class="badge ${usuario.rol === 'admin' ? 'badge-entregado' : 'badge-pendiente'}">
                        ${usuario.rol === 'admin' ? 'ADMINISTRADOR' : 'VENDEDOR'}
                    </span></td>
                    <td>${usuario.ultimo_acceso || 'Nunca'}</td>
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
                        ` : '<small style="color: var(--color-gris-oscuro);">(Usuario actual)</small>'}
                    </td>
                </tr>
            `).join('');

        } else {
            document.getElementById('noUsuarios').classList.remove('hidden');
        }

    } catch (error) {
        document.getElementById('loadingUsuarios').classList.add('hidden');
        document.getElementById('noUsuarios').classList.remove('hidden');
        console.error('Error al cargar usuarios:', error);
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
        const response = await fetchAPI(`/usuarios/${id}`);
        
        if (response.success) {
            const usuario = response.data.usuario;
            
            document.getElementById('usuarioId').value = usuario.id;
            document.getElementById('usuarioNombreCompleto').value = usuario.nombre_completo;
            document.getElementById('usuarioNombre').value = usuario.usuario;
            document.getElementById('usuarioRol').value = usuario.rol;
            
            // Ocultar campo de contraseña al editar
            document.getElementById('grupoPassword').style.display = 'none';
            document.getElementById('usuarioPassword').required = false;
            document.getElementById('usuarioPassword').value = '';
            
            document.getElementById('modalUsuario').style.display = 'block';
        } else {
            mostrarAlerta('Error al cargar usuario', 'error');
        }
        
    } catch (error) {
        mostrarAlerta('Error de conexión', 'error');
        console.error('Error al editar usuario:', error);
    }
}

async function guardarUsuario() {
    const id = document.getElementById('usuarioId').value;
    const nombreCompleto = document.getElementById('usuarioNombreCompleto').value.trim();
    const usuario = document.getElementById('usuarioNombre').value.trim();
    const password = document.getElementById('usuarioPassword').value;
    const rol = document.getElementById('usuarioRol').value;

    if (!nombreCompleto || !usuario || !rol) {
        mostrarAlerta('Complete todos los campos requeridos', 'error');
        return;
    }

    // Validar contraseña solo al crear
    if (!id && (!password || password.length < 6)) {
        mostrarAlerta('La contraseña debe tener al menos 6 caracteres', 'error');
        return;
    }

    const data = {
        nombre_completo: nombreCompleto,
        usuario: usuario,
        rol: rol
    };

    // Solo incluir password al crear
    if (!id) {
        data.password = password;
    }

    try {
        let response;
        
        if (id) {
            // Actualizar
            response = await fetchAPI(`/usuarios/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        } else {
            // Crear
            response = await fetchAPI('/usuarios', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        if (response.success) {
            mostrarAlerta(id ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente', 'success');
            cerrarModal('modalUsuario');
            cargarUsuarios();
        } else {
            mostrarAlerta(response.data.error || 'Error al guardar usuario', 'error');
        }

    } catch (error) {
        mostrarAlerta('Error de conexión', 'error');
        console.error('Error al guardar usuario:', error);
    }
}

async function toggleActivo(id, estadoActual) {
    const accion = estadoActual ? 'desactivar' : 'activar';
    
    if (!confirmar(`¿Está seguro de ${accion} este usuario?`)) return;

    try {
        const response = await fetchAPI(`/usuarios/${id}/toggle-activo`, {
            method: 'PATCH'
        });

        if (response.success) {
            mostrarAlerta(`Usuario ${accion}do exitosamente`, 'success');
            cargarUsuarios();
        } else {
            mostrarAlerta(response.data.error || 'Error al cambiar estado', 'error');
        }

    } catch (error) {
        mostrarAlerta('Error de conexión', 'error');
        console.error('Error al cambiar estado:', error);
    }
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}