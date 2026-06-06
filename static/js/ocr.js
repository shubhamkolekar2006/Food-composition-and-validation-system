// OCR Parsing logic for Nutrition Facts Label
const OCRParser = {
    // Normalizes text and searches for nutritional value matches
    parseText: function(text) {
        const lines = text.split('\n');
        const results = {
            calories: null,
            sugar: null,
            fat: null,
            saturated_fat: null,
            proteins: null,
            fibers: null,
            sodium: null
        };

        console.log("Parsing nutrition facts from raw OCR text...");
        
        let saltGrams = null;

        lines.forEach(line => {
            // Remove extra whitespace, convert to lowercase
            const cleanLine = line.toLowerCase().replace(/\s+/g, ' ').trim();
            console.log("Analyzing line:", cleanLine);

            // Calories / Energy
            if (results.calories === null) {
                // Matches "calories 250", "energy: 100", "calories: 120kcal", etc.
                const match = cleanLine.match(/(?:calories|energy|cal|kcal)\D*(\d+)/i);
                if (match) {
                    results.calories = parseFloat(match[1]);
                }
            }

            // Total Fat
            if (results.fat === null) {
                // Matches "total fat 8g", "fat 12.5g", "lipides 5g"
                const match = cleanLine.match(/(?:total fat|fat|fats|lipides)\D*(\d+(?:\.\d+)?)\s*g/i);
                if (match) {
                    results.fat = parseFloat(match[1]);
                }
            }

            // Saturated Fat
            if (results.saturated_fat === null) {
                // Matches "saturated fat 1.5g", "saturated 3g", "dont acides gras satures 4g"
                const match = cleanLine.match(/(?:saturated fat|saturated|saturates|saturated fatty acids|gras saturés|gras satures)\D*(\d+(?:\.\d+)?)\s*g/i);
                if (match) {
                    results.saturated_fat = parseFloat(match[1]);
                }
            }

            // Sugar
            if (results.sugar === null) {
                // Matches "sugars 15g", "sugar 10g", "total sugars 5g", "dont sucres 2g"
                const match = cleanLine.match(/(?:sugar|sugars|total sugars|dont sucres|sucres)\D*(\d+(?:\.\d+)?)\s*g/i);
                if (match) {
                    results.sugar = parseFloat(match[1]);
                }
            }

            // Protein
            if (results.proteins === null) {
                // Matches "protein 8g", "proteins 4.5g", "protéines 10g"
                const match = cleanLine.match(/(?:protein|proteins|proteines|protéines)\D*(\d+(?:\.\d+)?)\s*g/i);
                if (match) {
                    results.proteins = parseFloat(match[1]);
                }
            }

            // Fiber
            if (results.fibers === null) {
                // Matches "dietary fiber 2g", "fiber 3g", "fibers 1g", "fibres 4g"
                const match = cleanLine.match(/(?:dietary fiber|fiber|fibers|fibres|fibres alimentaires)\D*(\d+(?:\.\d+)?)\s*g/i);
                if (match) {
                    results.fibers = parseFloat(match[1]);
                }
            }

            // Sodium / Salt
            if (results.sodium === null) {
                // Matches "sodium 150mg", "sodium 0.5g", etc.
                const match = cleanLine.match(/sodium\D*(\d+(?:\.\d+)?)\s*(mg|g|milligrams|grams)?/i);
                if (match) {
                    let val = parseFloat(match[1]);
                    let unit = match[2] || 'mg';
                    if (unit.toLowerCase() === 'g' || unit.toLowerCase() === 'grams') {
                        val = val * 1000; // convert g to mg
                    }
                    results.sodium = val;
                }
            }

            // Capture salt for sodium fallback
            if (saltGrams === null) {
                const match = cleanLine.match(/(?:salt|sel)\D*(\d+(?:\.\d+)?)\s*(?:g|grams)?/i);
                if (match) {
                    saltGrams = parseFloat(match[1]);
                }
            }
        });

        // Fallback: If sodium is missing but salt is present, convert salt to sodium (sodium mg = salt g * 400)
        if (results.sodium === null && saltGrams !== null) {
            results.sodium = Math.round(saltGrams * 400);
            console.log(`Sodium auto-calculated from salt: ${saltGrams}g salt -> ${results.sodium}mg sodium`);
        }

        return results;
    }
};

