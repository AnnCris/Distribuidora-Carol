from flask import Blueprint, request, jsonify, session
from app.database import db
from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.models.devolucion import Devolucion
from app.utils.decorators import login_required

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/', methods=['GET'])
@login_required
def listar_clientes():
    """Listar todos los clientes"""
    try:
        # Parámetros de filtrado y búsqueda
        activo = request.args.get('activo')
        buscar = request.args.get('buscar', '').strip()
        zona = request.args.get('zona')
        ciudad = request.args.get('ciudad')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Cliente.query
        
        # Filtro por activo
        if activo is not None:
            query = query.filter_by(activo=activo.lower() == 'true')
        
        # Filtro por zona
        if zona:
            query = query.filter_by(zona=zona)
        
        # Filtro por ciudad
        if ciudad:
            query = query.filter_by(ciudad=ciudad)
        
        # Búsqueda por nombre, celular o dirección
        if buscar:
            query = query.filter(
                db.or_(
                    Cliente.nombre.ilike(f'%{buscar}%'),
                    Cliente.celular.ilike(f'%{buscar}%'),
                    Cliente.direccion.ilike(f'%{buscar}%')
                )
            )
        
        # Paginación
        clientes_paginados = query.order_by(Cliente.nombre).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'clientes': [cliente.to_dict() for cliente in clientes_paginados.items],
            'total': clientes_paginados.total,
            'pagina_actual': page,
            'total_paginas': clientes_paginados.pages,
            'por_pagina': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar clientes: {str(e)}'}), 500


