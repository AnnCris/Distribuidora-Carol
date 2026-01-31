from app.database import db, get_bolivia_time
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='vendedor')  # admin, vendedor
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=get_bolivia_time)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Relaciones
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    devoluciones = db.relationship('Devolucion', backref='usuario', lazy=True)
    
    def set_password(self, password):
        """Hashear contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'usuario': self.usuario,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if self.ultimo_acceso else None
        }
    
    def __repr__(self):
        return f'<Usuario {self.usuario}>'