// Performs OCR using Tesseract.js
function performOCR(imageFile, progressCallback, successCallback, errorCallback) {
    if (typeof Tesseract === 'undefined') {
        errorCallback('Tesseract.js library is not loaded. Please check your internet connection.');
        return;
    }

    // Use Tesseract recognize API
    Tesseract.recognize(
        imageFile,
        'eng',
        {
            logger: m => {
                if (progressCallback && m && m.status) {
                    let pct = 0;
                    if (typeof m.progress === 'number') {
                        pct = Math.round(m.progress * 100);
                    }
                    
                    // Make status descriptions user-friendly
                    let friendlyStatus = 'Processing image...';
                    if (m.status === 'loading tesseract core') {
                        friendlyStatus = 'Loading OCR Core...';
                    } else if (m.status === 'initializing api') {
                        friendlyStatus = 'Initializing OCR Engine...';
                    } else if (m.status === 'recognizing text') {
                        friendlyStatus = `Analyzing nutrition facts... (${pct}%)`;
                    }
                    
                    progressCallback(friendlyStatus, pct);
                }
            }
        }
    ).then(({ data: { text } }) => {
        console.log("Raw OCR Extracted Text:\n", text);
        const parsedData = OCRParser.parseText(text);
        successCallback(parsedData, text);
    }).catch(err => {
        console.error("Tesseract Error:", err);
        errorCallback(err.message || err || 'Failed to analyze the image.');
    });
}

// Function to trigger file click (retains manual_entry.html structure)
function startOCR() {
    const input = document.getElementById('ocrInput');
    if (input) {
        input.click();
    }
}

// Event listener for manual entry integration
document.addEventListener('DOMContentLoaded', function() {
    const ocrInput = document.getElementById('ocrInput');
    if (ocrInput) {
        ocrInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            // Check if we are on the manual_entry page. If so, integrate autofill
            const manualForm = document.getElementById('manualForm');
            if (manualForm && window.location.pathname.includes('/manual')) {
                // Inject an OCR scanning status box in manual_entry.html dynamically if not present
                let statusBox = document.getElementById('ocr-status-box');
                if (!statusBox) {
                    statusBox = document.createElement('div');
                    statusBox.id = 'ocr-status-box';
                    statusBox.className = 'alert alert-info mt-3 animate__animated animate__fadeIn';
                    manualForm.parentNode.insertBefore(statusBox, manualForm);
                }
                
                statusBox.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="fas fa-spinner fa-spin mr-3 fa-lg"></i>
                        <div>
                            <strong id="ocr-status-text">Loading OCR Engine...</strong>
                            <div class="progress mt-1" style="height: 5px; width: 200px;">
                                <div id="ocr-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%;"></div>
                            </div>
                        </div>
                    </div>
                `;

                performOCR(
                    file,
                    function(status, pct) {
                        document.getElementById('ocr-status-text').innerText = status;
                        document.getElementById('ocr-progress-bar').style.width = pct + '%';
                    },
                    function(data, rawText) {
                        statusBox.className = 'alert alert-success mt-3 animate__animated animate__fadeIn';
                        statusBox.innerHTML = `
                            <div class="d-flex align-items-center justify-content-between">
                                <div>
                                    <i class="fas fa-check-circle mr-2 text-success fa-lg"></i>
                                    <strong>OCR Scan Complete!</strong> Nutritional values have been filled. Please verify and submit.
                                </div>
                                <button type="button" class="close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                            </div>
                        `;

                        // Autofill inputs
                        const mappings = {
                            calories: 'calories',
                            sugar: 'sugar',
                            fat: 'fat',
                            saturated_fat: 'saturated_fat',
                            proteins: 'proteins',
                            fibers: 'fibers',
                            sodium: 'sodium'
                        };

                        let foundCount = 0;
                        for (const key in mappings) {
                            const inputName = mappings[key];
                            const inputEl = document.querySelector(`input[name="${inputName}"]`);
                            if (inputEl) {
                                if (data[key] !== null) {
                                    inputEl.value = data[key];
                                    inputEl.classList.add('is-valid');
                                    setTimeout(() => inputEl.classList.remove('is-valid'), 3000);
                                    foundCount++;
                                } else {
                                    inputEl.value = ''; // Clear if not found so user fills it
                                }
                            }
                        }
                        
                        console.log(`Autofilled ${foundCount} fields successfully.`);
                    },
                    function(errMsg) {
                        statusBox.className = 'alert alert-danger mt-3 animate__animated animate__shakeX';
                        statusBox.innerHTML = `
                            <div class="d-flex align-items-center justify-content-between">
                                <div>
                                    <i class="fas fa-exclamation-triangle mr-2 text-danger"></i>
                                    <strong>OCR Scan Failed:</strong> ${errMsg}
                                </div>
                                <button type="button" class="close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                            </div>
                        `;
                    }
                );
            }
        });
    }
});
