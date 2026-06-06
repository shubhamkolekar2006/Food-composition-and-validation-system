# Food Composition and Validation System

A Flask-based web application that predicts the health score of food products using a trained machine learning model. The application features three distinct methods for food composition validation and health score calculation:

1. **Manual Entry:** Enter nutritional values manually through a clean web form.
2. **Barcode Scanning:** Scan product barcodes using your device's camera or enter barcodes manually to fetch matching items from the local database (`products.csv`).
3. **OCR Label Scanner (New):** Upload or capture a photo of any nutrition facts label. Client-side OCR extracts nutritional facts (Calories, Sugars, Fats, Saturated Fats, Proteins, Fibers, Sodium) instantly, pre-fills the verification form, and calculates the health score.

---

## Features

### 1. Manual Entry
- Input parameters: Calories, Sugar (g), Fat (g), Saturated Fat (g), Proteins (g), Fibers (g), Sodium (mg).
- Validates data formats and requirements.
- Generates an instant health score ($0 - 100$) and visual feedback category ("Poor", "Moderate", "Excellent").

### 2. Barcode Scanner
- Client-side camera barcode scanning using **QuaggaJS**.
- Automatically queries the local CSV database for matching barcodes.
- Generates a prediction and saves results to a SQLite database.

### 3. OCR Label Scanner
- Client-side Optical Character Recognition (OCR) using **Tesseract.js**.
- Automatic text parser scans the image for keywords (e.g., *Calories*, *Sugar*, *Saturated Fat*, *Sodium*, etc.).
- Converts *Salt* to *Sodium* automatically if sodium metrics are not explicitly declared on the package.
- Displays detected values in an editable form for verification before score submission.

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Pip (Python Package Manager)

### Steps
1. Clone the repository and navigate to the project directory:
   ```bash
   cd "Food-Composition and validation system"
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. Open your browser and go to:
   ```
   http://127.0.0.1:5000
   ```

---

## Technologies Used
- **Backend:** Flask, Flask-SQLAlchemy, SQLite, Pandas, Numpy, Scikit-learn, Joblib
- **Frontend:** HTML5, CSS3, JavaScript (ES6), JQuery, Bootstrap 4, FontAwesome 6
- **Scanner Libraries:** QuaggaJS (Barcode), Tesseract.js (OCR)
