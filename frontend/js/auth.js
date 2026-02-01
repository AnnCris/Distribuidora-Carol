console.log('🚀 auth.js cargado');

// Al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM cargado - Verificando auth...');
    
    // Verificar si estamos en login.html
    if (window.location.pathname.includes('login.html')) {
        console.log('📍 Estamos en login.html');
        initLogin();
    } else if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
        console.log('📍 Estamos en index (landing page)');
        // No hacer nada, el script en index.html maneja esto
    } else {
        console.log('📍 Verificando autenticación...');
        verificarAuth();
    }
});

// Inicializar página de login
function initLogin() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('📝 Formulario enviado');
            
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Iniciando sesión...';
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                console.log('👤 Intentando login:', email);
                
                // Llamar a la API de login
                const response = await fetchAPI('/api/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ email, password })
                });
                
                console.log('📥 Respuesta recibida:', response);
                
                if (response.success && response.data.usuario) {
                    console.log('✅ Login exitoso:', response.data.usuario);
                    
                    // Guardar información del usuario en sessionStorage
                    sessionStorage.setItem('usuario', JSON.stringify(response.data.usuario));
                    
                    mostrarMensaje('¡Bienvenido!', 'success');
                    
                    // Redirigir al dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard.html';
                    }, 500);
                } else {
                    console.log('❌ Login fallido:', response.data);
                    mostrarMensaje(response.data.error || 'Credenciales incorrectas', 'error');
                }
                
            } catch (error) {
                console.error('❌ Error en login:', error);
                mostrarMensaje('Error al iniciar sesión. Por favor intenta de nuevo.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
}

// Verificar autenticación
async function verificarAuth() {
    console.log('🔐 Verificando autenticación...');
    
    // Si estamos en login o index, no verificar
    const path = window.location.pathname;
    if (path.includes('login.html') || path.includes('index.html') || path === '/') {
        console.log('📍 En página pública, saltando verificación');
        return true;
    }
    
    try {
        const response = await fetchAPI('/api/auth/validar');
        
        console.log('📥 Validación recibida:', response);
        
        if (response.success && response.data.valido) {
            console.log('✅ Usuario autenticado:', response.data.usuario);
            sessionStorage.setItem('usuario', JSON.stringify(response.data.usuario));
            return true;
        } else {
            console.log('❌ No autenticado, redirigiendo a login...');
            sessionStorage.removeItem('usuario');
            
            // Evitar loop infinito
            if (!path.includes('login.html')) {
                window.location.href = '/login.html';
            }
            return false;
        }
    } catch (error) {
        console.error('❌ Error verificando auth:', error);
        sessionStorage.removeItem('usuario');
        
        // Evitar loop infinito
        if (!path.includes('login.html')) {
            window.location.href = '/login.html';
        }
        return false;
    }
}

// Cerrar sesión
async function logout() {
    console.log('🚪 Cerrando sesión...');
    
    try {
        await fetchAPI('/api/auth/logout', {
            method: 'POST'
        });
        
        sessionStorage.removeItem('usuario');
        window.location.href = '/login.html';
    } catch (error) {
        console.error('❌ Error en logout:', error);
        // Limpiar de todas formas
        sessionStorage.removeItem('usuario');
        window.location.href = '/login.html';
    }
}

// Obtener usuario actual
function getUsuario() {
    const usuarioStr = sessionStorage.getItem('usuario');
    return usuarioStr ? JSON.parse(usuarioStr) : null;
}

// Verificar si es admin
function esAdmin() {
    const usuario = getUsuario();
    return usuario && usuario.rol === 'admin';
}

// Mostrar mensaje
function mostrarMensaje(mensaje, tipo = 'info') {
    const existente = document.querySelector('.mensaje-temporal');
    if (existente) {
        existente.remove();
    }
    
    const div = document.createElement('div');
    div.className = `mensaje-temporal mensaje-${tipo}`;
    div.textContent = mensaje;
    
    const styles = {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 25px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        zIndex: '10000',
        fontSize: '14px',
        fontWeight: '500',
        maxWidth: '400px'
    };
    
    Object.assign(div.style, styles);
    
    if (tipo === 'success') {
        div.style.backgroundColor = '#10b981';
        div.style.color = 'white';
    } else if (tipo === 'error') {
        div.style.backgroundColor = '#ef4444';
        div.style.color = 'white';
    } else {
        div.style.backgroundColor = '#3b82f6';
        div.style.color = 'white';
    }
    
    document.body.appendChild(div);
    
    setTimeout(() => {
        div.remove();
    }, 3000);
}