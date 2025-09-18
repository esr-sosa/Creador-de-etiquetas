# app.py - VERSIÓN FINAL CON AJUSTE DE FUENTE DINÁMICO
import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from io import BytesIO

# LIBRERÍAS PARA DIBUJO Y CONVERSIÓN
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pdf2image import convert_from_bytes
from PIL import Image

# --- CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# --- CONFIGURACIÓN DE DISEÑO ---
LOGO_PATH = 'logo.png'
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    EMOJI_FONT = 'DejaVuSans'
except:
    print("ADVERTENCIA: No se encontró la fuente DejaVuSans.ttf.")
    EMOJI_FONT = 'Helvetica'

if not os.path.exists(LOGO_PATH):
    print(f"ADVERTENCIA: No se encontró el archivo de logo en {LOGO_PATH}.")
    LOGO_PATH = None

# --- MAPEO DE COLORES ---
COLOR_MAPPING = {
    "red": "Rojo", "black": "Negro", "green": "Verde", "blue": "Azul",
    "white": "Blanco", "starlight": "Blanco Estrella", "midnight": "Negro Medianoche",
    "pink": "Rosa", "purple": "Púrpura", "gold": "Dorado", "silver": "Plateado",
    "space gray": "Gris Espacial", "sierra blue": "Azul Sierra", "alpine green": "Verde Alpino",
    "graphite": "Grafito", "natural": "Titanio Natural", "titanium": "Titanio"
}

