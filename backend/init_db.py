from app import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.producto import Producto
from app.models.pedido import Pedido, DetallePedido
from app.models.devolucion import Devolucion, DetalleDevolucion

def init_database():
    """Inicializar base de datos y crear usuario admin por defecto"""
    
    app = create_app()
    
    with app.app_context():
        # Eliminar todas las tablas existentes (¡CUIDADO EN PRODUCCIÓN!)
        print("🗑️  Eliminando tablas existentes...")
        db.drop_all()
        
        # Crear todas las tablas
        print("📋 Creando tablas...")
        db.create_all()
        
        # Verificar si ya existe el usuario admin
        admin_existente = Usuario.query.filter_by(usuario='admin').first()
        
        if not admin_existente:
            # Crear usuario admin por defecto
            print("👤 Creando usuario administrador...")
            admin = Usuario(
                nombre_completo='Administrador',
                usuario='admin',
                rol='admin'
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuario admin creado exitosamente")
            print("   Usuario: admin")
            print("   Contraseña: admin123")
        else:
            print("✅ Usuario admin ya existe")
        
        print("\n✅ Base de datos inicializada correctamente!")
        print("📊 Tablas creadas:")
        print("   - usuarios")
        print("   - clientes")
        print("   - productos")
        print("   - pedidos")
        print("   - detalle_pedidos")
        print("   - devoluciones")
        print("   - detalle_devoluciones")

if __name__ == '__main__':
    init_database()