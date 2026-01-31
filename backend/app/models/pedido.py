from app.database import db, get_bolivia_time
from datetime import datetime

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_pedido = db.Column(db.DateTime, default=get_bolivia_time)
    subtotal = db.Column(db.Numeric(10, 2), default=0)
    descuento = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, entregado, cancelado
    observaciones = db.Column(db.Text)
    fecha_entrega = db.Column(db.Date)
    
    # Relaciones
    detalles = db.relationship('DetallePedido', backref='pedido', lazy=True, cascade='all, delete-orphan')
    devoluciones = db.relationship('Devolucion', foreign_keys='Devolucion.pedido_id', 
                                  backref='pedido_original', lazy=True)
    
    @staticmethod
    def generar_numero_pedido():
        """Generar número de pedido único: PED-YYYYMMDD-001"""
        hoy = get_bolivia_time().date()
        fecha_str = hoy.strftime('%Y%m%d')
        
        ultimo_pedido = Pedido.query.filter(
            Pedido.numero_pedido.like(f'PED-{fecha_str}-%')
        ).order_by(Pedido.id.desc()).first()
        
        if ultimo_pedido:
            ultimo_numero = int(ultimo_pedido.numero_pedido.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1
        
        return f'PED-{fecha_str}-{nuevo_numero:03d}'
    
    def calcular_totales(self):
        """Calcular subtotal y total del pedido"""
        self.subtotal = sum(detalle.subtotal for detalle in self.detalles)
        self.total = self.subtotal - self.descuento
    
    def to_dict(self, include_detalles=False):
        """Convertir a diccionario"""
        data = {
            'id': self.id,
            'numero_pedido': self.numero_pedido,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre if self.cliente else None,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.nombre_completo if self.usuario else None,
            'fecha_pedido': self.fecha_pedido.strftime('%d/%m/%Y %H:%M') if self.fecha_pedido else None,
            'subtotal': float(self.subtotal),
            'descuento': float(self.descuento),
            'total': float(self.total),
            'estado': self.estado,
            'observaciones': self.observaciones,
            'fecha_entrega': self.fecha_entrega.strftime('%d/%m/%Y') if self.fecha_entrega else None
        }
        
        if include_detalles:
            data['detalles'] = [detalle.to_dict() for detalle in self.detalles]
        
        return data
    
    def __repr__(self):
        return f'<Pedido {self.numero_pedido}>'


class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    def calcular_subtotal(self):
        """Calcular subtotal del detalle"""
        self.subtotal = self.cantidad * self.precio_unitario
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'producto_codigo': self.producto.codigo if self.producto else None,
            'unidad_medida': self.producto.unidad_medida if self.producto else None,
            'cantidad': float(self.cantidad),
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal)
        }
    
    def __repr__(self):
        return f'<DetallePedido {self.id}>'