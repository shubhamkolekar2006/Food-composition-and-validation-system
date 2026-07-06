from datetime import datetime
from app.database import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    product_name = db.Column(db.String(255), nullable=True, index=True)
    brand = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    
    # Nutritional values per 100g
    calories = db.Column(db.Float, default=0.0)
    sugar = db.Column(db.Float, default=0.0)
    protein = db.Column(db.Float, default=0.0)
    fat = db.Column(db.Float, default=0.0)
    saturated_fat = db.Column(db.Float, default=0.0)
    fiber = db.Column(db.Float, default=0.0)
    sodium = db.Column(db.Float, default=0.0)  # in mg
    
    health_score = db.Column(db.Float, nullable=True)
    
    # Relationships
    scans = db.relationship('ScanHistory', backref='product', lazy=True)
    validation_logs = db.relationship('ValidationLog', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'barcode': self.barcode,
            'product_name': self.product_name,
            'brand': self.brand,
            'category': self.category,
            'ingredients': self.ingredients,
            'calories': self.calories,
            'sugar': self.sugar,
            'protein': self.protein,
            'fat': self.fat,
            'saturated_fat': self.saturated_fat,
            'fiber': self.fiber,
            'sodium': self.sodium,
            'health_score': self.health_score
        }

class ScanHistory(db.Model):
    __tablename__ = 'scan_history'
    
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(50), nullable=False, index=True)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False)  # 'found', 'not_found'

class ValidationLog(db.Model):
    __tablename__ = 'validation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, index=True)
    validation_type = db.Column(db.String(50), nullable=False)  # 'manual', 'ocr', 'barcode'
    confidence_score = db.Column(db.Float, default=100.0)
    status = db.Column(db.String(50), nullable=False)  # 'validated', 'warning', 'failed'
    details = db.Column(db.Text, nullable=True)  # JSON or text containing validation details
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ProductComparison(db.Model):
    __tablename__ = 'product_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    product_a_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_b_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    compared_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships for backref or manual access
    product_a = db.relationship('Product', foreign_keys=[product_a_id])
    product_b = db.relationship('Product', foreign_keys=[product_b_id])
