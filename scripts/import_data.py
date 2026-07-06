import os
import sys
import pandas as pd
import joblib

# Add the parent directory to Python path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Product

def import_data(csv_path="products.csv", model_path=None):
    print("Initializing Flask App context...")
    app = create_app()
    
    with app.app_context():
        # Ensure database tables exist
        print("Creating database tables if they do not exist...")
        db.create_all()
        
        # Load machine learning model
        if model_path is None:
            model_path = os.path.join(app.config['BASE_DIR'], 'ml', 'model.pkl')
            
        print(f"Loading ML model from {model_path}...")
        if not os.path.exists(model_path):
            print(f"CRITICAL ERROR: Model file not found at {model_path}")
            sys.exit(1)
        
        model = joblib.load(model_path)
        
        # Load CSV
        print(f"Reading CSV dataset from {csv_path}...")
        if not os.path.exists(csv_path):
            print(f"ERROR: Dataset not found at {csv_path}")
            sys.exit(1)
            
        df = pd.read_csv(csv_path)
        print(f"Total rows in CSV: {len(df)}")
        
        # Cleaning dataset
        print("Cleaning dataset and preparing records...")
        
        # 1. Drop rows without barcode or product name
        df = df.dropna(subset=['barcode'])
        df = df[df['barcode'].astype(str).str.strip() != '']
        
        # 2. Parse numeric columns and fill NaNs
        numeric_cols = ['calories', 'sugar', 'fat', 'proteins', 'saturated_fat', 'fibers', 'sodium']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
        # 3. Handle string columns
        df['product_name'] = df['product_name'].fillna('Unknown Product').astype(str).str.strip()
        df['ingredients'] = df['ingredients'].fillna('').astype(str).str.strip()
        
        # Extract brand or category if possible, otherwise null
        # Some product names are "Brand - Product Name" or similar, we can do basic parsing
        brands = []
        categories = []
        for name in df['product_name']:
            if ' - ' in name:
                parts = name.split(' - ', 1)
                brands.append(parts[0].strip())
            else:
                brands.append(None)
            categories.append(None)
            
        df['brand'] = brands
        df['category'] = categories
        
        print("Dataset cleaned. Calculating health scores using ML model...")
        
        # Calculate health scores in batch
        features_list = df[['calories', 'sugar', 'fat', 'saturated_fat', 'proteins', 'fibers', 'sodium']].values
        df['health_score'] = model.predict(features_list)
        
        # Remove duplicate barcodes to enforce unique constraint
        df = df.drop_duplicates(subset=['barcode'])
        print(f"Cleaned records to import: {len(df)}")
        
        # Insert records into database
        print("Inserting records into the database. This may take a moment...")
        
        count = 0
        products_to_add = []
        
        for _, row in df.iterrows():
            # Check if product with this barcode already exists
            existing = Product.query.filter_by(barcode=str(row['barcode']).strip()).first()
            if existing:
                continue
                
            product = Product(
                barcode=str(row['barcode']).strip(),
                product_name=row['product_name'],
                brand=row['brand'],
                category=row['category'],
                ingredients=row['ingredients'],
                calories=float(row['calories']),
                sugar=float(row['sugar']),
                protein=float(row['proteins']),
                fat=float(row['fat']),
                saturated_fat=float(row['saturated_fat']),
                fiber=float(row['fibers']),
                sodium=float(row['sodium']),
                health_score=float(row['health_score'])
            )
            products_to_add.append(product)
            count += 1
            
            # Batch commits
            if len(products_to_add) >= 500:
                db.session.bulk_save_objects(products_to_add)
                db.session.commit()
                products_to_add = []
                print(f"Imported {count} records...")
                
        if products_to_add:
            db.session.bulk_save_objects(products_to_add)
            db.session.commit()
            
        print(f"Import complete! Total new products added: {count}")

if __name__ == '__main__':
    import_data()
