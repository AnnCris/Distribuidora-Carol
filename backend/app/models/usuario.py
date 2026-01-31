from app.database import db, get_bolivia_time
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='vendedor')  # 'admin' o 'vendedor'
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=get_bolivia_time, nullable=False)
    
    # Relaciones
    pedidos = db.relationship('Pedido', backref='usuario', lazy='dynamic')
    devoluciones = db.relationship('Devolucion', backref='usuario', lazy='dynamic')
    
    def set_password(self, password):
        """Hashear la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Usuario {self.email}>'