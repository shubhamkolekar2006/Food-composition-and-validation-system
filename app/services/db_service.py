from app.database import db
from app.models import Product, ScanHistory, ValidationLog, ProductComparison
from sqlalchemy import func
import json

class DBService:
    # Thread-safe in-memory serialization caches
    _product_cache = {}
    _product_cache_by_id = {}
    
    @classmethod
    def get_product_by_barcode(cls, barcode):
        if not barcode:
            return None
        barcode_clean = barcode.strip()
        
        # Check cache
        if barcode_clean in cls._product_cache:
            return Product(**cls._product_cache[barcode_clean])
            
        prod = Product.query.filter(Product.barcode == barcode_clean).first()
        if prod:
            serialized = prod.to_dict()
            cls._product_cache[barcode_clean] = serialized
            cls._product_cache_by_id[prod.id] = serialized
        return prod
        
    @classmethod
    def get_product_by_id(cls, product_id):
        if not product_id:
            return None
            
        # Check cache
        if product_id in cls._product_cache_by_id:
            return Product(**cls._product_cache_by_id[product_id])
            
        prod = Product.query.get(product_id)
        if prod:
            serialized = prod.to_dict()
            cls._product_cache_by_id[prod.id] = serialized
            if prod.barcode:
                cls._product_cache[prod.barcode] = serialized
        return prod
        
    @classmethod
    def log_scan(cls, barcode, status, product_id=None):
        try:
            history = ScanHistory(
                barcode=barcode.strip(),
                status=status,
                product_id=product_id
            )
            db.session.add(history)
            db.session.commit()
            return history
        except Exception as e:
            db.session.rollback()
            print(f"Error logging scan session: {e}")
            return None
            
    @classmethod
    def log_validation(cls, product_id, validation_type, confidence_score, status, details):
        try:
            # Serialize details if it's a dict/list
            if isinstance(details, (dict, list)):
                details = json.dumps(details)
                
            log = ValidationLog(
                product_id=product_id,
                validation_type=validation_type,
                confidence_score=confidence_score,
                status=status,
                details=details
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            print(f"Error logging validation: {e}")
            return None
            
    @classmethod
    def save_manual_product(cls, name, calories, sugar, fat, saturated_fat, protein, fiber, sodium, health_score):
        try:
            import time
            pseudo_barcode = f"MAN-{int(time.time() * 1000)}"
            
            product = Product(
                barcode=pseudo_barcode,
                product_name=name.strip() if name else "Manual Entry Product",
                calories=calories,
                sugar=sugar,
                fat=fat,
                saturated_fat=saturated_fat,
                protein=protein,
                fiber=fiber,
                sodium=sodium,
                health_score=health_score
            )
            db.session.add(product)
            db.session.commit()
            
            # Clear or update caches after insert
            serialized = product.to_dict()
            cls._product_cache[pseudo_barcode] = serialized
            cls._product_cache_by_id[product.id] = serialized
            
            return product
        except Exception as e:
            db.session.rollback()
            print(f"Error saving manual product: {e}")
            return None

    @classmethod
    def log_comparison(cls, product_a_id, product_b_id, notes=None):
        try:
            comparison = ProductComparison(
                product_a_id=product_a_id,
                product_b_id=product_b_id,
                notes=notes
            )
            db.session.add(comparison)
            db.session.commit()
            return comparison
        except Exception as e:
            db.session.rollback()
            print(f"Error logging comparison: {e}")
            return None

    @classmethod
    def get_dashboard_statistics(cls):
        stats = {}
        
        # 1. Total products in Database
        stats['total_products'] = Product.query.count()
        
        # 2. Average health score
        avg_score = db.session.query(func.avg(Product.health_score)).scalar()
        stats['average_health_score'] = round(avg_score, 1) if avg_score is not None else 0.0
        
        # 3. Total scans count
        stats['total_scans'] = ScanHistory.query.count()
        
        # 4. Validation logs distribution
        validation_stats = db.session.query(
            ValidationLog.status, 
            func.count(ValidationLog.id)
        ).group_by(ValidationLog.status).all()
        
        val_map = {'validated': 0, 'warning': 0, 'failed': 0}
        for status, count in validation_stats:
            if status in val_map:
                val_map[status] = count
        stats['validation_distribution'] = val_map
        
        # 5. Top 5 scanned products
        top_scanned_query = db.session.query(
            Product.id,
            Product.product_name,
            Product.barcode,
            Product.brand,
            func.count(ScanHistory.id).label('scan_count')
        ).join(ScanHistory, Product.id == ScanHistory.product_id)\
         .group_by(Product.id)\
         .order_by(func.count(ScanHistory.id).desc())\
         .limit(5).all()
         
        stats['top_scanned_products'] = [
            {
                'id': row[0],
                'product_name': row[1],
                'barcode': row[2],
                'brand': row[3] or 'Generic',
                'scan_count': row[4]
            } for row in top_scanned_query
        ]
        
        # 6. Top scanned brands
        top_brands_query = db.session.query(
            Product.brand,
            func.count(ScanHistory.id).label('scan_count')
        ).join(ScanHistory, Product.id == ScanHistory.product_id)\
         .filter(Product.brand.isnot(None))\
         .group_by(Product.brand)\
         .order_by(func.count(ScanHistory.id).desc())\
         .limit(5).all()
         
        stats['top_scanned_brands'] = [
            {
                'brand': row[0],
                'scan_count': row[1]
            } for row in top_brands_query
        ]
        
        # 7. Recent Scans (last 10 scans)
        recent_scans = db.session.query(
            ScanHistory.scanned_at,
            ScanHistory.barcode,
            ScanHistory.status,
            Product.id,
            Product.product_name,
            Product.health_score
        ).outerjoin(Product, ScanHistory.product_id == Product.id)\
         .order_by(ScanHistory.scanned_at.desc())\
         .limit(10).all()
         
        stats['recent_scans'] = [
            {
                'scanned_at': row[0].strftime('%Y-%m-%d %H:%M:%S'),
                'barcode': row[1],
                'status': row[2],
                'product_id': row[3],
                'product_name': row[4] or 'Unknown Product',
                'health_score': round(row[5], 1) if row[5] is not None else None
            } for row in recent_scans
        ]
        
        # 8. Common warnings stats
        from app.services.warning_service import WarningService
        warning_counts = {}
        recent_products = Product.query.join(ScanHistory, Product.id == ScanHistory.product_id)\
            .order_by(ScanHistory.scanned_at.desc()).limit(30).all()
            
        for prod in recent_products:
            warnings = WarningService.detect_warnings(prod)
            for warn in warnings:
                title = warn['title']
                warning_counts[title] = warning_counts.get(title, 0) + 1
                
        stats['common_warnings'] = sorted(
            [{'title': k, 'count': v} for k, v in warning_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:5]
        
        # --- NEW OPTIMIZED DASHBOARD ANALYTICS ---
        # 9. Health Score Distribution (Histogram data)
        stats['health_score_distribution'] = {
            '0-20': Product.query.filter(Product.health_score >= 0, Product.health_score <= 20).count(),
            '21-40': Product.query.filter(Product.health_score > 20, Product.health_score <= 40).count(),
            '41-60': Product.query.filter(Product.health_score > 40, Product.health_score <= 60).count(),
            '61-80': Product.query.filter(Product.health_score > 60, Product.health_score <= 80).count(),
            '81-100': Product.query.filter(Product.health_score > 80, Product.health_score <= 100).count()
        }
        
        # 10. Validation Confidence Trends over last 15 checks
        recent_validations = ValidationLog.query.order_by(ValidationLog.logged_at.desc()).limit(15).all()
        stats['validation_trends'] = [
            {
                'date': val.logged_at.strftime('%m-%d %H:%M'),
                'score': val.confidence_score,
                'status': val.status
            } for val in reversed(recent_validations)
        ]
        
        # 11. Category Distributions (Top 5 categories + Other)
        cats_query = db.session.query(
            Product.category,
            func.count(Product.id)
        ).group_by(Product.category).order_by(func.count(Product.id).desc()).limit(5).all()
        
        cat_dist = {}
        for cat, cnt in cats_query:
            label = cat if cat else "Uncategorized"
            cat_dist[label] = cnt
        stats['category_distribution'] = cat_dist
        
        return stats
        
    @classmethod
    def get_all_products(cls):
        return Product.query.order_by(Product.product_name).all()

    @classmethod
    def get_similar_products(cls, product, limit=3):
        words = [w.strip().lower() for w in product.product_name.split() if len(w.strip()) > 3]
        query = Product.query.filter(Product.id != product.id)\
                             .filter(Product.health_score > product.health_score)
        
        if words:
            conditions = [Product.product_name.ilike(f"%{word}%") for word in words]
            import sqlalchemy
            query = query.filter(sqlalchemy.or_(*conditions))
            
        results = query.order_by(Product.health_score.desc()).limit(limit).all()
        
        if not results:
            results = Product.query.filter(Product.id != product.id)\
                                   .filter(Product.health_score > product.health_score)\
                                   .order_by(Product.health_score.desc())\
                                   .limit(limit).all()
        return results


