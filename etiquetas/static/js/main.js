// static/js/main.js - VERSIÓN CON MODO MANUAL
document.addEventListener('DOMContentLoaded', () => {
    // --- SECCIONES ---
    const modeSelection = document.getElementById('mode-selection');
    const uploadSection = document.getElementById('upload-section');
    const manualSection = document.getElementById('manual-section');
    const editSection = document.getElementById('edit-section');
    const resultSection = document.getElementById('result-section');

    // --- BOTONES DE MODO ---
    const modeAutoBtn = document.getElementById('mode-auto-btn');
    const modeManualBtn = document.getElementById('mode-manual-btn');

    // --- FORMULARIOS ---
    const uploadForm = document.getElementById('upload-form');
    const manualForm = document.getElementById('manual-form');
    const editForm = document.getElementById('edit-form');

    // --- CAMPOS DE EDICIÓN Y VISTA PREVIA ---
    const editFields = {
        model: document.getElementById('edit-model'),
        capacity: document.getElementById('edit-capacity'),
        color: document.getElementById('edit-color'),
        battery_life: document.getElementById('edit-battery'),
        imei: document.getElementById('edit-imei')
    };
    const livePreview = {
        model: document.getElementById('preview-model'),
        details: document.getElementById('preview-details'),
        battery: document.getElementById('preview-battery'),
        imei: document.getElementById('preview-imei'),
        logo: document.getElementById('preview-logo')
    };
    
    // --- OTROS ELEMENTOS ---
    const fileInput = document.getElementById('file-input');
    const initialImeiInput = document.getElementById('initial-imei-input');
    const uploadArea = document.getElementById('upload-area');
    const backBtn = document.getElementById('back-btn');
    const resetBtn = document.getElementById('reset-btn');
    const finalImage = document.getElementById('final-image');
    const downloadBtn = document.getElementById('download-btn');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-message');

    // --- DATOS PRE-CARGADOS PARA MODO MANUAL ---
    const models = ["iPhone 7", "iPhone 7 Plus", "iPhone 8", "iPhone 8 Plus", "iPhone X", "iPhone XR", "iPhone XS", "iPhone XS Max", "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max", "iPhone SE (2nd gen)", "iPhone 12", "iPhone 12 Mini", "iPhone 12 Pro", "iPhone 12 Pro Max", "iPhone 13", "iPhone 13 Mini", "iPhone 13 Pro", "iPhone 13 Pro Max", "iPhone SE (3rd gen)", "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max", "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max", "iPhone 16", "iPhone 16 Plus", "iPhone 16 Pro", "iPhone 16 Pro Max", "iPhone 17", "iPhone 17 Plus", "iPhone 17 Pro", "iPhone 17 Pro Max"];
    const capacities = ["32GB", "64GB", "128GB", "256GB", "512GB", "1TB"];
    const colors = ["Negro", "Blanco", "Rojo", "Verde", "Azul", "Rosa", "Púrpura", "Dorado", "Plateado", "Gris Espacial", "Blanco Estrella", "Negro Medianoche", "Titanio Natural", "Titanio Azul"];

    function populateSelect(selectId, options) {
        const select = document.getElementById(selectId);
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = opt.textContent = option;
            select.appendChild(opt);
        });
    }
    populateSelect('manual-model', models);
    populateSelect('manual-capacity', capacities);
    populateSelect('manual-color', colors);

    // --- MANEJO DE VISTAS ---
    modeAutoBtn.addEventListener('click', () => {
        modeSelection.style.display = 'none';
        uploadSection.style.display = 'block';
    });
    modeManualBtn.addEventListener('click', () => {
        modeSelection.style.display = 'none';
        manualSection.style.display = 'block';
    });

    // --- LÓGICA DE SUBIDA DE ARCHIVO (DRAG & DROP) ---
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => { if (fileInput.files.length > 0) uploadArea.querySelector('p').textContent = `Archivo: ${fileInput.files[0].name}`; });
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

    // --- PROCESO AUTOMÁTICO (PARSE) ---
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        const imei = initialImeiInput.value;
        if (!file || imei.trim() === "") {
            showError("Debes seleccionar un archivo .txt e ingresar el IMEI.");
            return;
        }
        const formData = new FormData();
        formData.append('file', file);
        showLoading(true);
        fetch('/parse', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                showLoading(false);
                if (data.error) {
                    showError(data.error);
                } else {
                    data.imei = imei; // Añadir el imei
                    showEditScreen(data);
                }
            }).catch(err => {
                showLoading(false);
                showError("Error de conexión al analizar el archivo.");
            });
    });

    // --- PROCESO MANUAL ---
    manualForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const manualData = {
            model: document.getElementById('manual-model').value,
            capacity: document.getElementById('manual-capacity').value,
            color: document.getElementById('manual-color').value,
            battery_life: document.getElementById('manual-battery').value,
            imei: document.getElementById('manual-imei').value
        };
        if (!manualData.imei || !manualData.battery_life) {
            showError("Los campos Batería e IMEI son obligatorios.");
            return;
        }
        showEditScreen(manualData);
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

    // --- PANTALLA DE EDICIÓN ---
    function showEditScreen(data) {
        uploadSection.style.display = 'none';
        manualSection.style.display = 'none';
        editSection.style.display = 'block';
        for (const key in editFields) {
            editFields[key].value = data[key] || '';
        }
        updateLivePreview();
    }
    
    // --- GENERACIÓN FINAL DE ETIQUETA ---
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
        .then(res => res.json())
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
        }).catch(err => {
            showLoading(false);
            showError("Error de conexión al generar la etiqueta.");
        });
    });

    // --- BOTONES PARA VOLVER Y REINICIAR ---
    function resetToStart() {
        modeSelection.style.display = 'block';
        uploadSection.style.display = 'none';
        manualSection.style.display = 'none';
        editSection.style.display = 'none';
        resultSection.style.display = 'none';
        errorDiv.style.display = 'none';
        // Limpiar formularios
        uploadForm.reset();
        manualForm.reset();
        editForm.reset();
        fileInput.value = '';
        uploadArea.querySelector('p').innerHTML = '<strong>Arrastra y suelta el reporte (.txt) aquí.</strong>';
    }
    backBtn.addEventListener('click', resetToStart);
    resetBtn.addEventListener('click', resetToStart);

    // --- FUNCIONES DE UTILIDAD ---
    function showLoading(isLoading) {
        errorDiv.style.display = 'none';
        loadingDiv.style.display = isLoading ? 'block' : 'none';
        if(isLoading) loadingDiv.innerHTML = '<div class="spinner"></div><p>Procesando...</p>';
    }
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
});