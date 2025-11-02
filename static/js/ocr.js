function startOCR() {
    document.getElementById('ocrInput').click();
}

document.getElementById('ocrInput').addEventListener('change', function() {
    alert('OCR scanning feature will come here!');
    // You will use Tesseract.js here (optional advanced step)
});
