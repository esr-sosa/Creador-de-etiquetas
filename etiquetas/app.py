# app.py - VERSIÓN FINAL CON CUADRO DE TEXTO Y DISEÑO PROFESIONAL
import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from pdf2image import convert_from_path

# --- CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads' # Aunque no subimos, la usamos para archivos temporales
app.config['GENERATED_FOLDER'] = 'generated'
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# --- DICCIONARIO PARA TRADUCIR CÓDIGOS DE MODELO ---
PRODUCT_TYPE_MAP = {
    "iPhone13,2": "iPhone 12",
    "iPhone13,1": "iPhone 12 Mini",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    # Agrega más modelos aquí si es necesario
}

# --- FUNCIÓN DE PARSEO (TRADUCTOR) PARA EL TEXTO PEGADO ---
def parse_info(text_content):
    """
    Parsea el texto pegado desde el informe de dispositivo de 3uTools.
    """
    data = {
        'model': 'N/A', 'color': 'N/A', 'capacity': 'N/A',
        'serial': 'N/A', 'battery_life': 'N/A', 'imei': 'N/A'
    }

    # Función auxiliar para buscar valores
    def find_value(key):
        match = re.search(fr"^{key}\s+(.+)$", text_content, re.MULTILINE)
        return match.group(1).strip() if match else 'N/A'

    # Extracción de datos
    product_type = find_value("ProductType")
    data['model'] = PRODUCT_TYPE_MAP.get(product_type, product_type) # Traduce el código a nombre
    data['serial'] = find_value("SerialNumber")
    data['imei'] = find_value("InternationalMobileEquipmentIdentity")
    
    # El color se infiere por códigos. '1' es usualmente Negro/Gris Espacial/etc.
    color_code = find_value("DeviceColor")
    if color_code == '1':
        data['color'] = "Negro"
    elif color_code == '2':
        data['color'] = "Blanco"
    # ... se pueden agregar más códigos de color si los descubres

    # NOTA: Capacidad y Batería no están en este informe
    # data['capacity'] = ...
    # data['battery_life'] = ...

    return data

# --- FUNCIÓN DE DIBUJO (DISEÑADOR) PROFESIONAL ---
def draw_label(c, x_start, y_start, data):
    """
    Diseño final de etiqueta: rectangular, limpio y perfectamente alineado.
    """
    label_width, label_height = 100 * mm, 60 * mm
    primary_text, secondary_text, border_color = HexColor("#1c1c1e"), HexColor("#6e6e73"), HexColor("#d2d2d7")

    c.saveState()
    # Contenedor y borde
    c.setStrokeColor(border_color)
    c.setLineWidth(0.4)
    c.roundRect(x_start, y_start, label_width, label_height, 3 * mm, stroke=1, fill=0)

    # --- TÍTULO (MODELO) Y MARCA ---
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(primary_text)
    c.drawString(x_start + 10 * mm, y_start + label_height - 20 * mm, data.get('model', 'Dispositivo'))
    
    c.setFont("Helvetica", 10)
    c.setFillColor(secondary_text)
    c.drawRightString(x_start + label_width - 10 * mm, y_start + label_height - 13 * mm, "ImportStore SL")

    # --- LÍNEA SEPARADORA ---
    c.setStrokeColor(border_color)
    c.setLineWidth(0.4)
    c.line(x_start + 8 * mm, y_start + label_height - 28 * mm, x_start + label_width - 8 * mm, y_start + label_height - 28 * mm)

    # --- ESPECIFICACIONES EN DOS COLUMNAS ALINEADAS ---
    y_pos = y_start + label_height - 38 * mm
    x_col1 = x_start + 10 * mm
    x_col2 = x_start + 55 * mm

    # Columna 1
    c.setFont("Helvetica", 10); c.setFillColor(secondary_text); c.drawString(x_col1, y_pos, "Capacidad")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(primary_text); c.drawString(x_col1, y_pos - 5*mm, data.get('capacity', 'N/A'))
    
    y_pos -= 15 * mm
    c.setFont("Helvetica", 10); c.setFillColor(secondary_text); c.drawString(x_col1, y_pos, "Color")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(primary_text); c.drawString(x_col1, y_pos - 5*mm, data.get('color', 'N/A'))

    # Columna 2
    y_pos = y_start + label_height - 38 * mm # Reiniciar Y
    c.setFont("Helvetica", 10); c.setFillColor(secondary_text); c.drawString(x_col2, y_pos, "Salud de Batería")
    c.setFont("Helvetica-Bold", 11); c.setFillColor(primary_text); c.drawString(x_col2, y_pos - 5*mm, data.get('battery_life', 'N/A'))
    
    # --- SECCIÓN INFERIOR: IDENTIFICADORES ---
    footer_y = y_start + 10 * mm
    c.setFont("Helvetica", 10); c.setFillColor(secondary_text); c.drawString(x_start + 10 * mm, footer_y, "Número de Serie")
    c.setFont("Helvetica-Bold", 10); c.setFillColor(primary_text); c.drawString(x_start + 10 * mm, footer_y - 5*mm, data.get('serial', 'N/A'))
    
    c.setFont("Helvetica", 10); c.setFillColor(secondary_text); c.drawRightString(x_start + label_width - 10*mm, footer_y, "IMEI")
    c.setFont("Helvetica-Bold", 10); c.setFillColor(primary_text); c.drawRightString(x_start + label_width - 10*mm, footer_y - 5*mm, data.get('imei', 'N/A'))
    
    c.restoreState()


def create_pdf(data, output_filename):
    c = canvas.Canvas(output_filename, pagesize=A4)
    draw_label(c, (A4[0] - 100 * mm) / 2, A4[1] - 80 * mm, data)
    c.save()

# --- RUTAS DE LA APLICACIÓN WEB ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_text():
    text_content = request.form.get('text_content')
    if not text_content:
        return jsonify({'error': 'El cuadro de texto está vacío.'}), 400

    device_data = parse_info(text_content)
    if not device_data:
        return jsonify({'error': 'No se pudo procesar el texto.'}), 500

    unique_id = str(uuid.uuid4())
    pdf_filename = f"etiqueta_{unique_id}.pdf"
    pdf_filepath = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
    create_pdf(device_data, pdf_filepath)

    preview_filename = f"preview_{unique_id}.png"
    preview_filepath = os.path.join(app.config['GENERATED_FOLDER'], preview_filename)
    try:
        images = convert_from_path(pdf_filepath, 300, first_page=1, last_page=1)
        if images: images[0].save(preview_filepath, 'PNG')
    except Exception as e:
        print(f"Error generando preview: {e}"); return jsonify({'error': 'Error al generar la vista previa.'}), 500
    
    return jsonify({
        'preview_url': f"/generated/{preview_filename}",
        'pdf_url': f"/generated/{pdf_filename}"
    })

@app.route('/generated/<filename>')
def generated_file(filename): return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__': app.run(debug=True)