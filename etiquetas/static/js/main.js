// static/js/main.js - VERSIÓN CORREGIDA
document.addEventListener('DOMContentLoaded', () => {
    // Secciones principales
    const uploadSection = document.getElementById('upload-section');
    const editSection = document.getElementById('edit-section');
    const resultSection = document.getElementById('result-section');

    // Formularios y botones
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const initialImeiInput = document.getElementById('initial-imei-input');
    const uploadArea = document.getElementById('upload-area');
    
    const editForm = document.getElementById('edit-form');
    const cancelBtn = document.getElementById('cancel-btn');
    const resetBtn = document.getElementById('reset-btn');
    
    // Campos de edición
    const editFields = {
        model: document.getElementById('edit-model'),
        capacity: document.getElementById('edit-capacity'),
        color: document.getElementById('edit-color'),
        battery_life: document.getElementById('edit-battery'),
        imei: document.getElementById('edit-imei')
    };

    // Elementos de la vista previa en vivo
    const livePreview = {
        model: document.getElementById('preview-model'),
        details: document.getElementById('preview-details'),
        battery: document.getElementById('preview-battery'),
        imei: document.getElementById('preview-imei'),
        logo: document.getElementById('preview-logo')
    };

    // Elementos del resultado final
    const finalImage = document.getElementById('final-image');
    const downloadBtn = document.getElementById('download-btn');

    // Utilidades
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-message');

    // --- LÓGICA DE SUBIDA DE ARCHIVO (DRAG & DROP) ---
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadArea.querySelector('p').textContent = `Archivo: ${fileInput.files[0].name}`;
        }
    });
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            uploadArea.querySelector('p').textContent = `Archivo: ${fileInput.files[0].name}`;
        }
    });
    
    // --- MANEJO DEL PASO 1: PARSEAR EL ARCHIVO ---
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        const imei = initialImeiInput.value;

        if (!file) { showError("Por favor, selecciona un archivo .txt."); return; }
        if (imei.trim() === "") { showError("Por favor, introduce el IMEI."); return; }

        const formData = new FormData();
        formData.append('file', file);
        
        showLoading(true);
        fetch('/parse', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                showLoading(false);
                if (data.error) {
                    showError(data.error);
                } else {
                    editFields.model.value = data.model || '';
                    editFields.capacity.value = data.capacity || '';
                    editFields.color.value = data.color || '';
                    editFields.battery_life.value = data.battery_life || '';
                    editFields.imei.value = imei; 
                    updateLivePreview();
                    uploadSection.style.display = 'none';
                    editSection.style.display = 'block';
                }
            })
            .catch(error => {
                showLoading(false);
                showError('Ocurrió un error al procesar el archivo.');
                console.error('Error:', error);
            });
    });
    
    // --- LÓGICA DE VISTA PREVIA EN VIVO ---
    function updateLivePreview() {
        livePreview.model.textContent = editFields.model.value;
        livePreview.details.textContent = `${editFields.capacity.value} · ${editFields.color.value}`;
        livePreview.battery.textContent = editFields.battery_life.value;
        livePreview.imei.textContent = editFields.imei.value;
        livePreview.logo.style.backgroundImage = 'url(/static/logo.png)';
    }

    Object.values(editFields).forEach(field => {
        field.addEventListener('input', updateLivePreview);
    });

    // --- MANEJO DEL PASO 2: GENERAR LA IMAGEN FINAL ---
    editForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const finalData = {};
        for (const key in editFields) {
            finalData[key] = editFields[key].value;
        }

        showLoading(true);
        fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(finalData)
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            if (data.error) {
                showError(data.error);
            } else {
                finalImage.src = data.image_url;
                downloadBtn.href = data.image_url;
                editSection.style.display = 'none';
                resultSection.style.display = 'block';
            }
        })
        .catch(error => {
            showLoading(false);
            showError('Ocurrió un error al generar la etiqueta final.');
            console.error('Error:', error);
        });
    });

    // --- MANEJO DE BOTONES DE CANCELAR Y REINICIAR ---
    function resetToStart() {
        uploadSection.style.display = 'block';
        editSection.style.display = 'none';
        resultSection.style.display = 'none';
        errorDiv.style.display = 'none';
        uploadForm.reset();
        editForm.reset();
        initialImeiInput.value = '';
        fileInput.value = ''; // Limpiar el archivo seleccionado
        uploadArea.querySelector('p').innerHTML = '<strong>Arrastra y suelta el reporte (.txt) aquí.</strong>';
    }
    
    cancelBtn.addEventListener('click', resetToStart);
    resetBtn.addEventListener('click', resetToStart);

    // --- FUNCIONES DE UTILIDAD ---
    function showLoading(isLoading) {
        errorDiv.style.display = 'none';
        loadingDiv.style.display = isLoading ? 'block' : 'none';
    }
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
});