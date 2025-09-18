// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const imeiInput = document.getElementById('imei-input');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error-message');
    const previewImage = document.getElementById('preview-image');
    const downloadBtn = document.getElementById('download-btn');

    // Abrir selector de archivos al hacer clic en el area
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadArea.querySelector('p').textContent = `Archivo seleccionado: ${fileInput.files[0].name}`;
        }
    });

    // Manejar Drag & Drop
    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
    uploadArea.addEventListener('dragleave', () => { uploadArea.classList.remove('drag-over'); });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            uploadArea.querySelector('p').textContent = `Archivo seleccionado: ${fileInput.files[0].name}`;
        }
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const file = fileInput.files[0];
        const imei = imeiInput.value;

        if (!file) {
            showError("Por favor, selecciona un archivo .txt.");
            return;
        }
        if (imei.trim() === "") {
            showError("Por favor, introduce el IMEI.");
            return;
        }

        handleUpload(file, imei);
    });

    const handleUpload = (file, imei) => {
        form.style.display = 'none';
        errorDiv.style.display = 'none';
        resultDiv.style.display = 'none';
        loadingDiv.style.display = 'block';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('imei', imei);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingDiv.style.display = 'none';
            if (data.error) {
                showError(data.error);
            } else {
                previewImage.src = data.preview_url;
                downloadBtn.href = data.pdf_url;
                resultDiv.style.display = 'block';
            }
        })
        .catch(error => {
            loadingDiv.style.display = 'none';
            showError('Ocurrió un error inesperado.');
            console.error('Error:', error);
        });
    };

    const showError = (message) => {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        form.style.display = 'block';
    };
});