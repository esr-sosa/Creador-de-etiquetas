// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error-message');
    const previewImage = document.getElementById('preview-image');
    const downloadBtn = document.getElementById('download-btn');

    // Abrir selector de archivos al hacer clic en el area
    form.addEventListener('click', () => {
        fileInput.click();
    });

    // Manejar el cambio del input de archivo
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    // Manejar Drag & Drop
    form.addEventListener('dragover', (e) => {
        e.preventDefault();
        form.classList.add('drag-over');
    });
    form.addEventListener('dragleave', () => {
        form.classList.remove('drag-over');
    });
    form.addEventListener('drop', (e) => {
        e.preventDefault();
        form.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFile(e.dataTransfer.files[0]);
        }
    });

    const handleFile = (file) => {
        // Ocultar resultados anteriores y mostrar carga
        form.style.display = 'none';
        errorDiv.style.display = 'none';
        resultDiv.style.display = 'none';
        loadingDiv.style.display = 'block';

        const formData = new FormData();
        formData.append('file', file);

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
            showError('Ocurrió un error inesperado. Revisa la consola del servidor.');
            console.error('Error:', error);
        });
    };

    const showError = (message) => {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        form.style.display = 'block'; // Mostrar el formulario de nuevo
    };
});