# --- FUNCIÓN DE PARSEO ---
def parse_3utools_report(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
    except FileNotFoundError: return None
    data = {'model': 'N/A', 'color': 'N/A', 'capacity': 'N/A', 'battery_life': 'N/A'}

    model_search = re.search(r"Device Model\s+(iPhone\s+\d+\s*(?:Plus|Pro|Max|Mini|SE)?)", content)
    if model_search: data['model'] = model_search.group(1).strip()

    color_line_search = re.search(r"Device Color\s+(.*)", content)
    if color_line_search:
        full_line = color_line_search.group(1)
        rear_color_search = re.search(r"Rear\s+([\w\s()]+)", full_line, re.IGNORECASE)
        if rear_color_search:
            extracted_color = rear_color_search.group(1).strip().lower()
            for key, value in COLOR_MAPPING.items():
                if key in extracted_color:
                    data['color'] = value
                    break
            if data['color'] == 'N/A': data['color'] = extracted_color.title()
        else:
            data['color'] = full_line.split('Normal')[0].strip()

    capacity_search = re.search(r"Hard Disk Capacity\s+(\d+GB)", content)
    if capacity_search: data['capacity'] = capacity_search.group(1).strip()
    
    battery_search = re.search(r"Battery Life\s+(\d+%)", content)
    if battery_search: data['battery_life'] = battery_search.group(1).strip()
    
    return data

# --- FUNCIÓN DE DIBUJO (CON LÓGICA DE FUENTE DINÁMICA) ---
def draw_label(c, x_start, y_start, data):
    label_width, label_height = 70 * mm, 40 * mm
    print_margin = 1.5 * mm
    
    draw_area_x = x_start + print_margin
    draw_area_y = y_start + print_margin
    draw_area_width = label_width - (2 * print_margin)
    draw_area_height = label_height - (2 * print_margin)
    
    text_color, subtle_text_color, border_color = colors.black, colors.HexColor("#4A4A4A"), colors.HexColor("#D8D8D8")
    font_bold, font_regular = "Helvetica-Bold", "Helvetica"
    margin = 5 * mm
    
    c.saveState()
    c.setStrokeColor(border_color)
    c.setLineWidth(0.5)
    c.roundRect(draw_area_x, draw_area_y, draw_area_width, draw_area_height, 2 * mm, stroke=1, fill=0)
    
    top_section_y = draw_area_y + draw_area_height - margin - 5*mm
    if LOGO_PATH:
        logo = ImageReader(LOGO_PATH)
        logo_w, logo_h = logo.getSize()
        aspect = logo_h / float(logo_w)
        logo_width_final = 20 * mm
        logo_height_final = logo_width_final * aspect
        c.drawImage(logo, draw_area_x + draw_area_width - logo_width_final - margin, top_section_y - logo_height_final/1.5,
                    width=logo_width_final, height=logo_height_final, mask='auto', preserveAspectRatio=True)
    
    # --- AJUSTE CLAVE: LÓGICA PARA EL TAMAÑO DE LA FUENTE ---
    model_text = data.get('model', '')
    model_font_size = 18  # Tamaño por defecto
    if 'Pro' in model_text or 'Max' in model_text or 'Plus' in model_text:
        model_font_size = 15  # Tamaño más chico para modelos con nombres largos

    c.setFont(font_bold, model_font_size)
    c.setFillColor(text_color)
    c.drawString(draw_area_x + margin, top_section_y, model_text)
    
    c.setFont(font_regular, 10)
    c.setFillColor(subtle_text_color)
    c.drawString(draw_area_x + margin, top_section_y - 6*mm, f"{data.get('capacity', '')} · {data.get('color', '')}")
    
    line_y = draw_area_y + 19 * mm - print_margin
    c.setStrokeColor(border_color)
    c.setLineWidth(0.5)
    c.line(draw_area_x + margin, line_y, draw_area_x + draw_area_width - margin, line_y)
    
    bottom_title_y = draw_area_y + margin + 7*mm
    bottom_data_y = draw_area_y + margin + 2*mm
    
    c.setFont(font_regular, 8)
    c.setFillColor(subtle_text_color)
    c.drawString(draw_area_x + margin, bottom_title_y, "Salud de Batería")
    c.setFont(font_bold, 12)
    c.setFillColor(text_color)
    c.drawString(draw_area_x + margin, bottom_data_y, data.get('battery_life', ''))
    
    c.setFont(font_regular, 8)
    c.setFillColor(subtle_text_color)
    c.drawRightString(draw_area_x + draw_area_width - margin, bottom_title_y, "IMEI")
    c.setFont(font_bold, 12)
    c.setFillColor(text_color)
    c.drawRightString(draw_area_x + draw_area_width - margin, bottom_data_y, data.get('imei', ''))
    
    c.setFont(EMOJI_FONT, 7)
    c.setFillColor(colors.HexColor("#008A00"))
    c.drawCentredString(draw_area_x + draw_area_width/2, draw_area_y + margin - 2*mm, "✅ Piezas Verificadas · Funciona Perfectamente")
    
    c.restoreState()

# --- FUNCIÓN DE CREACIÓN Y ROTACIÓN DE IMAGEN ---
def create_image_from_pdf(data, output_filepath):
    buffer = BytesIO()
    canvas_width, canvas_height = 70 * mm, 40 * mm
    c = canvas.Canvas(buffer, pagesize=(canvas_width, canvas_height))
    draw_label(c, 0, 0, data)
    c.save()
    buffer.seek(0)
    
    images = convert_from_bytes(buffer.read(), dpi=300)
    if images:
        images[0].save(output_filepath, 'PNG')
        with Image.open(output_filepath) as img:
            rotated_img = img.rotate(90, expand=True, fillcolor='white')
            rotated_img.save(output_filepath)

# --- RUTAS DE LA APLICACIÓN WEB ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse_file():
    if 'file' not in request.files: return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'Nombre de archivo vacío.'}), 400
    
    unique_id = str(uuid.uuid4())
    txt_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}.txt")
    file.save(txt_filepath)

    device_data = parse_3utools_report(txt_filepath)
    os.remove(txt_filepath)
    
    if not device_data: return jsonify({'error': 'No se pudo procesar el reporte.'}), 500
    return jsonify(device_data)

@app.route('/generate', methods=['POST'])
def generate_image():
    data = request.json
    if not data: return jsonify({'error': 'No se recibieron datos para generar la etiqueta.'}), 400
        
    unique_id = str(uuid.uuid4())
    image_filename = f"etiqueta_{unique_id}.png"
    image_filepath = os.path.join(app.config['GENERATED_FOLDER'], image_filename)
    
    try:
        create_image_from_pdf(data, image_filepath)
    except Exception as e:
        print(f"Error generando la imagen: {e}")
        return jsonify({'error': 'Ocurrió un error al crear la etiqueta.'}), 500

    return jsonify({'image_url': f"/generated/{image_filename}"})

@app.route('/generated/<filename>')
def generated_file(filename): return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__': app.run(debug=True)