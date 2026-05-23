const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('results');
const originalImg = document.getElementById('original-img');
const segmentationImg = document.getElementById('segmentation-img');
const heatmapImg = document.getElementById('heatmap-img');
const predClass = document.getElementById('pred-class');
const predConf = document.getElementById('pred-conf');
const confFill = document.getElementById('confidence-fill');
const resetBtn = document.getElementById('reset-btn');
const detectionResult = document.getElementById('detection-result');
const clinicalSummary = document.getElementById('clinical-summary-text');

// Click to upload
dropZone.addEventListener('click', () => fileInput.click());

// Drag and drop events
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
});

dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    let dt = e.dataTransfer;
    let files = dt.files;
    if (files.length) {
        handleFiles(files[0]);
    }
}

fileInput.addEventListener('change', function() {
    if (this.files.length) {
        handleFiles(this.files[0]);
    }
});

function handleFiles(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file.');
        return;
    }

    // Show preview of original
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImg.src = e.target.result;
    }
    reader.readAsDataURL(file);

    // Switch UI state
    document.querySelector('.upload-section').classList.add('hidden');
    resultsSection.classList.add('hidden');
    loading.classList.remove('hidden');

    uploadFile(file);
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/predict', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert(data.error);
            resetUI();
            return;
        }
        
        // Update UI with results
        segmentationImg.src = data.segmentation_mask;
        heatmapImg.src = data.heatmap;
        predClass.textContent = data.class;
        predConf.textContent = data.confidence + '%';
        confFill.style.width = data.confidence + '%';
        detectionResult.textContent = data.detection_result;
        clinicalSummary.textContent = data.summary;
        
        loading.classList.add('hidden');
        resultsSection.classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('There was an error analyzing the image.');
        resetUI();
    });
}

resetBtn.addEventListener('click', resetUI);

function resetUI() {
    fileInput.value = '';
    document.querySelector('.upload-section').classList.remove('hidden');
    resultsSection.classList.add('hidden');
    loading.classList.add('hidden');
    originalImg.src = '';
    segmentationImg.src = '';
    heatmapImg.src = '';
}
