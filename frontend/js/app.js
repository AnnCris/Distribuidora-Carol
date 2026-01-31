// API URL
const API_URL = 'http://localhost:5000';

// Obtener token
function getToken() {
    const token = localStorage.getItem('token');
    console.log('🔑 getToken llamado, token:', token ? 'EXISTE' : 'NO EXISTE');
    return token;
}

// Obtener usuario
function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

// Guardar autenticación
function saveAuth(token, user) {
    console.log('💾 Guardando token y usuario');
    console.log('Token a guardar:', token ? token.substring(0, 20) + '...' : 'VACIO');
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    console.log('✅ Token guardado. Verificando...');
    console.log('Token en localStorage:', localStorage.getItem('token') ? 'EXISTE' : 'NO EXISTE');
}

// Limpiar autenticación
function clearAuth() {
    console.log('🗑️ Limpiando autenticación');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

// Verificar autenticación
function verificarAuth() {
    const hasToken = !!getToken();
    console.log('🔐 verificarAuth:', hasToken);
    return hasToken;
}

// Fetch con autenticación
async function fetchAPI(endpoint, options = {}) {
    const token = getToken();
    
    if (!endpoint.startsWith('/api')) {
        endpoint = '/api' + endpoint;
    }
    
    console.log('📡 fetchAPI:', endpoint);
    console.log('   Token disponible:', token ? 'SÍ' : 'NO');
    
    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        }
    };

    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
        console.log('   ✅ Header Authorization agregado');
    } else {
        console.log('   ❌ NO se agregó header Authorization');
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, config);
        
        console.log('   📥 Response:', response.status);
        
        // Si es 401 Y NO es la ruta de login, redirigir
        if (response.status === 401 && !endpoint.includes('/auth/login')) {
            console.error('❌ 401 NO AUTORIZADO - Redirigiendo a login');
            clearAuth();
            window.location.href = 'login.html';
            return { success: false, status: 401, data: { error: 'No autorizado' } };
        }

        const data = await response.json();

        return {
            success: response.ok,
            status: response.status,
            data: data
        };

    } catch (error) {
        console.error('❌ Error en fetchAPI:', error);
        return {
            success: false,
            status: 0,
            data: { error: 'Error de conexión' }
        };
    }
}

// Mostrar alerta
function mostrarAlerta(mensaje, tipo = 'error', elementId = 'alert') {
    const alert = document.getElementById(elementId);
    if (!alert) return;

    alert.className = `alert alert-${tipo}`;
    alert.textContent = mensaje;
    alert.style.display = 'block';

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Formatear precio
function formatearPrecio(precio) {
    return parseFloat(precio).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Formatear fecha
function formatearFecha(fecha) {
    if (!fecha) return '';
    const date = new Date(fecha);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

// Formatear fecha y hora
function formatearFechaHora(fecha) {
    if (!fecha) return '';
    const date = new Date(fecha);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// Cargar info usuario
function cargarInfoUsuario() {
    const user = getUser();
    if (!user) return;

    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.textContent = user.nombre_completo;
    }

    const userRoleElement = document.getElementById('userRole');
    if (userRoleElement) {
        userRoleElement.textContent = user.rol === 'admin' ? 'Administrador' : 'Vendedor';
    }

    const userAvatarElement = document.getElementById('userAvatar');
    if (userAvatarElement) {
        userAvatarElement.textContent = user.nombre_completo.charAt(0).toUpperCase();
    }

    if (user.rol !== 'admin') {
        const menuUsuarios = document.getElementById('menuUsuarios');
        if (menuUsuarios) {
            menuUsuarios.style.display = 'none';
        }
    }
}

// Logout
function logout() {
    clearAuth();
    window.location.href = 'login.html';
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            if (confirm('¿Está seguro que desea cerrar sesión?')) {
                logout();
            }
        });
    }
});

// Debounce
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

// Confirmar
function confirmar(mensaje) {
    return confirm(mensaje);
}