@clientes_bp.route('/todos', methods=['GET'])
@login_required
def listar_todos_clientes():
    """Listar todos los clientes activos sin paginación (para selectores)"""
    try:
        clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all()
        
        return jsonify({
            'clientes': [{'id': c.id, 'nombre': c.nombre, 'celular': c.celular} for c in clientes],
            'total': len(clientes)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar clientes: {str(e)}'}), 500


@clientes_bp.route('/<int:id>', methods=['GET'])
@login_required
def obtener_cliente(id):
    """Obtener un cliente por ID con sus estadísticas"""
    try:
        cliente = Cliente.query.get(id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        # Obtener estadísticas
        total_pedidos = Pedido.query.filter_by(cliente_id=id).count()
        total_devoluciones = Devolucion.query.filter_by(cliente_id=id).count()
        
        # Calcular total vendido
        pedidos = Pedido.query.filter_by(cliente_id=id, estado='entregado').all()
        total_vendido = sum(float(p.total) for p in pedidos)
        
        # Último pedido
        ultimo_pedido = Pedido.query.filter_by(cliente_id=id).order_by(Pedido.fecha_pedido.desc()).first()
        
        return jsonify({
            'cliente': cliente.to_dict(),
            'estadisticas': {
                'total_pedidos': total_pedidos,
                'total_devoluciones': total_devoluciones,
                'total_vendido': total_vendido,
                'ultimo_pedido': ultimo_pedido.to_dict() if ultimo_pedido else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener cliente: {str(e)}'}), 500


@clientes_bp.route('/', methods=['POST'])
@login_required
def crear_cliente():
    """Crear un nuevo cliente"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nombre'):
            return jsonify({'error': 'El nombre es requerido'}), 400
        
        # Validar celular si se proporciona
        if data.get('celular'):
            import re
            if not re.match(r'^[67]\d{7}$', data['celular']):
                return jsonify({
                    'error': 'Formato de celular inválido',
                    'mensaje': 'El celular debe tener 8 dígitos y empezar con 6 o 7'
                }), 400
        
        # Verificar si ya existe un cliente con el mismo nombre
        cliente_existente = Cliente.query.filter(
            Cliente.nombre.ilike(data['nombre'])
        ).first()
        
        if cliente_existente:
            return jsonify({
                'error': 'Ya existe un cliente con ese nombre',
                'cliente_existente': cliente_existente.to_dict()
            }), 400
        
        # Crear cliente
        nuevo_cliente = Cliente(
            nombre=data['nombre'],
            celular=data.get('celular'),
            direccion=data.get('direccion'),
            zona=data.get('zona'),
            ciudad=data.get('ciudad', 'La Paz')
        )
        
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Cliente creado exitosamente',
            'cliente': nuevo_cliente.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear cliente: {str(e)}'}), 500


@clientes_bp.route('/<int:id>', methods=['PUT'])
@login_required
def actualizar_cliente(id):
    """Actualizar un cliente"""
    try:
        cliente = Cliente.query.get(id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        data = request.get_json()
        
        # Validar nombre único si se actualiza
        if 'nombre' in data and data['nombre'] != cliente.nombre:
            cliente_existente = Cliente.query.filter(
                Cliente.nombre.ilike(data['nombre']),
                Cliente.id != id
            ).first()
            
            if cliente_existente:
                return jsonify({'error': 'Ya existe un cliente con ese nombre'}), 400
            
            cliente.nombre = data['nombre']
        
        # Validar celular si se actualiza
        if 'celular' in data:
            if data['celular']:
                import re
                if not re.match(r'^[67]\d{7}$', data['celular']):
                    return jsonify({
                        'error': 'Formato de celular inválido',
                        'mensaje': 'El celular debe tener 8 dígitos y empezar con 6 o 7'
                    }), 400
            cliente.celular = data['celular']
        
        # Actualizar otros campos
        if 'direccion' in data:
            cliente.direccion = data['direccion']
        
        if 'zona' in data:
            cliente.zona = data['zona']
        
        if 'ciudad' in data:
            cliente.ciudad = data['ciudad']
        
        if 'activo' in data:
            cliente.activo = data['activo']
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Cliente actualizado exitosamente',
            'cliente': cliente.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar cliente: {str(e)}'}), 500


@clientes_bp.route('/<int:id>/toggle-activo', methods=['PATCH'])
@login_required
def toggle_activo_cliente(id):
    """Activar/Desactivar un cliente"""
    try:
        cliente = Cliente.query.get(id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        cliente.activo = not cliente.activo
        db.session.commit()
        
        estado = 'activado' if cliente.activo else 'desactivado'
        
        return jsonify({
            'mensaje': f'Cliente {estado} exitosamente',
            'cliente': cliente.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500


@clientes_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def eliminar_cliente(id):
    """Eliminar un cliente"""
    try:
        cliente = Cliente.query.get(id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        # Verificar si tiene pedidos o devoluciones
        if len(cliente.pedidos) > 0 or len(cliente.devoluciones) > 0:
            return jsonify({
                'error': 'No se puede eliminar el cliente porque tiene pedidos o devoluciones registradas',
                'sugerencia': 'Considere desactivar el cliente en lugar de eliminarlo',
                'pedidos': len(cliente.pedidos),
                'devoluciones': len(cliente.devoluciones)
            }), 400
        
        db.session.delete(cliente)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Cliente eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar cliente: {str(e)}'}), 500


@clientes_bp.route('/<int:id>/historial-pedidos', methods=['GET'])
@login_required
def historial_pedidos_cliente(id):
    """Obtener historial de pedidos de un cliente"""
    try:
        cliente = Cliente.query.get(id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        # Parámetros de filtrado
        estado = request.args.get('estado')
        limite = request.args.get('limite', 10, type=int)
        
        query = Pedido.query.filter_by(cliente_id=id)
        
        if estado:
            query = query.filter_by(estado=estado)
        
        pedidos = query.order_by(Pedido.fecha_pedido.desc()).limit(limite).all()
        
        return jsonify({
            'cliente': cliente.to_dict(),
            'pedidos': [pedido.to_dict() for pedido in pedidos],
            'total': len(pedidos)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener historial: {str(e)}'}), 500


@clientes_bp.route('/<int:id>/historial-devoluciones', methods=['GET'])
@login_required
def historial_devoluciones_cliente(id):
    """Obtener historial de devoluciones de un cliente"""
    try:
        cliente = Cliente.query.get(id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        # Parámetros de filtrado
        estado = request.args.get('estado')
        limite = request.args.get('limite', 10, type=int)
        
        query = Devolucion.query.filter_by(cliente_id=id)
        
        if estado:
            query = query.filter_by(estado=estado)
        
        devoluciones = query.order_by(Devolucion.fecha_devolucion.desc()).limit(limite).all()
        
        return jsonify({
            'cliente': cliente.to_dict(),
            'devoluciones': [dev.to_dict(include_detalles=True) for dev in devoluciones],
            'total': len(devoluciones)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener historial: {str(e)}'}), 500


@clientes_bp.route('/zonas', methods=['GET'])
@login_required
def listar_zonas():
    """Listar todas las zonas registradas"""
    try:
        zonas = db.session.query(Cliente.zona).filter(
            Cliente.zona.isnot(None),
            Cliente.zona != ''
        ).distinct().order_by(Cliente.zona).all()
        
        return jsonify({
            'zonas': [z[0] for z in zonas]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar zonas: {str(e)}'}), 500


@clientes_bp.route('/ciudades', methods=['GET'])
@login_required
def listar_ciudades():
    """Listar todas las ciudades registradas"""
    try:
        ciudades = db.session.query(Cliente.ciudad).filter(
            Cliente.ciudad.isnot(None),
            Cliente.ciudad != ''
        ).distinct().order_by(Cliente.ciudad).all()
        
        return jsonify({
            'ciudades': [c[0] for c in ciudades]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar ciudades: {str(e)}'}), 500
    

@clientes_bp.route('/estadisticas', methods=['GET'])
@login_required
def estadisticas_clientes():
    """Obtener estadísticas de clientes"""
    try:
        total_clientes = Cliente.query.count()
        clientes_activos = Cliente.query.filter_by(activo=True).count()
        clientes_inactivos = Cliente.query.filter_by(activo=False).count()
        
        return jsonify({
            'total_clientes': total_clientes,
            'activos': clientes_activos,
            'inactivos': clientes_inactivos
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500