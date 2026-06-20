document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            
            e.target.classList.add('active');
            document.getElementById(e.target.dataset.target).classList.add('active');
        });
    });

    // Upload & Cropper variables
    const fileInput = document.getElementById('file-input');
    const editorModal = document.getElementById('editor-modal');
    const imageToCrop = document.getElementById('image-to-crop');
    const btnRotate = document.getElementById('btn-rotate');
    const btnPreview = document.getElementById('btn-preview');
    const btnUpload = document.getElementById('btn-upload');
    const previewContainer = document.querySelector('.preview-container');
    const ditherCanvas = document.getElementById('dither-preview-canvas');
    let cropper = null;
    let currentFiles = [];
    let currentFileIndex = 0;
    let ditherWorker = new Worker('/js/dither-worker.js');

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            currentFiles = Array.from(e.target.files);
            currentFileIndex = 0;
            processNextFile();
        }
    });

    function processNextFile() {
        if (currentFileIndex >= currentFiles.length) {
            editorModal.classList.add('hidden');
            fileInput.value = '';
            alert('All uploads complete!');
            return;
        }

        const file = currentFiles[currentFileIndex];
        const url = URL.createObjectURL(file);
        imageToCrop.src = url;
        
        previewContainer.classList.add('hidden');
        editorModal.classList.remove('hidden');

        if (cropper) {
            cropper.destroy();
        }

        cropper = new Cropper(imageToCrop, {
            aspectRatio: 800 / 480,
            viewMode: 1,
            dragMode: 'move',
            autoCropArea: 1,
            cropBoxResizable: true,
        });
    }

    btnRotate.addEventListener('click', () => {
        if (cropper) cropper.rotate(90);
    });

    btnPreview.addEventListener('click', () => {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({
            width: 800,
            height: 480,
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high'
        });
        
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        btnPreview.innerText = "Processing...";
        btnPreview.disabled = true;
        
        ditherWorker.postMessage({
            imageData: imageData,
            width: canvas.width,
            height: canvas.height
        });
    });

    ditherWorker.onmessage = function(e) {
        const processedImageData = e.data.processed;
        ditherCanvas.width = 800;
        ditherCanvas.height = 480;
        const ctx = ditherCanvas.getContext('2d');
        ctx.putImageData(processedImageData, 0, 0);
        previewContainer.classList.remove('hidden');
        
        btnPreview.innerText = "Dither Preview";
        btnPreview.disabled = false;
    };

    btnUpload.addEventListener('click', async () => {
        if (!cropper) return;
        
        if (previewContainer.classList.contains('hidden')) {
            alert("Please generate a Dither Preview first to confirm the quality.");
            return;
        }

        btnUpload.disabled = true;
        btnUpload.innerText = 'Uploading...';

        ditherCanvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('files', blob, currentFiles[currentFileIndex].name + ".png");
            formData.append('pre_processed', 'true');

            try {
                const res = await fetch('/api/photos/upload', {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    currentFileIndex++;
                    processNextFile();
                } else {
                    alert("Upload failed.");
                }
            } catch(e) {
                alert("Upload failed.");
            } finally {
                btnUpload.disabled = false;
                btnUpload.innerText = 'Confirm & Upload';
            }
        }, 'image/png');
    });

    // OTA Status Check
    const btnCheckUpdate = document.getElementById('btn-check-update');
    const otaStatus = document.getElementById('ota-status');

    btnCheckUpdate.addEventListener('click', async () => {
        otaStatus.innerText = "Checking...";
        try {
            const res = await fetch('/api/system/ota/check', { method: 'POST' });
            const data = await res.json();
            if (data.update_available) {
                if (confirm(`Update available! ${data.current_version} -> ${data.latest_version}. Update and restart now?`)) {
                    await fetch('/api/system/ota/update', { method: 'POST' });
                    alert("Update started. The frame will restart shortly. Please reconnect to the page.");
                }
            } else {
                otaStatus.innerText = `Up to date (v${data.current_version}).`;
            }
        } catch(e) {
            otaStatus.innerText = "Error checking for updates.";
        }
    });
});
