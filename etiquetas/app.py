# app.py - VERSIÓN FINAL HÍBRIDA (ARCHIVO + IMEI MANUAL)
import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from pdf2image import convert_from_path

# --- CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# --- FUNCIÓN DE PARSEO (TRADUCTOR) PRECISO PARA EL REPORTE ---
def parse_3utools_report(file_path):
    """
    Parsea el reporte de Verificación de 3uTools. Es específico para este formato.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        return None

    data = {
        'model': 'iPhone', # Valor predeterminado a 'iPhone' si no se encuentra el modelo exacto
        'color': 'N/A',
        'capacity': 'N/A',
        'serial': 'N/A',
        'battery_life': 'N/A',
        'imei': 'N/A'
    }

    # Modelo: Busca "iPhone 12" específicamente
    model_search = re.search(r"Device Model\s+(iPhone\s+\d+)", content)
    if model_search:
        data['model'] = model_search.group(1).strip()
    else: # Si no encuentra el "iPhone 12", se queda con "iPhone"
        pass

    # Color: Busca "(PRODUCT)RED" y lo traduce a "Rojo" o el color que aparezca
    color_search_red = re.search(r"Device Color\s+\(.*PRODUCT\)RED", content)
    if color_search_red:
        data['color'] = "Rojo"
    else:
        # Busca el patrón de color más genérico
        color_search = re.search(r"Device Color\s+([\w\s]+?)(?:£¬Rear[\w\s]+?)?\s+Normal", content)
        if color_search:
            extracted_color = color_search.group(1).strip()
            # Si el color es "Front Black", lo simplificamos a "Negro"
            if extracted_color == "Front Black":
                data['color'] = "Negro"
            else:
                data['color'] = extracted_color


    # Capacidad: Busca el patrón "XXGB"
    capacity_search = re.search(r"Hard Disk Capacity\s+(\d+GB)", content)
    if capacity_search:
        data['capacity'] = capacity_search.group(1)

    # Serial: Busca la cadena alfanumérica de 12 caracteres después de "Serial Number"
    serial_search = re.search(r"Serial Number\s+([A-Z0-9]{12})", content)
    if serial_search:
        data['serial'] = serial_search.group(1)

    # Batería: Busca el porcentaje exacto
    battery_search = re.search(r"Battery Life\s+(\d+%)", content)
    if battery_search:
        data['battery_life'] = battery_search.group(1)
        
    return data

from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

def draw_label(c, x_start, y_start, data):
    """
    Diseño final tipo Apple Swap con barcode de IMEI.
    """
    # Tamaño etiqueta más chico (realista)
    label_width, label_height = 70 * mm, 40 * mm
    primary_text, secondary_text, border_color = HexColor("#1c1c1e"), HexColor("#6e6e73"), HexColor("#d2d2d7")

    c.saveState()
    # Contenedor con bordes suaves
    c.setStrokeColor(border_color)
    c.setLineWidth(0.4)
    c.roundRect(x_start, y_start, label_width, label_height, 2 * mm, stroke=1, fill=0)

    # --- MODELO ---
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(primary_text)
    model_text = data.get('model', 'iPhone')
    c.drawString(x_start + 8 * mm, y_start + label_height - 10 * mm, model_text)

    # --- CAPACIDAD + COLOR ---
    c.setFont("Helvetica", 9)
    c.setFillColor(secondary_text)
    cap_col = f"{data.get('capacity', 'N/A')} · {data.get('color', 'N/A')}"
    c.drawString(x_start + 8 * mm, y_start + label_height - 15 * mm, cap_col)

    # --- LÍNEA DIVISORIA ---
    c.setStrokeColor(border_color)
    c.setLineWidth(0.3)
    c.line(x_start + 6 * mm, y_start + label_height - 18 * mm, x_start + label_width - 6 * mm, y_start + label_height - 18 * mm)

    # --- SALUD DE BATERÍA ---
    c.setFont("Helvetica", 9)
    c.setFillColor(secondary_text)
    c.drawString(x_start + 8 * mm, y_start + label_height - 23 * mm, "Salud de Batería")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(primary_text)
    c.drawString(x_start + 8 * mm, y_start + label_height - 28 * mm, data.get('battery_life', 'N/A'))

    # --- SERIE E IMEI ---
    footer_y = y_start + 8 * mm
    c.setFont("Helvetica", 8); c.setFillColor(secondary_text)
    c.drawString(x_start + 8 * mm, footer_y, "Serie")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(primary_text)
    c.drawString(x_start + 8 * mm, footer_y - 4 * mm, data.get('serial', 'N/A'))

    c.setFont("Helvetica", 8); c.setFillColor(secondary_text)
    c.drawRightString(x_start + label_width - 8 * mm, footer_y, "IMEI")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(primary_text)
    c.drawRightString(x_start + label_width - 8 * mm, footer_y - 4 * mm, data.get('imei', 'N/A'))

    # --- CÓDIGO DE BARRAS DEL IMEI ---
    imei_value = data.get('imei', '000000000000000')
    barcode = code128.Code128(imei_value, barHeight=8*mm, barWidth=0.3)
    # --- CÓDIGO DE BARRAS DEL IMEI ---
    imei_value = data.get('imei', '000000000000000')
    barcode = code128.Code128(imei_value, barHeight=8*mm, barWidth=0.3)
# Dibujar directo sobre el canvas (sin Drawing)
    barcode.drawOn(c, x_start + (label_width/2 - 25*mm), y_start + 2*mm)


    c.restoreState()





def create_pdf(data, output_filename):
    c = canvas.Canvas(output_filename, pagesize=A4)
    # Centramos la etiqueta en la página
    draw_label(c, (A4[0] - 100 * mm) / 2, A4[1] - 80 * mm, data)
    c.save()

# --- RUTAS DE LA APLICACIÓN WEB ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400
    
    file = request.files['file']
    imei_text = request.form.get('imei', '').strip()
    
    if file.filename == '': return jsonify({'error': 'No se seleccionó ningún archivo .txt.'}), 400
    if not imei_text: return jsonify({'error': 'El campo IMEI es obligatorio.'}), 400

    unique_id = str(uuid.uuid4())
    txt_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}.txt")
    file.save(txt_filepath)

    device_data = parse_3utools_report(txt_filepath)
    if not device_data or device_data['model'] == 'N/A':
        return jsonify({'error': 'No se pudo procesar el archivo. Sube un reporte válido.'}), 500

    # Añadimos el IMEI del formulario a los datos extraídos
    device_data['imei'] = imei_text

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

    return jsonify({'preview_url': f"/generated/{preview_filename}", 'pdf_url': f"/generated/{pdf_filename}"})


@app.route('/generated/<filename>')
def generated_file(filename): return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__': app.run(debug=True)