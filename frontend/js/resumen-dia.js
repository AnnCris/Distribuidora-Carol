let resumenData = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!verificarAuth()) {
        window.location.href = 'login.html';
        return;
    }

    cargarInfoUsuario();
    
    // Establecer fecha de hoy
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('fechaResumen').value = hoy;
    
    await cargarResumen();

    // Menu toggle
    document.getElementById('menuToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('active');
    });
});

async function cargarResumen() {
    const fecha = document.getElementById('fechaResumen').value;
    
    if (!fecha) {
        mostrarAlerta('Seleccione una fecha', 'error');
        return;
    }

    try {
        document.getElementById('loadingResumen').classList.remove('hidden');
        document.getElementById('contenidoResumen').classList.add('hidden');
        document.getElementById('noResumen').classList.add('hidden');

        const response = await fetchAPI(`/pedidos/resumen-dia?fecha=${fecha}`);

        document.getElementById('loadingResumen').classList.add('hidden');

        if (response.success) {
            resumenData = response.data;
            
            // Actualizar tarjetas
            document.getElementById('totalPedidos').textContent = resumenData.total_pedidos;
            document.getElementById('totalClientes').textContent = resumenData.total_clientes;
            document.getElementById('totalGeneral').textContent = `Bs. ${formatearPrecio(resumenData.total_general)}`;
            
            // Actualizar fecha seleccionada
            document.getElementById('fechaSeleccionada').textContent = `Fecha: ${resumenData.fecha}`;

            if (resumenData.resumen.length > 0) {
                mostrarResumen();
            } else {
                document.getElementById('noResumen').classList.remove('hidden');
            }

        } else {
            document.getElementById('noResumen').classList.remove('hidden');
            mostrarAlerta('Error al cargar resumen', 'error');
        }

    } catch (error) {
        document.getElementById('loadingResumen').classList.add('hidden');
        document.getElementById('noResumen').classList.remove('hidden');
        mostrarAlerta('Error de conexión', 'error');
        console.error('Error al cargar resumen:', error);
    }
}

function mostrarResumen() {
    const contenedor = document.getElementById('contenidoResumen');
    contenedor.classList.remove('hidden');

    let html = '';

    resumenData.resumen.forEach((cliente, index) => {
        html += `
            <div style="background: ${index % 2 === 0 ? 'var(--color-blanco)' : 'var(--color-gris)'}; 
                        padding: 20px; 
                        border-radius: var(--border-radius-small); 
                        margin-bottom: 15px;
                        border-left: 4px solid var(--color-celeste);">
                
                <h3 style="color: var(--color-celeste); margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <span>📦 CLIENTE: ${cliente.cliente_nombre.toUpperCase()}</span>
                    <span style="font-size: 16px; color: var(--color-exito);">Bs. ${formatearPrecio(cliente.total)}</span>
                </h3>
                
                <div style="margin-left: 20px;">
                    ${cliente.productos.map(prod => `
                        <p style="margin: 5px 0; font-size: 15px;">
                            • <strong>${prod.nombre}</strong> × ${formatearCantidad(prod.cantidad)} ${prod.unidad_medida}
                        </p>
                    `).join('')}
                </div>
            </div>
        `;
    });

    contenedor.innerHTML = html;
}

function formatearCantidad(cantidad) {
    const num = parseFloat(cantidad);
    if (num === parseInt(num)) {
        return parseInt(num);
    }
    return num.toFixed(2);
}

function cargarHoy() {
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('fechaResumen').value = hoy;
    cargarResumen();
}

function descargarPDFResumen() {
    const fecha = document.getElementById('fechaResumen').value;
    
    if (!fecha) {
        mostrarAlerta('Seleccione una fecha primero', 'error');
        return;
    }

    if (!resumenData || resumenData.total_pedidos === 0) {
        mostrarAlerta('No hay datos para descargar', 'error');
        return;
    }

    window.open(`${API_URL}/pedidos/resumen-dia/pdf?fecha=${fecha}`, '_blank');
}