from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime, date
from app.database import db, get_bolivia_time
from app.models.pedido import Pedido, DetallePedido
from app.models.cliente import Cliente
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.models.devolucion import Devolucion
from app.utils.decorators import login_required
from app.utils.pdf_generator import PDFGenerator

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/', methods=['GET'])
@login_required
def listar_pedidos():
    """Listar todos los pedidos con filtros"""
    try:
        # Parámetros de filtrado
        cliente_id = request.args.get('cliente_id', type=int)
        estado = request.args.get('estado')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        buscar = request.args.get('buscar', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Pedido.query
        
        # Filtro por cliente
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        
        # Filtro por estado
        if estado:
            query = query.filter_by(estado=estado)
        
        # Filtro por rango de fechas
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.filter(Pedido.fecha_pedido >= fecha_desde_obj)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'}), 400
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(Pedido.fecha_pedido <= fecha_hasta_obj)
            except ValueError:
                return jsonify({'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'}), 400
        
        # Búsqueda por número de pedido o nombre de cliente
        if buscar:
            query = query.join(Cliente).filter(
                db.or_(
                    Pedido.numero_pedido.ilike(f'%{buscar}%'),
                    Cliente.nombre.ilike(f'%{buscar}%')
                )
            )
        
        # Paginación
        pedidos_paginados = query.order_by(Pedido.fecha_pedido.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'pedidos': [pedido.to_dict() for pedido in pedidos_paginados.items],
            'total': pedidos_paginados.total,
            'pagina_actual': page,
            'total_paginas': pedidos_paginados.pages,
            'por_pagina': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al listar pedidos: {str(e)}'}), 500


@pedidos_bp.route('/<int:id>', methods=['GET'])
@login_required
def obtener_pedido(id):
    """Obtener un pedido por ID con todos sus detalles"""
    try:
        pedido = Pedido.query.get(id)
        
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        # Verificar si tiene devoluciones pendientes
        devoluciones_pendientes = Devolucion.query.filter_by(
            cliente_id=pedido.cliente_id,
            estado='pendiente'
        ).all()
        
        return jsonify({
            'pedido': pedido.to_dict(include_detalles=True),
            'devoluciones_pendientes': [d.to_dict(include_detalles=True) for d in devoluciones_pendientes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener pedido: {str(e)}'}), 500


@pedidos_bp.route('/', methods=['POST'])
@login_required
def crear_pedido():
    try:
        user_id = session.get('user_id')
        data = request.get_json()

        if not data or not data.get('cliente_id') or not data.get('detalles'):
            return jsonify({'error': 'Cliente y detalles son requeridos'}), 400

        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        if not cliente.activo:
            return jsonify({'error': 'El cliente está desactivado'}), 400

        if not data['detalles'] or len(data['detalles']) == 0:
            return jsonify({'error': 'Debe agregar al menos un producto al pedido'}), 400

        numero_pedido = Pedido.generar_numero_pedido()
        descuento = float(data.get('descuento', 0))

        nuevo_pedido = Pedido(
            numero_pedido=numero_pedido,
            cliente_id=data['cliente_id'],
            usuario_id=user_id,
            descuento=descuento,
            observaciones=data.get('observaciones'),
            fecha_entrega=datetime.strptime(data['fecha_entrega'], '%Y-%m-%d').date() if data.get('fecha_entrega') else None,
            subtotal=0,
            total=0
        )

        db.session.add(nuevo_pedido)
        db.session.flush()

        subtotal_acumulado = 0.0

        for detalle_data in data['detalles']:
            producto = Producto.query.get(detalle_data['producto_id'])
            if not producto:
                db.session.rollback()
                return jsonify({'error': f'Producto con ID {detalle_data["producto_id"]} no encontrado'}), 404
            if not producto.activo:
                db.session.rollback()
                return jsonify({'error': f'El producto {producto.nombre} está desactivado'}), 400

            try:
                cantidad = float(detalle_data['cantidad'])
                if cantidad <= 0:
                    raise ValueError()
            except:
                db.session.rollback()
                return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400

            precio_unitario = float(detalle_data.get('precio_unitario', producto.precio_venta))
            subtotal_detalle = cantidad * precio_unitario

            detalle = DetallePedido(
                pedido_id=nuevo_pedido.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal_detalle
            )
            db.session.add(detalle)

            subtotal_acumulado += subtotal_detalle
            producto.actualizar_stock(int(cantidad), 'restar')

        nuevo_pedido.subtotal = subtotal_acumulado
        nuevo_pedido.total = subtotal_acumulado - descuento

        db.session.commit()

        return jsonify({
            'mensaje': 'Pedido creado exitosamente',
            'pedido': nuevo_pedido.to_dict(include_detalles=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear pedido: {str(e)}'}), 500

@pedidos_bp.route('/<int:id>', methods=['PUT'])
@login_required
def actualizar_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        if pedido.estado != 'pendiente':
            return jsonify({'error': f'No se puede editar un pedido en estado "{pedido.estado}"'}), 400
        
        data = request.get_json()
        
        if 'observaciones' in data:
            pedido.observaciones = data['observaciones']
        
        if 'fecha_entrega' in data:
            pedido.fecha_entrega = datetime.strptime(data['fecha_entrega'], '%Y-%m-%d').date() if data['fecha_entrega'] else None
        
        descuento = float(data.get('descuento', pedido.descuento))
        pedido.descuento = descuento

        if 'detalles' in data:
            # Restaurar stock de productos anteriores
            for detalle in pedido.detalles:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    producto.actualizar_stock(int(detalle.cantidad), 'sumar')
            
            # Eliminar detalles antiguos
            DetallePedido.query.filter_by(pedido_id=id).delete()
            db.session.flush()

            subtotal_acumulado = 0.0

            for detalle_data in data['detalles']:
                producto = Producto.query.get(detalle_data['producto_id'])
                if not producto:
                    db.session.rollback()
                    return jsonify({'error': f'Producto con ID {detalle_data["producto_id"]} no encontrado'}), 404
                
                if not producto.activo:
                    db.session.rollback()
                    return jsonify({'error': f'El producto {producto.nombre} está desactivado'}), 400
                
                cantidad = float(detalle_data['cantidad'])
                precio_unitario = float(detalle_data.get('precio_unitario', producto.precio_venta))
                subtotal_detalle = cantidad * precio_unitario

                detalle = DetallePedido(
                    pedido_id=pedido.id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal_detalle
                )
                db.session.add(detalle)

                subtotal_acumulado += subtotal_detalle
                producto.actualizar_stock(int(cantidad), 'restar')

            # Asignar totales directamente
            pedido.subtotal = subtotal_acumulado
            pedido.total = subtotal_acumulado - descuento

        db.session.commit()
        
        return jsonify({
            'mensaje': 'Pedido actualizado exitosamente',
            'pedido': pedido.to_dict(include_detalles=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar pedido: {str(e)}'}), 500

@pedidos_bp.route('/<int:id>/cambiar-estado', methods=['PATCH'])
@login_required
def cambiar_estado_pedido(id):
    """Cambiar el estado de un pedido"""
    try:
        pedido = Pedido.query.get(id)
        
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('estado'):
            return jsonify({'error': 'Estado es requerido'}), 400
        
        nuevo_estado = data['estado']
        
        # Validar estado
        estados_validos = ['pendiente', 'entregado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return jsonify({
                'error': 'Estado inválido',
                'estados_validos': estados_validos
            }), 400
        
        # Si se cancela, restaurar stock
        if nuevo_estado == 'cancelado' and pedido.estado != 'cancelado':
            for detalle in pedido.detalles:
                producto = Producto.query.get(detalle.producto_id)
                producto.actualizar_stock(int(detalle.cantidad), 'sumar')
        
        # Si se reactiva desde cancelado, descontar stock
        if pedido.estado == 'cancelado' and nuevo_estado in ['pendiente', 'entregado']:
            for detalle in pedido.detalles:
                producto = Producto.query.get(detalle.producto_id)
                if producto.stock_actual < int(detalle.cantidad):
                    db.session.rollback()
                    return jsonify({
                        'error': f'Stock insuficiente de {producto.nombre}',
                        'stock_disponible': producto.stock_actual,
                        'cantidad_necesaria': int(detalle.cantidad)
                    }), 400
                producto.actualizar_stock(int(detalle.cantidad), 'restar')
        
        pedido.estado = nuevo_estado
        db.session.commit()
        
        return jsonify({
            'mensaje': f'Pedido cambiado a estado "{nuevo_estado}" exitosamente',
            'pedido': pedido.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500


@pedidos_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def eliminar_pedido(id):
    """Eliminar un pedido (solo si está pendiente)"""
    try:
        pedido = Pedido.query.get(id)
        
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        if pedido.estado != 'pendiente':
            return jsonify({'error': 'Solo se pueden eliminar pedidos en estado pendiente'}), 400
        
        # Restaurar stock
        for detalle in pedido.detalles:
            producto = Producto.query.get(detalle.producto_id)
            producto.actualizar_stock(int(detalle.cantidad), 'sumar')
        
        db.session.delete(pedido)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Pedido eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar pedido: {str(e)}'}), 500


@pedidos_bp.route('/resumen-dia', methods=['GET'])
@login_required
def resumen_dia():
    """Obtener resumen de pedidos del día"""
    try:
        fecha_param = request.args.get('fecha')
        
        if fecha_param:
            try:
                fecha = datetime.strptime(fecha_param, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        else:
            fecha = get_bolivia_time().date()
        
        # Obtener pedidos del día
        pedidos = Pedido.query.filter(
            db.func.date(Pedido.fecha_pedido) == fecha
        ).order_by(Pedido.cliente_id, Pedido.fecha_pedido).all()
        
        # Agrupar por cliente
        resumen = []
        total_general = 0
        
        for pedido in pedidos:
            cliente_existente = next(
                (item for item in resumen if item['cliente_id'] == pedido.cliente_id),
                None
            )
            
            if cliente_existente:
                for detalle in pedido.detalles:
                    cliente_existente['productos'].append({
                        'nombre': detalle.producto.nombre,
                        'cantidad': float(detalle.cantidad),
                        'unidad_medida': detalle.producto.unidad_medida
                    })
                cliente_existente['total'] += float(pedido.total)
            else:
                resumen.append({
                    'cliente_id': pedido.cliente_id,
                    'cliente_nombre': pedido.cliente.nombre,
                    'productos': [{
                        'nombre': detalle.producto.nombre,
                        'cantidad': float(detalle.cantidad),
                        'unidad_medida': detalle.producto.unidad_medida
                    } for detalle in pedido.detalles],
                    'total': float(pedido.total)
                })
            
            total_general += float(pedido.total)
        
        return jsonify({
            'fecha': fecha.strftime('%d/%m/%Y'),
            'resumen': resumen,
            'total_pedidos': len(pedidos),
            'total_clientes': len(resumen),
            'total_general': total_general
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al generar resumen: {str(e)}'}), 500


@pedidos_bp.route('/estadisticas', methods=['GET'])
@login_required
def estadisticas_pedidos():
    """Obtener estadísticas generales de pedidos"""
    try:
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        
        query = Pedido.query
        
        if fecha_desde:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Pedido.fecha_pedido >= fecha_desde_obj)
        
        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Pedido.fecha_pedido <= fecha_hasta_obj)
        
        # Contar por estado
        total_pendientes = query.filter_by(estado='pendiente').count()
        total_entregados = query.filter_by(estado='entregado').count()
        total_cancelados = query.filter_by(estado='cancelado').count()
        
        # Calcular total vendido
        pedidos_entregados = query.filter_by(estado='entregado').all()
        total_vendido = sum(float(p.total) for p in pedidos_entregados)
        
        return jsonify({
            'total_pedidos': query.count(),
            'pendientes': total_pendientes,
            'entregados': total_entregados,
            'cancelados': total_cancelados,
            'total_vendido': total_vendido
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener estadísticas: {str(e)}'}), 500


@pedidos_bp.route('/<int:id>/pdf', methods=['GET'])
@login_required
def generar_pdf_pedido(id):
    """Generar PDF de un pedido"""
    try:
        pedido = Pedido.query.get(id)
        
        if not pedido:
            return jsonify({'error': 'Pedido no encontrado'}), 404
        
        pdf_gen = PDFGenerator()
        buffer = pdf_gen.generar_pedido(pedido.to_dict(include_detalles=True))
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'pedido_{pedido.numero_pedido}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error al generar PDF: {str(e)}'}), 500


@pedidos_bp.route('/resumen-dia/pdf', methods=['GET'])
@login_required
def generar_pdf_resumen_dia():
    """Generar PDF del resumen del día"""
    try:
        fecha_param = request.args.get('fecha')
        
        if fecha_param:
            try:
                fecha = datetime.strptime(fecha_param, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        else:
            fecha = get_bolivia_time().date()
        
        # Obtener datos del resumen
        pedidos = Pedido.query.filter(
            db.func.date(Pedido.fecha_pedido) == fecha
        ).order_by(Pedido.cliente_id, Pedido.fecha_pedido).all()
        
        # Agrupar por cliente
        resumen = []
        total_general = 0
        
        for pedido in pedidos:
            cliente_existente = next(
                (item for item in resumen if item['cliente_id'] == pedido.cliente_id),
                None
            )
            
            if cliente_existente:
                for detalle in pedido.detalles:
                    cliente_existente['productos'].append({
                        'nombre': detalle.producto.nombre,
                        'cantidad': float(detalle.cantidad),
                        'unidad_medida': detalle.producto.unidad_medida
                    })
                cliente_existente['total'] += float(pedido.total)
            else:
                resumen.append({
                    'cliente_id': pedido.cliente_id,
                    'cliente_nombre': pedido.cliente.nombre,
                    'productos': [{
                        'nombre': detalle.producto.nombre,
                        'cantidad': float(detalle.cantidad),
                        'unidad_medida': detalle.producto.unidad_medida
                    } for detalle in pedido.detalles],
                    'total': float(pedido.total)
                })
            
            total_general += float(pedido.total)
        
        data = {
            'fecha': fecha.strftime('%d/%m/%Y'),
            'resumen': resumen,
            'total_pedidos': len(pedidos),
            'total_clientes': len(resumen),
            'total_general': total_general
        }
        
        pdf_gen = PDFGenerator()
        buffer = pdf_gen.generar_resumen_dia(data)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'resumen_{fecha.strftime("%Y%m%d")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error al generar PDF: {str(e)}'}), 500