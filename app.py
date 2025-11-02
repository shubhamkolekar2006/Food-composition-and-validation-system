from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import joblib
import os
import pandas as pd

# Load the CSV file with product data
products_df = pd.read_csv("products.csv")
model = joblib.load("model.pkl")  # Load your trained model

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the database model for products
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float)
    sugar = db.Column(db.Float)
    fat = db.Column(db.Float)
    saturated_fat = db.Column(db.Float)
    proteins = db.Column(db.Float)
    fibers = db.Column(db.Float)
    sodium = db.Column(db.Float)
    health_score = db.Column(db.Float)

# Health feedback function based on the prediction score
def get_health_feedback(score):
    if score < 40:
        return "Poor nutritional quality"
    elif 40 <= score < 70:
        return "Moderate nutritional quality"
    else:
        return "Excellent nutritional quality"

@app.route('/')
def home():
    return render_template('index.html')  # Render your homepage

@app.route('/manual', methods=['GET', 'POST'])
def manual():
    if request.method == 'GET':
        return render_template('manual_entry.html')  # Or whatever your manual input template is
    
    # Ensure request is JSON
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 415
    
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'No data received'}), 400
            
        print(f"Data received: {data}")  # Debug logging

        # Validate required fields
        required_fields = ['calories', 'sugar', 'fat', 'saturated_fat', 'proteins', 'fibers', 'sodium']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Convert to floats and prepare features
        try:
            features = [
                float(data['calories']),
                float(data['sugar']),
                float(data['fat']),
                float(data['saturated_fat']),
                float(data['proteins']),
                float(data['fibers']),
                float(data['sodium'])
            ]
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid number format: {str(e)}'}), 400

        # Make prediction
        try:
            prediction = model.predict([features])[0]
            feedback = get_health_feedback(prediction)
        except Exception as e:
            return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

        # Save to database (optional)
        try:
            product = Product(
                name=data.get('name', 'Unknown Product'),
                calories=features[0],
                sugar=features[1],
                fat=features[2],
                saturated_fat=features[3],
                proteins=features[4],
                fibers=features[5],
                sodium=features[6],
                health_score=prediction
            )
            db.session.add(product)
            db.session.commit()
        except Exception as db_error:
            print(f"Database error (non-critical): {db_error}")
            # Continue even if DB fails - prediction is more important

        print(f"Prediction: {prediction}, Feedback: {feedback}")
        
        return jsonify({
            'score': prediction,
            'feedback': feedback
        })

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected server error occurred'}), 500



@app.route('/scan', methods=['GET', 'POST'])
def scan():
    message = None
    error = None

    if request.method == 'POST':
        barcode = request.form.get('barcode')
        print(f"Entered Barcode: {barcode}")

        # Convert the 'barcode' column to string to avoid AttributeError
        products_df['barcode'] = products_df['barcode'].astype(str)

        # Matching the barcode in the CSV (strip spaces and convert to lowercase)
        row = products_df[products_df['barcode'].str.strip().str.lower() == barcode.strip().lower()]
        print(f"Matching row found: {row}")

        if not row.empty:
            features = row[['calories', 'sugar', 'fat', 'saturated_fat', 'proteins', 'fibers', 'sodium']].values[0]
            prediction = model.predict([features])[0]
            feedback = get_health_feedback(prediction)
            message = f"Product: {row.iloc[0]['product_name']}<br>Health Score: {round(prediction, 2)}<br>Feedback: {feedback}"
        else:
            error = "Product not found in DATABASE."

    return render_template("scanner.html", message=message, error=error)


# @app.route('/result',methods=['GET'])
# def result():
#     score = request.args.get('score')
#     feedback = request.args.get('feedback')
#     return render_template('result.html', score=score, feedback=feedback)


if __name__ == '__main__':
    # ✅ Fix: Create DB inside app context
    with app.app_context():
        if not os.path.exists('products.db'):
            db.create_all()
    app.run(debug=True)
