from app.database import db, get_bolivia_time

class Devolucion(db.Model):
    __tablename__ = 'devoluciones'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_devolucion = db.Column(db.String(20), unique=True, nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'))
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_devolucion = db.Column(db.DateTime, default=get_bolivia_time)
    motivo = db.Column(db.String(50), nullable=False)  # vencido, mal_estado, error_entrega, otro
    descripcion_motivo = db.Column(db.Text)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, compensado
    pedido_compensacion_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'))
    fecha_compensacion = db.Column(db.DateTime)
    observaciones = db.Column(db.Text)
    
    # Relaciones
    detalles = db.relationship('DetalleDevolucion', backref='devolucion', lazy=True, cascade='all, delete-orphan')
    pedido_compensacion = db.relationship('Pedido', foreign_keys=[pedido_compensacion_id],
                                         backref='devoluciones_compensadas')
    
    @staticmethod
    def generar_numero_devolucion():
        """Generar número de devolución único: DEV-YYYYMMDD-001"""
        hoy = get_bolivia_time().date()
        fecha_str = hoy.strftime('%Y%m%d')
        
        ultima_devolucion = Devolucion.query.filter(
            Devolucion.numero_devolucion.like(f'DEV-{fecha_str}-%')
        ).order_by(Devolucion.id.desc()).first()
        
        if ultima_devolucion:
            ultimo_numero = int(ultima_devolucion.numero_devolucion.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1
        
        return f'DEV-{fecha_str}-{nuevo_numero:03d}'
    
    def marcar_compensado(self, pedido_compensacion_id):
        """Marcar devolución como compensada"""
        self.estado = 'compensado'
        self.pedido_compensacion_id = pedido_compensacion_id
        self.fecha_compensacion = get_bolivia_time()
    
    def to_dict(self, include_detalles=False):
        """Convertir a diccionario"""
        data = {
            'id': self.id,
            'numero_devolucion': self.numero_devolucion,
            'pedido_id': self.pedido_id,
            'numero_pedido': self.pedido_original.numero_pedido if self.pedido_original else None,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre if self.cliente else None,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.nombre_completo if self.usuario else None,
            'fecha_devolucion': self.fecha_devolucion.strftime('%d/%m/%Y %H:%M') if self.fecha_devolucion else None,
            'motivo': self.motivo,
            'descripcion_motivo': self.descripcion_motivo,
            'estado': self.estado,
            'pedido_compensacion_id': self.pedido_compensacion_id,
            'fecha_compensacion': self.fecha_compensacion.strftime('%d/%m/%Y %H:%M') if self.fecha_compensacion else None,
            'observaciones': self.observaciones
        }
        
        if include_detalles:
            data['detalles'] = [detalle.to_dict() for detalle in self.detalles]
        
        return data
    
    def __repr__(self):
        return f'<Devolucion {self.numero_devolucion}>'


class DetalleDevolucion(db.Model):
    __tablename__ = 'detalle_devoluciones'
    
    id = db.Column(db.Integer, primary_key=True)
    devolucion_id = db.Column(db.Integer, db.ForeignKey('devoluciones.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    producto_reemplazo_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    observacion = db.Column(db.String(255))
    
    # Relación con producto de reemplazo
    producto_reemplazo = db.relationship('Producto', foreign_keys=[producto_reemplazo_id])
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'producto_codigo': self.producto.codigo if self.producto else None,
            'cantidad': float(self.cantidad),
            'producto_reemplazo_id': self.producto_reemplazo_id,
            'producto_reemplazo_nombre': self.producto_reemplazo.nombre if self.producto_reemplazo else None,
            'observacion': self.observacion
        }
    
    def __repr__(self):
        return f'<DetalleDevolucion {self.id}>'