from app.database import db, get_bolivia_time

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    celular = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    zona = db.Column(db.String(50))
    ciudad = db.Column(db.String(50), default='La Paz')
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=get_bolivia_time)
    
    # Relaciones
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)
    devoluciones = db.relationship('Devolucion', backref='cliente', lazy=True)
    
    def to_dict(self, include_stats=False):
        """Convertir a diccionario"""
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'celular': self.celular,
            'direccion': self.direccion,
            'zona': self.zona,
            'ciudad': self.ciudad,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.strftime('%d/%m/%Y') if self.fecha_registro else None
        }
        
        if include_stats:
            data['total_pedidos'] = len(self.pedidos)
            data['total_devoluciones'] = len(self.devoluciones)
        
        return data
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'