# -*- coding: utf-8 -*-
import sys
from app import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.producto import Producto
from sqlalchemy import text

def init_database():
    """Inicializar la base de datos con datos de ejemplo"""
    app = create_app()
    
    with app.app_context():
        print("Eliminando base de datos existente...")
        
        # Eliminar todas las tablas con CASCADE
        db.session.execute(text('DROP SCHEMA public CASCADE'))
        db.session.execute(text('CREATE SCHEMA public'))
        db.session.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
        db.session.execute(text('GRANT ALL ON SCHEMA public TO public'))
        db.session.commit()
        
        print("Creando tablas...")
        db.create_all()
        
        print("Creando usuario administrador...")
        admin = Usuario(
            nombre='Administrador',
            email='admin@carolina.com',
            rol='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        print("Creando usuario vendedor...")
        vendedor = Usuario(
            nombre='Ana Perez',
            email='ana@carolina.com',
            rol='vendedor'
        )
        vendedor.set_password('vendedor123')
        db.session.add(vendedor)
        
        print("Creando clientes de ejemplo...")
        clientes = [
            Cliente(
                nombre='Tienda Don Jose',
                celular='72345678',
                zona='Zona Sur',
                ciudad='La Paz'
            ),
            Cliente(
                nombre='Minimarket El Dorado',
                celular='71234567',
                zona='Miraflores',
                ciudad='La Paz'
            ),
            Cliente(
                nombre='Bodega San Miguel',
                celular='73456789',
                zona='Villa Victoria',
                ciudad='La Paz'
            ),
            Cliente(
                nombre='Supermercado Central',
                celular='74567890',
                zona='Centro',
                ciudad='El Alto'
            ),
            Cliente(
                nombre='Tienda La Estrella',
                celular='75678901',
                zona='Ceja',
                ciudad='El Alto'
            )
        ]
        
        for cliente in clientes:
            db.session.add(cliente)
        
        print("Creando productos de ejemplo...")
        productos = [
            Producto(
                codigo='QUESO-001',
                nombre='Queso Mozzarella 500g',
                descripcion='Queso mozzarella fresco de alta calidad',
                precio_venta=25.00,
                stock_actual=100,
                stock_minimo=20,
                unidad_medida='unidad'
            ),
            Producto(
                codigo='QUESO-002',
                nombre='Queso Gouda 1kg',
                descripcion='Queso gouda semicurado',
                precio_venta=55.00,
                stock_actual=80,
                stock_minimo=15,
                unidad_medida='kg'
            ),
            Producto(
                codigo='QUESO-003',
                nombre='Queso Paria 500g',
                descripcion='Queso paria tradicional boliviano',
                precio_venta=20.00,
                stock_actual=150,
                stock_minimo=30,
                unidad_medida='unidad'
            ),
            Producto(
                codigo='QUESO-004',
                nombre='Queso Crema 200g',
                descripcion='Queso crema para untar',
                precio_venta=15.00,
                stock_actual=120,
                stock_minimo=25,
                unidad_medida='unidad'
            ),
            Producto(
                codigo='QUESO-005',
                nombre='Queso Parmesano Rallado 100g',
                descripcion='Queso parmesano rallado',
                precio_venta=18.00,
                stock_actual=90,
                stock_minimo=20,
                unidad_medida='paquete'
            ),
            Producto(
                codigo='LACTEO-001',
                nombre='Leche Entera 1L',
                descripcion='Leche entera pasteurizada',
                precio_venta=7.00,
                stock_actual=200,
                stock_minimo=50,
                unidad_medida='litro'
            ),
            Producto(
                codigo='LACTEO-002',
                nombre='Yogurt Natural 1L',
                descripcion='Yogurt natural sin azucar',
                precio_venta=12.00,
                stock_actual=150,
                stock_minimo=30,
                unidad_medida='litro'
            ),
            Producto(
                codigo='LACTEO-003',
                nombre='Mantequilla 250g',
                descripcion='Mantequilla sin sal',
                precio_venta=16.00,
                stock_actual=100,
                stock_minimo=20,
                unidad_medida='unidad'
            ),
            Producto(
                codigo='QUESO-006',
                nombre='Queso Manchego 500g',
                descripcion='Queso manchego curado',
                precio_venta=45.00,
                stock_actual=50,
                stock_minimo=10,
                unidad_medida='unidad'
            ),
            Producto(
                codigo='QUESO-007',
                nombre='Queso Dambo 1kg',
                descripcion='Queso dambo argentino',
                precio_venta=50.00,
                stock_actual=60,
                stock_minimo=12,
                unidad_medida='kg'
            )
        ]
        
        for producto in productos:
            db.session.add(producto)
        
        print("Guardando cambios...")
        db.session.commit()
        
        print("\nBase de datos inicializada exitosamente!")
        print("\nCredenciales de acceso:")
        print("="*50)
        print("ADMINISTRADOR:")
        print("  Email: admin@carolina.com")
        print("  Password: admin123")
        print("\nVENDEDOR:")
        print("  Email: ana@carolina.com")
        print("  Password: vendedor123")
        print("="*50)
        print("\nDatos creados:")
        print("  - {} clientes".format(len(clientes)))
        print("  - {} productos".format(len(productos)))
        print("  - 2 usuarios")
        print("\nPuedes iniciar el servidor con: python run.py")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print("\nError al inicializar la base de datos: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)