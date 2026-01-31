// API URL
const API_URL = 'http://localhost:5000';

// Obtener token - CON VERIFICACIÓN EXHAUSTIVA
function getToken() {
    try {
        const token = localStorage.getItem('token');
        console.log('🔑 getToken:', token ? `Token existe (${token.length} chars)` : 'NO EXISTE');
        return token;
    } catch (error) {
        console.error('❌ Error al obtener token:', error);
        return null;
    }
}

// Obtener usuario
function getUser() {
    try {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    } catch (error) {
        console.error('❌ Error al obtener usuario:', error);
        return null;
    }
}

// Guardar autenticación - CON VERIFICACIÓN
function saveAuth(token, user) {
    try {
        console.log('💾 Guardando autenticación...');
        console.log('   Token length:', token ? token.length : 0);
        console.log('   Usuario:', user ? user.nombre_completo : 'null');
        
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        
        // VERIFICAR que se guardó
        const tokenGuardado = localStorage.getItem('token');
        const userGuardado = localStorage.getItem('user');
        
        console.log('✅ Verificación:');
        console.log('   Token guardado:', tokenGuardado ? 'SÍ' : 'NO');
        console.log('   User guardado:', userGuardado ? 'SÍ' : 'NO');
        
        if (!tokenGuardado || !userGuardado) {
            throw new Error('No se pudo guardar en localStorage');
        }
        
        return true;
    } catch (error) {
        console.error('❌ Error al guardar auth:', error);
        return false;
    }
}

// Limpiar autenticación
function clearAuth() {
    console.log('🗑️ Limpiando autenticación');
    try {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        console.log('✅ Auth limpiada');
    } catch (error) {
        console.error('❌ Error al limpiar auth:', error);
    }
}

// Verificar autenticación
function verificarAuth() {
    const token = getToken();
    const hasAuth = !!token;
    console.log('🔐 verificarAuth:', hasAuth);
    return hasAuth;
}

// Función para hacer peticiones fetch con manejo de errores
async function fetchAPI(endpoint, options = {}) {
    console.log(`📡 fetchAPI: ${endpoint}`);
    
    try {
        const baseURL = window.location.origin; // Usar el mismo origin
        const url = `${baseURL}${endpoint}`;
        
        console.log('   🌐 URL completa:', url);
        
        // Configuración por defecto
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include' // ✅ IMPORTANTE: Incluir cookies/sesiones
        };
        
        // Combinar opciones
        const fetchOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        console.log('   📤 Opciones:', fetchOptions);
        
        const response = await fetch(url, fetchOptions);
        
        console.log('   📥 Response status:', response.status);
        
        let data;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.log('   📄 Response text:', text);
            data = { error: text || 'Respuesta no válida del servidor' };
        }
        
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
    if (!user) {
        console.log('⚠️ No hay usuario para cargar info');
        return;
    }

    console.log('👤 Cargando info de usuario:', user.nombre_completo);

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
    window.location.href = '/login.html';
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