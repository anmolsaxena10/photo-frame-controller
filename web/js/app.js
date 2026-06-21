document.addEventListener('DOMContentLoaded', () => {
    // ---- Navigation (unified for side-nav + bottom-nav) ----
    const allNavItems = document.querySelectorAll('.bottom-nav__item, .side-nav__item');
    const views = document.querySelectorAll('.view');

    function navigateTo(target) {
        allNavItems.forEach(n => n.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));

        // Activate matching nav items in both navs
        allNavItems.forEach(n => {
            if (n.dataset.target === target) n.classList.add('active');
        });
        document.getElementById(target).classList.add('active');

        // Load data when switching to views
        if (target === 'gallery-view') loadGallery();
        if (target === 'settings-view') loadSettings();
    }

    allNavItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(item.dataset.target);
        });
    });

    // ---- Upload & Cropper ----
    const fileInput = document.getElementById('file-input');
    const uploadZone = document.getElementById('upload-zone');
    const editorModal = document.getElementById('editor-modal');
    const modalScrim = editorModal.querySelector('.modal__scrim');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const imageToCrop = document.getElementById('image-to-crop');
    const btnRotate = document.getElementById('btn-rotate');
    const btnPreview = document.getElementById('btn-preview');
    const btnUpload = document.getElementById('btn-upload');
    const previewContainer = document.querySelector('.preview-container');
    const ditherCanvas = document.getElementById('dither-preview-canvas');
    const photoCounter = document.getElementById('photo-counter');

    let cropper = null;
    let currentFiles = [];
    let currentFileIndex = 0;
    let ditherWorker = new Worker('/js/dither-worker.js');

    // Drag & drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            currentFiles = Array.from(e.dataTransfer.files);
            currentFileIndex = 0;
            processNextFile();
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            currentFiles = Array.from(e.target.files);
            currentFileIndex = 0;
            processNextFile();
        }
    });

    function openModal() {
        editorModal.classList.remove('hidden');
    }

    function closeModal() {
        editorModal.classList.add('hidden');
        if (cropper) { cropper.destroy(); cropper = null; }
        fileInput.value = '';
        currentFiles = [];
        currentFileIndex = 0;
    }

    btnCloseModal.addEventListener('click', closeModal);
    modalScrim.addEventListener('click', closeModal);

    function processNextFile() {
        if (currentFileIndex >= currentFiles.length) {
            closeModal();
            return;
        }

        const file = currentFiles[currentFileIndex];
        const url = URL.createObjectURL(file);
        imageToCrop.src = url;

        // Show counter for multi-file uploads
        if (currentFiles.length > 1) {
            photoCounter.textContent = `(${currentFileIndex + 1} of ${currentFiles.length})`;
        } else {
            photoCounter.textContent = '';
        }

        previewContainer.classList.add('hidden');
        openModal();

        if (cropper) cropper.destroy();

        cropper = new Cropper(imageToCrop, {
            aspectRatio: 800 / 480,
            viewMode: 2,
            dragMode: 'move',
            autoCropArea: 1,
            cropBoxResizable: true,
            background: true,
            responsive: true,
            restore: true,
            center: true,
            highlight: false,
            cropBoxMovable: true,
            toggleDragModeOnDblclick: false,
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
            fillColor: '#000000',
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high'
        });

        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

        btnPreview.disabled = true;
        btnPreview.innerHTML = '<span class="material-symbols-rounded">hourglass_top</span>Processing...';

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

        btnPreview.disabled = false;
        btnPreview.innerHTML = '<span class="material-symbols-rounded">palette</span>Preview';
    };

    btnUpload.addEventListener('click', async () => {
        if (!cropper) return;

        if (previewContainer.classList.contains('hidden')) {
            btnPreview.click();
            return;
        }

        btnUpload.disabled = true;
        btnUpload.innerHTML = '<span class="material-symbols-rounded">cloud_upload</span>Uploading...';

        ditherCanvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('files', blob, currentFiles[currentFileIndex].name + '.png');
            formData.append('pre_processed', 'true');

            try {
                const res = await fetch('/api/photos/upload', { method: 'POST', body: formData });
                if (res.ok) {
                    currentFileIndex++;
                    processNextFile();
                } else {
                    alert('Upload failed. Please try again.');
                }
            } catch (e) {
                alert('Upload failed. Check your connection.');
            } finally {
                btnUpload.disabled = false;
                btnUpload.innerHTML = '<span class="material-symbols-rounded">cloud_upload</span>Upload';
            }
        }, 'image/png');
    });

    // ---- Gallery ----
    const galleryGrid = document.getElementById('gallery-grid');
    let deletePhotoId = null;

    async function loadGallery() {
        galleryGrid.innerHTML = `
            <div class="gallery-loading">
                <span class="material-symbols-rounded spin">progress_activity</span>
                <p>Loading photos...</p>
            </div>`;

        try {
            const res = await fetch('/api/photos');
            const data = await res.json();

            if (!data.photos || data.photos.length === 0) {
                galleryGrid.innerHTML = `
                    <div class="gallery-empty">
                        <span class="material-symbols-rounded gallery-empty__icon">photo_library</span>
                        <p>No photos uploaded yet</p>
                    </div>`;
                return;
            }

            galleryGrid.innerHTML = '';
            data.photos.forEach(photo => {
                const item = document.createElement('div');
                item.className = 'gallery-item';
                item.innerHTML = `
                    <img src="${photo.thumbnail_url || photo.full_url}" alt="Photo" loading="lazy">
                    <div class="gallery-item__overlay">
                        <button class="gallery-item__delete" data-id="${photo.id}" aria-label="Delete photo">
                            <span class="material-symbols-rounded">delete</span>
                        </button>
                    </div>`;
                galleryGrid.appendChild(item);
            });

            // Attach delete handlers
            galleryGrid.querySelectorAll('.gallery-item__delete').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deletePhotoId = btn.dataset.id;
                    document.getElementById('delete-modal').classList.remove('hidden');
                });
            });
        } catch (e) {
            galleryGrid.innerHTML = `
                <div class="gallery-empty">
                    <span class="material-symbols-rounded gallery-empty__icon">cloud_off</span>
                    <p>Could not load photos</p>
                </div>`;
        }
    }

    // Delete modal
    const deleteModal = document.getElementById('delete-modal');
    document.getElementById('btn-cancel-delete').addEventListener('click', () => {
        deleteModal.classList.add('hidden');
        deletePhotoId = null;
    });
    deleteModal.querySelector('.modal__scrim').addEventListener('click', () => {
        deleteModal.classList.add('hidden');
        deletePhotoId = null;
    });
    document.getElementById('btn-confirm-delete').addEventListener('click', async () => {
        if (!deletePhotoId) return;
        try {
            await fetch(`/api/photos/${deletePhotoId}`, { method: 'DELETE' });
        } catch (e) { /* silent */ }
        deleteModal.classList.add('hidden');
        deletePhotoId = null;
        loadGallery();
    });

    // ---- Settings ----
    const carouselEnabled = document.getElementById('carousel-enabled');
    const carouselMode = document.getElementById('carousel-mode');
    const refreshInterval = document.getElementById('refresh-interval');
    const versionLabel = document.getElementById('version-label');

    async function loadSettings() {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();

            carouselEnabled.checked = data.carousel.enabled;
            carouselMode.value = data.carousel.mode;
            refreshInterval.value = String(data.carousel.refresh_interval_minutes);
            versionLabel.textContent = `Version: v${data.ota.current_version}`;
        } catch (e) {
            // Settings might not be available yet
        }
    }

    async function saveCarouselSettings() {
        try {
            await fetch('/api/settings/carousel', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    enabled: carouselEnabled.checked,
                    mode: carouselMode.value,
                    refresh_interval_minutes: parseInt(refreshInterval.value, 10),
                })
            });
        } catch (e) { /* silent */ }
    }

    carouselEnabled.addEventListener('change', saveCarouselSettings);
    carouselMode.addEventListener('change', saveCarouselSettings);
    refreshInterval.addEventListener('change', saveCarouselSettings);

    // OTA
    const btnCheckUpdate = document.getElementById('btn-check-update');
    const otaStatus = document.getElementById('ota-status');

    btnCheckUpdate.addEventListener('click', async () => {
        otaStatus.innerText = 'Checking...';
        btnCheckUpdate.disabled = true;

        try {
            const res = await fetch('/api/system/ota/check', { method: 'POST' });
            const data = await res.json();
            if (data.update_available) {
                if (confirm(`Update available: v${data.current_version} → v${data.latest_version}\n\nUpdate and restart now?`)) {
                    otaStatus.innerText = 'Updating...';
                    await fetch('/api/system/ota/update', { method: 'POST' });
                    otaStatus.innerText = 'Restarting... reconnect shortly.';
                } else {
                    otaStatus.innerText = 'Update available';
                }
            } else {
                otaStatus.innerText = 'Up to date';
                versionLabel.textContent = `Version: v${data.current_version}`;
            }
        } catch (e) {
            otaStatus.innerText = 'Error checking updates';
        } finally {
            btnCheckUpdate.disabled = false;
        }
    });

    // Load settings on initial page load
    loadSettings();
});
