from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime
from app.database import db, get_bolivia_time
from app.models.devolucion import Devolucion, DetalleDevolucion
from app.models.pedido import Pedido
from app.models.cliente import Cliente
from app.models.producto import Producto
from app.utils.decorators import login_required
from app.utils.pdf_generator import PDFGenerator

devoluciones_bp = Blueprint('devoluciones', __name__)

@devoluciones_bp.route('/', methods=['GET'])
@login_required
def listar_devoluciones():
    """Listar todas las devoluciones con filtros"""
    try:
        # Parámetros de filtrado
        cliente_id = request.args.get('cliente_id', type=int)
        estado = request.args.get('estado')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        motivo = request.args.get('motivo')
        buscar = request.args.get('buscar', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Devolucion.query
        
        # Filtro por cliente
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        
        # Filtro por estado
        if estado:
            query = query.filter_by(estado=estado)
        
        # Filtro por motivo
        if motivo:
            query = query.filter_by(motivo=motivo)
        
        # Filtro por rango de fechas
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.filter(Devolucion.fecha_devolucion >= fecha_desde_obj)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(Devolucion.fecha_devolucion <= fecha_hasta_obj)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400
        
        # Búsqueda por número de devolución o nombre de cliente
        if buscar:
            query = query.join(Cliente).filter(
                db.or_(
                    Devolucion.numero_devolucion.ilike(f'%{buscar}%'),
                    Cliente.nombre.ilike(f'%{buscar}%')
                )
            )
        
        # Paginación
        devoluciones_paginadas = query.order_by(Devolucion.fecha_devolucion.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'devoluciones': [devolucion.to_dict() for devolucion in devoluciones_paginadas.items],
            'total': devoluciones_paginadas.total,
            'pagina_actual': page,
            'total_paginas': devoluciones_paginadas.pages,
            'por_pagina': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar devoluciones: {str(e)}'}), 500


@devoluciones_bp.route('/pendientes', methods=['GET'])
@login_required
def listar_devoluciones_pendientes():
    """Listar devoluciones pendientes de compensación"""
    try:
        cliente_id = request.args.get('cliente_id', type=int)
        
        query = Devolucion.query.filter_by(estado='pendiente')
        
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        
        devoluciones = query.order_by(Devolucion.fecha_devolucion.desc()).all()
        
        return jsonify({
            'devoluciones': [dev.to_dict(include_detalles=True) for dev in devoluciones],
            'total': len(devoluciones)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar devoluciones pendientes: {str(e)}'}), 500


@devoluciones_bp.route('/<int:id>', methods=['GET'])
@login_required
def obtener_devolucion(id):
    """Obtener una devolución por ID con todos sus detalles"""
    try:
        devolucion = Devolucion.query.get(id)
        
        if not devolucion:
            return jsonify({'error': 'Devolución no encontrada'}), 404
        
        return jsonify({
            'devolucion': devolucion.to_dict(include_detalles=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener devolución: {str(e)}'}), 500


@devoluciones_bp.route('/', methods=['POST'])
@login_required
def crear_devolucion():
    """Crear una nueva devolución"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        if not data or not data.get('cliente_id') or not data.get('motivo') or not data.get('detalles'):
            return jsonify({'error': 'Cliente, motivo y detalles son requeridos'}), 400
        
        # Validar que el cliente existe
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        if not cliente.activo:
            return jsonify({'error': 'El cliente está desactivado'}), 400
        
        # Validar motivo
        motivos_validos = ['vencido', 'mal_estado', 'error_entrega', 'otro']
        if data['motivo'] not in motivos_validos:
            return jsonify({
                'error': 'Motivo inválido',
                'motivos_validos': motivos_validos
            }), 400
        
        # Validar que hay detalles
        if not data['detalles'] or len(data['detalles']) == 0:
            return jsonify({'error': 'Debe agregar al menos un producto a la devolución'}), 400
        
        # Si se proporciona pedido_id, validar que existe
        pedido_id = data.get('pedido_id')
        if pedido_id:
            pedido = Pedido.query.get(pedido_id)
            if not pedido:
                return jsonify({'error': 'Pedido no encontrado'}), 404
            
            if pedido.cliente_id != data['cliente_id']:
                return jsonify({'error': 'El pedido no pertenece a este cliente'}), 400
        
        # Generar número de devolución
        numero_devolucion = Devolucion.generar_numero_devolucion()
        
        # Crear devolución
        nueva_devolucion = Devolucion(
            numero_devolucion=numero_devolucion,
            pedido_id=pedido_id,
            cliente_id=data['cliente_id'],
            usuario_id=user_id,
            motivo=data['motivo'],
            descripcion_motivo=data.get('descripcion_motivo'),
            observaciones=data.get('observaciones')
        )
        
        db.session.add(nueva_devolucion)
        db.session.flush()
        
        # Agregar detalles
        for detalle_data in data['detalles']:
            # Validar producto
            producto = Producto.query.get(detalle_data['producto_id'])
            if not producto:
                db.session.rollback()
                return jsonify({'error': f'Producto con ID {detalle_data["producto_id"]} no encontrado'}), 404
            
            # Validar cantidad
            try:
                cantidad = float(detalle_data['cantidad'])
                if cantidad <= 0:
                    raise ValueError()
            except:
                db.session.rollback()
                return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
            
            # Validar producto de reemplazo si existe
            producto_reemplazo_id = detalle_data.get('producto_reemplazo_id')
            if producto_reemplazo_id:
                producto_reemplazo = Producto.query.get(producto_reemplazo_id)
                if not producto_reemplazo:
                    db.session.rollback()
                    return jsonify({'error': f'Producto de reemplazo con ID {producto_reemplazo_id} no encontrado'}), 404
                
                if not producto_reemplazo.activo:
                    db.session.rollback()
                    return jsonify({'error': f'El producto de reemplazo {producto_reemplazo.nombre} está desactivado'}), 400
            
            # Crear detalle
            detalle = DetalleDevolucion(
                devolucion_id=nueva_devolucion.id,
                producto_id=producto.id,
                cantidad=cantidad,
                producto_reemplazo_id=producto_reemplazo_id,
                observacion=detalle_data.get('observacion')
            )
            
            db.session.add(detalle)
            
            # Retornar producto al stock
            producto.actualizar_stock(int(cantidad), 'sumar')
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Devolución registrada exitosamente',
            'devolucion': nueva_devolucion.to_dict(include_detalles=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear devolución: {str(e)}'}), 500


@devoluciones_bp.route('/<int:id>', methods=['PUT'])
@login_required
def actualizar_devolucion(id):
    """Actualizar una devolución (solo si está pendiente)"""
    try:
        devolucion = Devolucion.query.get(id)
        
        if not devolucion:
            return jsonify({'error': 'Devolución no encontrada'}), 404
        
        if devolucion.estado != 'pendiente':
            return jsonify({'error': f'No se puede editar una devolución en estado "{devolucion.estado}"'}), 400
        
        data = request.get_json()
        
        # Actualizar campos básicos
        if 'motivo' in data:
            motivos_validos = ['vencido', 'mal_estado', 'error_entrega', 'otro']
            if data['motivo'] not in motivos_validos:
                return jsonify({
                    'error': 'Motivo inválido',
                    'motivos_validos': motivos_validos
                }), 400
            devolucion.motivo = data['motivo']
        
        if 'descripcion_motivo' in data:
            devolucion.descripcion_motivo = data['descripcion_motivo']
        
        if 'observaciones' in data:
            devolucion.observaciones = data['observaciones']
        
        # Si se actualizan los detalles
        if 'detalles' in data:
            # Restaurar stock de productos eliminados
            for detalle in devolucion.detalles:
                producto = Producto.query.get(detalle.producto_id)
                producto.actualizar_stock(int(detalle.cantidad), 'restar')
            
            # Eliminar detalles antiguos
            DetalleDevolucion.query.filter_by(devolucion_id=id).delete()
            
            # Agregar nuevos detalles
            for detalle_data in data['detalles']:
                producto = Producto.query.get(detalle_data['producto_id'])
                if not producto:
                    db.session.rollback()
                    return jsonify({'error': f'Producto con ID {detalle_data["producto_id"]} no encontrado'}), 404
                
                producto_reemplazo_id = detalle_data.get('producto_reemplazo_id')
                if producto_reemplazo_id:
                    producto_reemplazo = Producto.query.get(producto_reemplazo_id)
                    if not producto_reemplazo or not producto_reemplazo.activo:
                        db.session.rollback()
                        return jsonify({'error': 'Producto de reemplazo inválido'}), 400
                
                detalle = DetalleDevolucion(
                    devolucion_id=devolucion.id,
                    producto_id=producto.id,
                    cantidad=detalle_data['cantidad'],
                    producto_reemplazo_id=producto_reemplazo_id,
                    observacion=detalle_data.get('observacion')
                )
                db.session.add(detalle)
                
                # Retornar al stock
                producto.actualizar_stock(int(detalle_data['cantidad']), 'sumar')
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Devolución actualizada exitosamente',
            'devolucion': devolucion.to_dict(include_detalles=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar devolución: {str(e)}'}), 500


@devoluciones_bp.route('/<int:id>/marcar-compensado', methods=['PATCH'])
@login_required
def marcar_compensado(id):
    """Marcar una devolución como compensada"""
    try:
        devolucion = Devolucion.query.get(id)
        
        if not devolucion:
            return jsonify({'error': 'Devolución no encontrada'}), 404
        
        if devolucion.estado != 'pendiente':
            return jsonify({'error': 'La devolución ya fue compensada'}), 400
        
        data = request.get_json()
        
        if not data or not data.get('pedido_compensacion_id'):
            return jsonify({'error': 'ID del pedido de compensación es requerido'}), 400
        
        pedido_compensacion_id = data['pedido_compensacion_id']
        
        # Validar que el pedido existe
        pedido_compensacion = Pedido.query.get(pedido_compensacion_id)
        if not pedido_compensacion:
            return jsonify({'error': 'Pedido de compensación no encontrado'}), 404
        
        # Verificar que el pedido es del mismo cliente
        if pedido_compensacion.cliente_id != devolucion.cliente_id:
            return jsonify({'error': 'El pedido de compensación debe ser del mismo cliente'}), 400
        
        # Marcar como compensado
        devolucion.marcar_compensado(pedido_compensacion_id)
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Devolución marcada como compensada exitosamente',
            'devolucion': devolucion.to_dict(include_detalles=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al marcar como compensado: {str(e)}'}), 500


@devoluciones_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def eliminar_devolucion(id):
    """Eliminar una devolución (solo si está pendiente)"""
    try:
        devolucion = Devolucion.query.get(id)
        
        if not devolucion:
            return jsonify({'error': 'Devolución no encontrada'}), 404
        
        if devolucion.estado != 'pendiente':
            return jsonify({'error': 'Solo se pueden eliminar devoluciones pendientes'}), 400
        
        # Descontar del stock los productos devueltos
        for detalle in devolucion.detalles:
            producto = Producto.query.get(detalle.producto_id)
            producto.actualizar_stock(int(detalle.cantidad), 'restar')
        
        db.session.delete(devolucion)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Devolución eliminada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar devolución: {str(e)}'}), 500


@devoluciones_bp.route('/motivos', methods=['GET'])
@login_required
def listar_motivos():
    """Listar motivos de devolución disponibles"""
    try:
        motivos = [
            {'valor': 'vencido', 'nombre': 'Producto Vencido'},
            {'valor': 'mal_estado', 'nombre': 'Mal Estado'},
            {'valor': 'error_entrega', 'nombre': 'Error en la Entrega'},
            {'valor': 'otro', 'nombre': 'Otro'}
        ]
        
        return jsonify({
            'motivos': motivos
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar motivos: {str(e)}'}), 500


@devoluciones_bp.route('/estadisticas', methods=['GET'])
@login_required
def estadisticas_devoluciones():
    """Obtener estadísticas de devoluciones"""
    try:
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        
        query = Devolucion.query
        
        if fecha_desde:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Devolucion.fecha_devolucion >= fecha_desde_obj)
        
        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Devolucion.fecha_devolucion <= fecha_hasta_obj)
        
        # Contar por estado
        total_pendientes = query.filter_by(estado='pendiente').count()
        total_compensadas = query.filter_by(estado='compensado').count()
        
        # Contar por motivo
        devoluciones_por_motivo = db.session.query(
            Devolucion.motivo,
            db.func.count(Devolucion.id).label('total')
        ).filter(Devolucion.id.in_([d.id for d in query.all()])
        ).group_by(Devolucion.motivo).all()
        
        motivos_dict = {motivo: total for motivo, total in devoluciones_por_motivo}
        
        return jsonify({
            'total_devoluciones': query.count(),
            'pendientes': total_pendientes,
            'compensadas': total_compensadas,
            'por_motivo': {
                'vencido': motivos_dict.get('vencido', 0),
                'mal_estado': motivos_dict.get('mal_estado', 0),
                'error_entrega': motivos_dict.get('error_entrega', 0),
                'otro': motivos_dict.get('otro', 0)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500


@devoluciones_bp.route('/cliente/<int:cliente_id>/pendientes-alerta', methods=['GET'])
@login_required
def alerta_devoluciones_pendientes(cliente_id):
    """Verificar si un cliente tiene devoluciones pendientes"""
    try:
        cliente = Cliente.query.get(cliente_id)
        
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        
        devoluciones_pendientes = Devolucion.query.filter_by(
            cliente_id=cliente_id,
            estado='pendiente'
        ).all()
        
        tiene_pendientes = len(devoluciones_pendientes) > 0
        
        return jsonify({
            'tiene_devoluciones_pendientes': tiene_pendientes,
            'cantidad': len(devoluciones_pendientes),
            'devoluciones': [dev.to_dict(include_detalles=True) for dev in devoluciones_pendientes] if tiene_pendientes else []
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al verificar devoluciones: {str(e)}'}), 500


@devoluciones_bp.route('/<int:id>/pdf', methods=['GET'])
@login_required
def generar_pdf_devolucion(id):
    """Generar PDF de una devolución"""
    try:
        devolucion = Devolucion.query.get(id)
        
        if not devolucion:
            return jsonify({'error': 'Devolución no encontrada'}), 404
        
        pdf_gen = PDFGenerator()
        buffer = pdf_gen.generar_devolucion(devolucion.to_dict(include_detalles=True))
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'devolucion_{devolucion.numero_devolucion}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error al generar PDF: {str(e)}'}), 500