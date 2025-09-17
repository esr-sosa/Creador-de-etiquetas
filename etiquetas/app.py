# app.py
import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from pdf2image import convert_from_path

# --- CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB max file size

# --- Asegurarse de que las carpetas existan ---
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# --- (Copiamos y adaptamos las funciones del script anterior) ---

def parse_3utools_report(file_path):
    # ... (La misma función de parseo que ya teníamos)
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None
    data = {'model': 'N/A', 'color': 'N/A', 'capacity': 'N/A', 'serial': 'N/A', 'battery_life': 'N/A', 'ios_version': 'N/A'}
    for i, line in enumerate(lines):
        line = line.strip()
        if "Device Model" in line and i + 2 < len(lines):
            model_line = lines[i+2].strip()
            if model_line: data['model'] = model_line.split()[0]
        if line.startswith("Device Color"):
            color_text = line.replace("Device Color", "").strip()
            if not color_text and i + 2 < len(lines):
                color_text = lines[i+2].strip().split("Normal")[0].strip()
            data['color'] = color_text
        if line.startswith("Hard Disk Capacity"):
            if i + 2 < len(lines):
                capacity_line = lines[i+2].strip()
                match = re.search(r'(\d+GB)', capacity_line)
                if match: data['capacity'] = match.group(1)
        if line.startswith("Serial Number") and i + 2 < len(lines):
            serial_line = lines[i+2].strip()
            if serial_line: data['serial'] = serial_line.split()[0]
        match_battery = re.search(r'Battery Life\s*(\d+%)', line)
        if match_battery: data['battery_life'] = match_battery.group(1)
        if line.startswith("iOS Version"):
            match_ios = re.search(r'iOS Version\s*([\d\.]+)', line)
            if match_ios: data['ios_version'] = match_ios.group(1)
    data['color'] = data['color'].replace("Front Black，Rear", "").replace("(PRODUCT)RED", "Rojo").strip()
    return data

def draw_label(c, x_start, y_start, data):
    # ... (La misma función de dibujo que ya teníamos)
    label_width, label_height = 85 * mm, 50 * mm
    primary_color, secondary_color, border_color = HexColor("#1A1A1A"), HexColor("#666666"), HexColor("#E0E0E0")
    c.saveState()
    c.setStrokeColor(border_color); c.setLineWidth(1); c.roundRect(x_start, y_start, label_width, label_height, 4 * mm)
    qr_code = qr.QrCodeWidget(f"https://wa.me/TUNUMERO?text=Hola,%20me%20interesa%20el%20equipo%20SN:%20{data.get('serial', '')}", barLevel='H')
    bounds = qr_code.getBounds(); width = bounds[2] - bounds[0]; height = bounds[3] - bounds[1]
    qr_size = 32 * mm; d = Drawing(qr_size, qr_size, transform=[qr_size/width, 0, 0, qr_size/height, 0, 0]); d.add(qr_code)
    qr_x = x_start + label_width - qr_size - 6 * mm; qr_y = y_start + (label_height - qr_size) / 2
    renderPDF.draw(d, c, qr_x, qr_y)
    text_x = x_start + 8 * mm
    c.setFont("Helvetica-Bold", 16); c.setFillColor(primary_color); c.drawString(text_x, y_start + label_height - 12 * mm, data.get('model', 'N/A'))
    c.setStrokeColor(border_color); c.line(text_x, y_start + label_height - 15 * mm, x_start + 45 * mm, y_start + label_height - 15 * mm)
    c.setFont("Helvetica", 9); c.setFillColor(secondary_color)
    y_offset = y_start + label_height - 22 * mm; line_gap = 5 * mm
    c.drawString(text_x, y_offset, f"💾 Capacidad: {data.get('capacity', 'N/A')}"); y_offset -= line_gap
    c.drawString(text_x, y_offset, f"🎨 Color: {data.get('color', 'N/A')}"); y_offset -= line_gap
    c.drawString(text_x, y_offset, f"🔋 Batería: {data.get('battery_life', 'N/A')}")
    c.setFont("Helvetica", 7); c.setFillColor(secondary_color); c.drawString(text_x, y_start + 8 * mm, f"SN: {data.get('serial', 'N/A')}")
    c.setFont("Helvetica-Oblique", 7); c.drawRightString(x_start + label_width - 8 * mm, y_start + 8 * mm, "EmaTecno")
    c.restoreState()

def create_pdf(data, output_filename):
    c = canvas.Canvas(output_filename, pagesize=A4)
    draw_label(c, 20 * mm, A4[1] - 70 * mm, data)
    c.save()

# --- RUTAS DE LA APLICACIÓN WEB ---

@app.route('/')
def index():
    """ Muestra la página principal de carga de archivos. """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """ Procesa el archivo TXT subido y genera los archivos de salida. """
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400
    if file and file.filename.endswith('.txt'):
        # Guardar el archivo subido con un nombre único
        unique_id = str(uuid.uuid4())
        txt_filename = f"{unique_id}.txt"
        txt_filepath = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
        file.save(txt_filepath)

        # Procesar el archivo
        device_data = parse_3utools_report(txt_filepath)
        if not device_data:
            return jsonify({'error': 'No se pudo procesar el archivo de 3uTools.'}), 500

        # Generar el PDF
        pdf_filename = f"etiqueta_{unique_id}.pdf"
        pdf_filepath = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
        create_pdf(device_data, pdf_filepath)

        # Generar la imagen de preview desde el PDF
        preview_filename = f"preview_{unique_id}.png"
        preview_filepath = os.path.join(app.config['GENERATED_FOLDER'], preview_filename)
        try:
            images = convert_from_path(pdf_filepath, 300, first_page=1, last_page=1)
            if images:
                images[0].save(preview_filepath, 'PNG')
        except Exception as e:
            # Si pdf2image falla, devolver un error claro
            print(f"Error generando preview: {e}")
            return jsonify({'error': 'Error al generar la vista previa. Asegúrate que Poppler esté instalado.'}), 500

        # Devolver las URLs de los archivos generados
        return jsonify({
            'preview_url': f"/generated/{preview_filename}",
            'pdf_url': f"/generated/{pdf_filename}"
        })

    return jsonify({'error': 'Formato de archivo no válido. Sube un .txt'}), 400

@app.route('/generated/<filename>')
def generated_file(filename):
    """ Sirve los archivos generados (PDF e imágenes). """
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)