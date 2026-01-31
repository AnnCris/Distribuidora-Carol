from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
from io import BytesIO

class PDFGenerator:
    """Clase para generar PDFs del sistema"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()
    
    def _crear_estilos_personalizados(self):
        """Crear estilos personalizados para el PDF"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloEmpresa',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Información general
        self.styles.add(ParagraphStyle(
            name='InfoGeneral',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Cliente nombre
        self.styles.add(ParagraphStyle(
            name='ClienteNombre',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            spaceAfter=4,
            spaceBefore=8
        ))
    
    def generar_resumen_dia(self, data, output_path=None):
        """
        Generar PDF del resumen del día
        
        Args:
            data: Diccionario con la información del resumen
            output_path: Ruta donde guardar el PDF (opcional)
        
        Returns:
            BytesIO si no se especifica output_path, None si se guarda en archivo
        """
        # Crear buffer o archivo
        if output_path:
            pdf = SimpleDocTemplate(output_path, pagesize=A4)
        else:
            buffer = BytesIO()
            pdf = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Contenido del PDF
        elementos = []
        
        # Encabezado
        elementos.append(Paragraph(
            "DISTRIBUIDORA DE QUESOS CAROLINA",
            self.styles['TituloEmpresa']
        ))
        elementos.append(Spacer(1, 0.3*cm))
        
        elementos.append(Paragraph(
            "RESUMEN DE PEDIDOS DEL DÍA",
            self.styles['Subtitulo']
        ))
        elementos.append(Spacer(1, 0.5*cm))
        
        # Información de fecha
        elementos.append(Paragraph(
            f"<b>Fecha:</b> {data['fecha']}",
            self.styles['InfoGeneral']
        ))
        elementos.append(Spacer(1, 0.3*cm))
        
        # Línea separadora
        elementos.append(self._crear_linea_separadora())
        elementos.append(Spacer(1, 0.4*cm))
        
        # Resumen por cliente
        for item in data['resumen']:
            # Nombre del cliente
            elementos.append(Paragraph(
                f"CLIENTE: {item['cliente_nombre'].upper()}",
                self.styles['ClienteNombre']
            ))
            
            # Lista de productos
            productos_texto = []
            for producto in item['productos']:
                cantidad_formato = self._formatear_cantidad(producto['cantidad'])
                productos_texto.append(
                    f"  • {producto['nombre']} × {cantidad_formato} {producto['unidad_medida']}"
                )
            
            for prod_text in productos_texto:
                elementos.append(Paragraph(
                    prod_text,
                    self.styles['InfoGeneral']
                ))
            
            # Total del cliente
            elementos.append(Paragraph(
                f"<b>Total: Bs. {self._formatear_precio(item['total'])}</b>",
                self.styles['InfoGeneral']
            ))
            
            elementos.append(Spacer(1, 0.5*cm))
        
        # Línea separadora final
        elementos.append(self._crear_linea_separadora())
        elementos.append(Spacer(1, 0.4*cm))
        
        # Resumen general
        resumen_data = [
            ['RESUMEN GENERAL', ''],
            ['Total de pedidos:', str(data['total_pedidos'])],
            ['Total de clientes:', str(data['total_clientes'])],
            ['Total general:', f"Bs. {self._formatear_precio(data['total_general'])}"]
        ]
        
        tabla_resumen = Table(resumen_data, colWidths=[10*cm, 6*cm])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
        ]))
        
        elementos.append(tabla_resumen)
        elementos.append(Spacer(1, 1*cm))
        
        # Pie de página
        elementos.append(Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['InfoGeneral']
        ))
        
        # Construir PDF
        pdf.build(elementos)
        
        if output_path:
            return None
        else:
            buffer.seek(0)
            return buffer
    
    def generar_pedido(self, pedido_data, output_path=None):
        """
        Generar PDF de un pedido individual
        
        Args:
            pedido_data: Diccionario con la información del pedido
            output_path: Ruta donde guardar el PDF (opcional)
        
        Returns:
            BytesIO si no se especifica output_path, None si se guarda en archivo
        """
        # Crear buffer o archivo
        if output_path:
            pdf = SimpleDocTemplate(output_path, pagesize=A4)
        else:
            buffer = BytesIO()
            pdf = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Contenido del PDF
        elementos = []
        
        # Encabezado
        elementos.append(Paragraph(
            "DISTRIBUIDORA DE QUESOS CAROLINA",
            self.styles['TituloEmpresa']
        ))
        elementos.append(Spacer(1, 0.3*cm))
        
        elementos.append(Paragraph(
            "PEDIDO",
            self.styles['Subtitulo']
        ))
        elementos.append(Spacer(1, 0.5*cm))
        
        # Información del pedido
        info_pedido = [
            ['Número de Pedido:', pedido_data['numero_pedido']],
            ['Fecha:', pedido_data['fecha_pedido']],
            ['Estado:', pedido_data['estado'].upper()],
        ]
        
        tabla_info = Table(info_pedido, colWidths=[5*cm, 11*cm])
        tabla_info.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elementos.append(tabla_info)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Información del cliente
        elementos.append(Paragraph(
            "<b>INFORMACIÓN DEL CLIENTE</b>",
            self.styles['ClienteNombre']
        ))
        
        info_cliente = [
            ['Cliente:', pedido_data['cliente_nombre']],
        ]
        
        if pedido_data.get('fecha_entrega'):
            info_cliente.append(['Fecha de Entrega:', pedido_data['fecha_entrega']])
        
        tabla_cliente = Table(info_cliente, colWidths=[5*cm, 11*cm])
        tabla_cliente.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elementos.append(tabla_cliente)
        elementos.append(Spacer(1, 0.7*cm))
        
        # Detalle de productos
        elementos.append(Paragraph(
            "<b>DETALLE DEL PEDIDO</b>",
            self.styles['ClienteNombre']
        ))
        elementos.append(Spacer(1, 0.3*cm))
        
        # Tabla de productos
        productos_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
        
        for detalle in pedido_data['detalles']:
            cantidad_formato = self._formatear_cantidad(detalle['cantidad'])
            productos_data.append([
                f"{detalle['producto_nombre']} ({detalle['unidad_medida']})",
                cantidad_formato,
                f"Bs. {self._formatear_precio(detalle['precio_unitario'])}",
                f"Bs. {self._formatear_precio(detalle['subtotal'])}"
            ])
        
        tabla_productos = Table(productos_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
        tabla_productos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elementos.append(tabla_productos)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Totales
        totales_data = [
            ['Subtotal:', f"Bs. {self._formatear_precio(pedido_data['subtotal'])}"],
            ['Descuento:', f"Bs. {self._formatear_precio(pedido_data['descuento'])}"],
            ['TOTAL:', f"Bs. {self._formatear_precio(pedido_data['total'])}"]
        ]
        
        tabla_totales = Table(totales_data, colWidths=[14*cm, 3*cm])
        tabla_totales.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elementos.append(tabla_totales)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Observaciones
        if pedido_data.get('observaciones'):
            elementos.append(Paragraph(
                f"<b>Observaciones:</b> {pedido_data['observaciones']}",
                self.styles['InfoGeneral']
            ))
            elementos.append(Spacer(1, 0.5*cm))
        
        # Pie de página
        elementos.append(Spacer(1, 1*cm))
        elementos.append(Paragraph(
            f"Usuario: {pedido_data['usuario_nombre']} | Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['InfoGeneral']
        ))
        
        # Construir PDF
        pdf.build(elementos)
        
        if output_path:
            return None
        else:
            buffer.seek(0)
            return buffer
    
    def generar_devolucion(self, devolucion_data, output_path=None):
        """
        Generar PDF de una devolución
        
        Args:
            devolucion_data: Diccionario con la información de la devolución
            output_path: Ruta donde guardar el PDF (opcional)
        
        Returns:
            BytesIO si no se especifica output_path, None si se guarda en archivo
        """
        # Crear buffer o archivo
        if output_path:
            pdf = SimpleDocTemplate(output_path, pagesize=A4)
        else:
            buffer = BytesIO()
            pdf = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Contenido del PDF
        elementos = []
        
        # Encabezado
        elementos.append(Paragraph(
            "DISTRIBUIDORA DE QUESOS CAROLINA",
            self.styles['TituloEmpresa']
        ))
        elementos.append(Spacer(1, 0.3*cm))
        
        elementos.append(Paragraph(
            "NOTA DE DEVOLUCIÓN",
            self.styles['Subtitulo']
        ))
        elementos.append(Spacer(1, 0.5*cm))
        
        # Información de la devolución
        info_devolucion = [
            ['Número de Devolución:', devolucion_data['numero_devolucion']],
            ['Fecha:', devolucion_data['fecha_devolucion']],
            ['Estado:', devolucion_data['estado'].upper()],
            ['Motivo:', self._traducir_motivo(devolucion_data['motivo'])],
        ]
        
        if devolucion_data.get('numero_pedido'):
            info_devolucion.append(['Pedido Original:', devolucion_data['numero_pedido']])
        
        tabla_info = Table(info_devolucion, colWidths=[5*cm, 11*cm])
        tabla_info.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elementos.append(tabla_info)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Información del cliente
        elementos.append(Paragraph(
            f"<b>Cliente:</b> {devolucion_data['cliente_nombre']}",
            self.styles['ClienteNombre']
        ))
        elementos.append(Spacer(1, 0.7*cm))
        
        # Detalle de productos devueltos
        elementos.append(Paragraph(
            "<b>PRODUCTOS DEVUELTOS</b>",
            self.styles['ClienteNombre']
        ))
        elementos.append(Spacer(1, 0.3*cm))
        
        # Tabla de productos
        productos_data = [['Producto', 'Cantidad', 'Producto Reemplazo']]
        
        for detalle in devolucion_data['detalles']:
            cantidad_formato = self._formatear_cantidad(detalle['cantidad'])
            reemplazo = detalle.get('producto_reemplazo_nombre', 'Sin reemplazo')
            
            productos_data.append([
                detalle['producto_nombre'],
                cantidad_formato,
                reemplazo
            ])
        
        tabla_productos = Table(productos_data, colWidths=[7*cm, 3*cm, 7*cm])
        tabla_productos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elementos.append(tabla_productos)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Descripción del motivo
        if devolucion_data.get('descripcion_motivo'):
            elementos.append(Paragraph(
                f"<b>Descripción del motivo:</b> {devolucion_data['descripcion_motivo']}",
                self.styles['InfoGeneral']
            ))
            elementos.append(Spacer(1, 0.3*cm))
        
        # Observaciones
        if devolucion_data.get('observaciones'):
            elementos.append(Paragraph(
                f"<b>Observaciones:</b> {devolucion_data['observaciones']}",
                self.styles['InfoGeneral']
            ))
            elementos.append(Spacer(1, 0.3*cm))
        
        # Información de compensación
        if devolucion_data.get('fecha_compensacion'):
            elementos.append(Spacer(1, 0.5*cm))
            elementos.append(Paragraph(
                f"<b>Compensado el:</b> {devolucion_data['fecha_compensacion']}",
                self.styles['InfoGeneral']
            ))
        
        # Pie de página
        elementos.append(Spacer(1, 1*cm))
        elementos.append(Paragraph(
            f"Usuario: {devolucion_data['usuario_nombre']} | Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['InfoGeneral']
        ))
        
        # Construir PDF
        pdf.build(elementos)
        
        if output_path:
            return None
        else:
            buffer.seek(0)
            return buffer
    
    def _crear_linea_separadora(self):
        """Crear una línea separadora"""
        return Table([['_' * 100]], colWidths=[17*cm])
    
    def _formatear_precio(self, precio):
        """Formatear precio con 2 decimales"""
        return f"{float(precio):,.2f}"
    
    def _formatear_cantidad(self, cantidad):
        """Formatear cantidad eliminando decimales innecesarios"""
        cantidad_float = float(cantidad)
        if cantidad_float == int(cantidad_float):
            return str(int(cantidad_float))
        return str(cantidad_float)
    
    def _traducir_motivo(self, motivo):
        """Traducir código de motivo a texto legible"""
        motivos = {
            'vencido': 'Producto Vencido',
            'mal_estado': 'Mal Estado',
            'error_entrega': 'Error en la Entrega',
            'otro': 'Otro'
        }
        return motivos.get(motivo, motivo)