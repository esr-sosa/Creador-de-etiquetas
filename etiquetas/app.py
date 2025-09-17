# app.py - VERSIÓN DISEÑO RECTANGULAR PROFESIONAL
import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black
from pdf2image import convert_from_path

# --- CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# --- FUNCIÓN DE PARSEO (TRADUCTOR) DE ALTA PRECISIÓN ---
def parse_3utools_report(file_path):
    """
    Función de parseo final. Utiliza regex para extraer los datos de
    forma precisa sin importar los espacios o saltos de línea.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        return None

    data = {
        'model': 'N/A',
        'color': 'N/A',
        'capacity': 'N/A',
        'serial': 'N/A',
        'battery_life': 'N/A',
        'imei': 'N/A' # El reporte de 3uTools no parece incluir el IMEI
    }

    # Regex para Modelo: Busca "Device Model" y captura el texto hasta la siguiente palabra "Normal"
    model_match = re.search(r"Device Model\s+(.*?)\s+Normal", content, re.DOTALL)
    if model_match:
        # De las líneas capturadas, tomamos la que contiene "iPhone"
        for line in model_match.group(1).splitlines():
            if "iPhone" in line:
                data['model'] = line.strip()
                break

    # Regex para Color: Busca "Device Color" y captura el texto hasta la siguiente "Normal"
    color_match = re.search(r"Device Color\s+(.*?)\s+Normal", content, re.DOTALL)
    if color_match:
        color_text = color_match.group(1).replace("\n", " ").replace("，", ", ")
        # Limpieza final del texto de color
        color_text = re.sub(r'\s{2,}', ' ', color_text).strip()
        data['color'] = color_text.replace("Front Black, Rear (PRODUCT)RED", "Rojo (PRODUCT)RED")


    # Regex para Capacidad
    capacity_match = re.search(r"Hard Disk Capacity\s+(\d+GB)", content)
    if capacity_match:
        data['capacity'] = capacity_match.group(1).strip()

    # Regex para Número de Serie
    serial_match = re.search(r"Serial Number\s+([\w\d]+)", content)
    if serial_match:
        data['serial'] = serial_match.group(1).strip()

    # Regex para Batería
    battery_match = re.search(r"Battery Life\s+(\d+%)", content)
    if battery_match:
        data['battery_life'] = battery_match.group(1).strip()

    # Aún no encontramos el IMEI en el reporte, pero lo dejamos preparado
    # imei_match = re.search(r"IMEI:\s*(\d+)", content)
    # if imei_match: data['imei'] = imei_match.group(1).strip()

    return data


# --- FUNCIÓN DE DIBUJO (DISEÑADOR) RECTANGULAR Y LIMPIO ---
def draw_label(c, x_start, y_start, data):
    """
    Dibuja la etiqueta final con un diseño rectangular, ordenado y profesional.
    """
    label_width, label_height = 100 * mm, 60 * mm
    
    # Colores
    bg_color = HexColor("#FFFFFF")
    primary_text = HexColor("#000000")
    secondary_text = HexColor("#4A4A4A")
    border_color = HexColor("#DDDDDD")

    # Contenedor principal rectangular
    c.saveState()
    c.setFillColor(bg_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(0.5)
    c.rect(x_start, y_start, label_width, label_height, fill=1, stroke=1)

    # --- TÍTULO (MODELO) ---
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(primary_text)
    model_text = data.get('model', 'Dispositivo')
    c.drawString(x_start + 8 * mm, y_start + label_height - 18 * mm, model_text)

    # --- NOMBRE DE LA TIENDA ---
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(secondary_text)
    c.drawRightString(x_start + label_width - 8 * mm, y_start + label_height - 12 * mm, "ImportStore SL")

    # --- LÍNEA SEPARADORA ---
    c.setStrokeColor(border_color)
    c.setLineWidth(0.5)
    c.line(x_start + 8 * mm, y_start + label_height - 24 * mm, x_start + label_width - 8 * mm, y_start + label_height - 24 * mm)

    # --- ESPECIFICACIONES EN DOS COLUMNAS ---
    c.setFont("Helvetica", 11)
    c.setFillColor(secondary_text)
    
    # Coordenadas iniciales
    y_pos = y_start + label_height - 34 * mm
    x_col1_label = x_start + 8 * mm
    x_col1_value = x_start + 30 * mm
    x_col2_label = x_start + 55 * mm
    x_col2_value = x_start + 70 * mm

    # Columna 1
    c.drawString(x_col1_label, y_pos, "Capacidad:")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_col1_value, y_pos, data.get('capacity', 'N/A'))
    c.setFont("Helvetica", 11)

    # Columna 2
    c.drawString(x_col2_label, y_pos, "Batería:")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_col2_value, y_pos, data.get('battery_life', 'N/A'))
    c.setFont("Helvetica", 11)

    # Segunda Fila
    y_pos -= 8 * mm
    c.drawString(x_col1_label, y_pos, "Color:")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_col1_value, y_pos, data.get('color', 'N/A'))
    c.setFont("Helvetica", 11)
    
    # --- SECCIÓN INFERIOR PARA SN / IMEI ---
    footer_y = y_start + 8 * mm
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_start + 8 * mm, footer_y, f"S/N: {data.get('serial', 'N/A')}")
    c.drawRightString(x_start + label_width - 8 * mm, footer_y, f"IMEI: {data.get('imei', 'N/A')}")

    c.restoreState()


def create_pdf(data, output_filename):
    c = canvas.Canvas(output_filename, pagesize=A4)
    draw_label(c, (A4[0] - 100 * mm) / 2, A4[1] - 80 * mm, data) # Etiqueta centrada en la parte superior
    c.save()

# --- RUTAS DE LA APLICACIÓN WEB (SIN CAMBIOS) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'No se envió ningún archivo.'}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.txt'): return jsonify({'error': 'Archivo no válido. Sube un .txt'}), 400
    
    unique_id = str(uuid.uuid4())
    txt_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}.txt")
    file.save(txt_filepath)

    device_data = parse_3utools_report(txt_filepath)
    if not device_data: return jsonify({'error': 'No se pudo procesar el archivo.'}), 500

    pdf_filename = f"etiqueta_{unique_id}.pdf"
    pdf_filepath = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
    create_pdf(device_data, pdf_filepath)

    preview_filename = f"preview_{unique_id}.png"
    preview_filepath = os.path.join(app.config['GENERATED_FOLDER'], preview_filename)
    try:
        images = convert_from_path(pdf_filepath, 300, first_page=1, last_page=1)
        if images: images[0].save(preview_filepath, 'PNG')
    except Exception as e:
        print(f"Error generando preview: {e}")
        return jsonify({'error': 'Error al generar la vista previa. Revisa que Poppler esté instalado.'}), 500

    return jsonify({'preview_url': f"/generated/{preview_filename}", 'pdf_url': f"/generated/{pdf_filename}"})

@app.route('/generated/<filename>')
def generated_file(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)