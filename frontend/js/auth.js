document.addEventListener('DOMContentLoaded', () => {
    // Si ya está autenticado, ir al dashboard
    if (verificarAuth()) {
        window.location.href = 'dashboard.html';
        return;
    }

    const loginForm = document.getElementById('loginForm');
    const btnLogin = document.getElementById('btnLogin');
    const loading = document.getElementById('loading');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const usuario = document.getElementById('usuario').value.trim();
        const password = document.getElementById('password').value;

        if (!usuario || !password) {
            mostrarAlerta('Complete todos los campos', 'error');
            return;
        }

        btnLogin.disabled = true;
        loginForm.style.display = 'none';
        loading.classList.remove('hidden');

        try {
            const response = await fetchAPI('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ usuario, password })
            });

            if (response.success) {
                console.log('💾 Guardando token y usuario');
                
                // GUARDAR PRIMERO
                saveAuth(response.data.token, response.data.usuario);
                
                // VERIFICAR QUE SE GUARDÓ
                const tokenGuardado = localStorage.getItem('token');
                console.log('✅ Token guardado. Verificando...', tokenGuardado ? 'EXISTE' : 'NO EXISTE');
                
                if (!tokenGuardado) {
                    throw new Error('No se pudo guardar el token');
                }
                
                mostrarAlerta('Inicio de sesión exitoso', 'success');
                
                // ESPERAR 100ms ANTES de redirigir para asegurar que localStorage se sincronizó
                await new Promise(resolve => setTimeout(resolve, 100));
                
                // REDIRIGIR
                window.location.href = 'dashboard.html';

            } else {
                loginForm.style.display = 'block';
                loading.classList.add('hidden');
                btnLogin.disabled = false;
                mostrarAlerta(response.data.error || 'Error al iniciar sesión', 'error');
            }

        } catch (error) {
            loginForm.style.display = 'block';
            loading.classList.add('hidden');
            btnLogin.disabled = false;
            mostrarAlerta('Error de conexión', 'error');
            console.error('Error:', error);
        }
    });
});