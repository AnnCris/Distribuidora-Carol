from flask import Blueprint, request, jsonify, session
from app.database import db
from app.models.producto import Producto
from app.models.pedido import DetallePedido
from app.utils.decorators import login_required

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/', methods=['GET'])
@login_required
def listar_productos():
    """Listar todos los productos"""
    try:
        # Parámetros de filtrado y búsqueda
        activo = request.args.get('activo')
        buscar = request.args.get('buscar', '').strip()
        stock_bajo = request.args.get('stock_bajo')
        unidad_medida = request.args.get('unidad_medida')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Producto.query
        
        # Filtro por activo
        if activo is not None:
            query = query.filter_by(activo=activo.lower() == 'true')
        
        # Filtro por unidad de medida
        if unidad_medida:
            query = query.filter_by(unidad_medida=unidad_medida)
        
        # Filtro por stock bajo
        if stock_bajo and stock_bajo.lower() == 'true':
            query = query.filter(Producto.stock_actual <= Producto.stock_minimo)
        
        # Búsqueda por código, nombre o descripción
        if buscar:
            query = query.filter(
                db.or_(
                    Producto.codigo.ilike(f'%{buscar}%'),
                    Producto.nombre.ilike(f'%{buscar}%'),
                    Producto.descripcion.ilike(f'%{buscar}%')
                )
            )
        
        # Paginación
        productos_paginados = query.order_by(Producto.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'productos': [producto.to_dict() for producto in productos_paginados.items],
            'total': productos_paginados.total,
            'pagina_actual': page,
            'total_paginas': productos_paginados.pages,
            'por_pagina': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar productos: {str(e)}'}), 500


@productos_bp.route('/todos', methods=['GET'])
@login_required
def listar_todos_productos():
    """Listar todos los productos activos sin paginación (para selectores)"""
    try:
        productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
        
        return jsonify({
            'productos': [{
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'precio_venta': float(p.precio_venta),
                'unidad_medida': p.unidad_medida,
                'stock_actual': p.stock_actual
            } for p in productos],
            'total': len(productos)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar productos: {str(e)}'}), 500


@productos_bp.route('/<int:id>', methods=['GET'])
@login_required
def obtener_producto(id):
    """Obtener un producto por ID"""
    try:
        producto = Producto.query.get(id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Obtener estadísticas de ventas
        ventas = db.session.query(
            db.func.sum(DetallePedido.cantidad).label('total_vendido'),
            db.func.count(DetallePedido.id).label('veces_vendido')
        ).filter(DetallePedido.producto_id == id).first()
        
        return jsonify({
            'producto': producto.to_dict(),
            'estadisticas': {
                'total_vendido': float(ventas.total_vendido) if ventas.total_vendido else 0,
                'veces_vendido': ventas.veces_vendido if ventas.veces_vendido else 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener producto: {str(e)}'}), 500


@productos_bp.route('/', methods=['POST'])
@login_required
def crear_producto():
    """Crear un nuevo producto"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nombre') or not data.get('precio_venta'):
            return jsonify({'error': 'Nombre y precio son requeridos'}), 400
        
        # Validar precio
        try:
            precio = float(data['precio_venta'])
            if precio <= 0:
                return jsonify({'error': 'El precio debe ser mayor a 0'}), 400
        except:
            return jsonify({'error': 'Precio inválido'}), 400
        
        # Validar código único si se proporciona
        if data.get('codigo'):
            codigo_existente = Producto.query.filter_by(codigo=data['codigo']).first()
            if codigo_existente:
                return jsonify({'error': 'El código de producto ya existe'}), 400
        
        # Validar nombre único
        nombre_existente = Producto.query.filter(
            Producto.nombre.ilike(data['nombre'])
        ).first()
        if nombre_existente:
            return jsonify({
                'error': 'Ya existe un producto con ese nombre',
                'producto_existente': nombre_existente.to_dict()
            }), 400
        
        # Validar unidad de medida
        unidades_validas = ['unidad', 'kg', 'caja', 'paquete', 'litro']
        unidad = data.get('unidad_medida', 'unidad')
        if unidad not in unidades_validas:
            return jsonify({
                'error': 'Unidad de medida inválida',
                'unidades_validas': unidades_validas
            }), 400
        
        # Crear producto
        nuevo_producto = Producto(
            codigo=data.get('codigo'),
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            unidad_medida=unidad,
            precio_venta=data['precio_venta'],
            stock_actual=data.get('stock_actual', 0),
            stock_minimo=data.get('stock_minimo', 5)
        )
        
        db.session.add(nuevo_producto)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Producto creado exitosamente',
            'producto': nuevo_producto.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear producto: {str(e)}'}), 500


@productos_bp.route('/<int:id>', methods=['PUT'])
@login_required
def actualizar_producto(id):
    """Actualizar un producto"""
    try:
        producto = Producto.query.get(id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        data = request.get_json()
        
        # Validar código único si se actualiza
        if 'codigo' in data and data['codigo'] != producto.codigo:
            codigo_existente = Producto.query.filter(
                Producto.codigo == data['codigo'],
                Producto.id != id
            ).first()
            
            if codigo_existente:
                return jsonify({'error': 'El código de producto ya existe'}), 400
            
            producto.codigo = data['codigo']
        
        # Validar nombre único si se actualiza
        if 'nombre' in data and data['nombre'] != producto.nombre:
            nombre_existente = Producto.query.filter(
                Producto.nombre.ilike(data['nombre']),
                Producto.id != id
            ).first()
            
            if nombre_existente:
                return jsonify({'error': 'Ya existe un producto con ese nombre'}), 400
            
            producto.nombre = data['nombre']
        
        # Validar precio si se actualiza
        if 'precio_venta' in data:
            try:
                precio = float(data['precio_venta'])
                if precio <= 0:
                    return jsonify({'error': 'El precio debe ser mayor a 0'}), 400
                producto.precio_venta = precio
            except:
                return jsonify({'error': 'Precio inválido'}), 400
        
        # Validar unidad de medida si se actualiza
        if 'unidad_medida' in data:
            unidades_validas = ['unidad', 'kg', 'caja', 'paquete', 'litro']
            if data['unidad_medida'] not in unidades_validas:
                return jsonify({
                    'error': 'Unidad de medida inválida',
                    'unidades_validas': unidades_validas
                }), 400
            producto.unidad_medida = data['unidad_medida']
        
        # Actualizar otros campos
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        
        if 'stock_minimo' in data:
            producto.stock_minimo = data['stock_minimo']
        
        if 'activo' in data:
            producto.activo = data['activo']
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Producto actualizado exitosamente',
            'producto': producto.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar producto: {str(e)}'}), 500


@productos_bp.route('/<int:id>/ajustar-stock', methods=['PATCH'])
@login_required
def ajustar_stock(id):
    """Ajustar stock de un producto (sumar o restar)"""
    try:
        producto = Producto.query.get(id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('cantidad') or not data.get('operacion'):
            return jsonify({'error': 'Cantidad y operación son requeridas'}), 400
        
        try:
            cantidad = int(data['cantidad'])
            if cantidad <= 0:
                return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        except:
            return jsonify({'error': 'Cantidad inválida'}), 400
        
        operacion = data['operacion']
        
        # Validar operación
        if operacion not in ['sumar', 'restar']:
            return jsonify({'error': 'Operación inválida. Use "sumar" o "restar"'}), 400
        
        # Ajustar stock
        stock_anterior = producto.stock_actual
        
        if operacion == 'sumar':
            producto.stock_actual += cantidad
        else:  # restar
            if producto.stock_actual < cantidad:
                return jsonify({
                    'error': 'Stock insuficiente',
                    'stock_actual': producto.stock_actual,
                    'cantidad_solicitada': cantidad
                }), 400
            producto.stock_actual -= cantidad
        
        db.session.commit()
        
        return jsonify({
            'mensaje': f'Stock {operacion}do exitosamente',
            'producto': producto.to_dict(),
            'stock_anterior': stock_anterior,
            'stock_nuevo': producto.stock_actual,
            'diferencia': cantidad
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al ajustar stock: {str(e)}'}), 500


@productos_bp.route('/<int:id>/toggle-activo', methods=['PATCH'])
@login_required
def toggle_activo_producto(id):
    """Activar/Desactivar un producto"""
    try:
        producto = Producto.query.get(id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        producto.activo = not producto.activo
        db.session.commit()
        
        estado = 'activado' if producto.activo else 'desactivado'
        
        return jsonify({
            'mensaje': f'Producto {estado} exitosamente',
            'producto': producto.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500


@productos_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def eliminar_producto(id):
    """Eliminar un producto"""
    try:
        producto = Producto.query.get(id)
        
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Verificar si tiene detalles de pedidos
        if len(producto.detalle_pedidos) > 0:
            return jsonify({
                'error': 'No se puede eliminar el producto porque está en pedidos registrados',
                'sugerencia': 'Considere desactivar el producto en lugar de eliminarlo',
                'pedidos_relacionados': len(producto.detalle_pedidos)
            }), 400
        
        db.session.delete(producto)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Producto eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar producto: {str(e)}'}), 500


@productos_bp.route('/stock-bajo', methods=['GET'])
@login_required
def productos_stock_bajo():
    """Listar productos con stock bajo o agotado"""
    try:
        productos_bajo = Producto.query.filter(
            Producto.activo == True,
            Producto.stock_actual <= Producto.stock_minimo
        ).order_by(Producto.stock_actual).all()
        
        return jsonify({
            'productos': [{
                **p.to_dict(),
                'estado_stock': 'agotado' if p.stock_actual == 0 else 'bajo'
            } for p in productos_bajo],
            'total': len(productos_bajo)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener productos con stock bajo: {str(e)}'}), 500


@productos_bp.route('/unidades-medida', methods=['GET'])
@login_required
def listar_unidades_medida():
    """Listar unidades de medida disponibles"""
    try:
        unidades = ['unidad', 'kg', 'caja', 'paquete', 'litro']
        
        return jsonify({
            'unidades_medida': unidades
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar unidades: {str(e)}'}), 500


@productos_bp.route('/mas-vendidos', methods=['GET'])
@login_required
def productos_mas_vendidos():
    """Listar los productos más vendidos"""
    try:
        limite = request.args.get('limite', 10, type=int)
        
        productos_vendidos = db.session.query(
            Producto,
            db.func.sum(DetallePedido.cantidad).label('total_vendido')
        ).join(
            DetallePedido, Producto.id == DetallePedido.producto_id
        ).group_by(
            Producto.id
        ).order_by(
            db.desc('total_vendido')
        ).limit(limite).all()
        
        return jsonify({
            'productos': [{
                **producto.to_dict(),
                'total_vendido': float(total)
            } for producto, total in productos_vendidos],
            'total': len(productos_vendidos)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener productos más vendidos: {str(e)}'}), 500
    

@productos_bp.route('/estadisticas', methods=['GET'])
@login_required
def estadisticas_productos():
    """Obtener estadísticas de productos"""
    try:
        total_productos = Producto.query.count()
        productos_activos = Producto.query.filter_by(activo=True).count()
        productos_stock_bajo = Producto.query.filter(
            Producto.stock_actual <= Producto.stock_minimo
        ).count()
        
        return jsonify({
            'total_productos': total_productos,
            'activos': productos_activos,
            'stock_bajo': productos_stock_bajo
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500