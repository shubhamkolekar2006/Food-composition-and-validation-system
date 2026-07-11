# Intelligent Food Composition & Validation System

> AI-powered Flask application for packaged food analysis, OCR-based
> nutrition extraction, ML health scoring, explainable AI insights, and
> Gemini-powered nutrition assistance.

## 🚀 Features

-   OCR nutrition label scanning (Tesseract.js)
-   Barcode-based product lookup
-   Machine Learning health score prediction
-   Nutrition validation against SQLite database
-   Explainable AI (feature contribution analysis)
-   Gemini AI nutrition assistant
-   Product comparison dashboard
-   Interactive charts using Chart.js

------------------------------------------------------------------------

# Tech Stack

  Layer      Technology
  ---------- ---------------------------------------
  Backend    Flask
  Database   SQLite + SQLAlchemy
  ML         Scikit-learn
  OCR        Tesseract.js
  AI         Google Gemini API
  Frontend   HTML, Bootstrap, JavaScript, Chart.js

------------------------------------------------------------------------

# Architecture

``` mermaid
graph TD

A[User]
B[Flask Application]
C[(SQLite Database)]
D[ML Model]
E[Gemini AI]
F[Dashboard]

A -->|OCR / Manual Entry| B
B -->|Read Product| C
B -->|Predict Score| D
B -->|AI Summary| E
B -->|Return Results| F
F --> A
```

------------------------------------------------------------------------

# Database ER Diagram

``` mermaid
erDiagram

PRODUCTS {
    int id PK
    string barcode
    string product_name
    string brand
    float calories
    float sugar
    float fat
    float saturated_fat
    float protein
    float fiber
    float sodium
    float health_score
}

SCAN_HISTORY {
    int id PK
    int product_id FK
    datetime scanned_at
    string status
}

VALIDATION_LOGS {
    int id PK
    int product_id FK
    string validation_type
    float confidence_score
    string status
}

PRODUCTS ||--o{ SCAN_HISTORY : stores
PRODUCTS ||--o{ VALIDATION_LOGS : validates
```

------------------------------------------------------------------------

# Data Flow

``` mermaid
sequenceDiagram

actor User
participant App
participant DB
participant ML
participant Gemini

User->>App: Scan barcode
App->>DB: Lookup product

alt Product Found
    DB-->>App: Nutrition values
else Not Found
    App->>App: Manual Input
end

App->>ML: Predict Score
ML-->>App: Health Score

App->>Gemini: Generate AI Summary
Gemini-->>App: Recommendation

App-->>User: Dashboard
```

------------------------------------------------------------------------

# Folder Structure

``` text
app/
├── routes/
├── services/
├── models/
├── templates/
├── static/
├── database/
├── config.py
├── __init__.py
scripts/
instance/
requirements.txt
app.py
```

------------------------------------------------------------------------

# ML Pipeline

1.  Collect nutrition data.
2.  Clean and preprocess.
3.  Predict using Random Forest Regressor.
4.  Explain feature contribution.
5.  Display dashboard.

------------------------------------------------------------------------

# Installation

``` bash
git clone https://github.com/shubhamkolekar2006/Food-composition-and-validation-system.git
cd Food-composition-and-validation-system
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

python app.py
```

------------------------------------------------------------------------

# Environment Variables

``` text
GEMINI_API_KEY=your_key
SECRET_KEY=your_secret
```

------------------------------------------------------------------------

# API

### POST /manual

Predict health score.

### POST /chat

Chat with nutrition assistant.

------------------------------------------------------------------------

# Future Improvements

-   Docker deployment
-   PostgreSQL support
-   User authentication
-   Cloud deployment
-   Recommendation engine

------------------------------------------------------------------------


