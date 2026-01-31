from app.database import db, get_bolivia_time

class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    unidad_medida = db.Column(db.String(20), default='unidad')  # kg, unidad, caja, paquete
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=get_bolivia_time)
    
    # Relaciones
    detalle_pedidos = db.relationship('DetallePedido', backref='producto', lazy=True)
    detalle_devoluciones = db.relationship('DetalleDevolucion', 
                                          foreign_keys='DetalleDevolucion.producto_id',
                                          backref='producto', lazy=True)
    
    def to_dict(self, include_stock=True):
        """Convertir a diccionario"""
        data = {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'unidad_medida': self.unidad_medida,
            'precio_venta': float(self.precio_venta),
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y') if self.fecha_creacion else None
        }
        
        if include_stock:
            data['stock_actual'] = self.stock_actual
            data['stock_minimo'] = self.stock_minimo
            data['stock_bajo'] = self.stock_actual <= self.stock_minimo
        
        return data
    
    def actualizar_stock(self, cantidad, operacion='restar'):
        """Actualizar stock del producto"""
        if operacion == 'restar':
            self.stock_actual -= cantidad
        elif operacion == 'sumar':
            self.stock_actual += cantidad
    
    def __repr__(self):
        return f'<Producto {self.nombre}>'