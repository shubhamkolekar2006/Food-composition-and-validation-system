class ValidationService:
    # Importance weights for calculating discrepancies (must sum to 1.0)
    WEIGHTS = {
        'calories': 0.05,
        'sugar': 0.25,
        'fat': 0.15,
        'saturated_fat': 0.20,
        'proteins': 0.15,
        'fibers': 0.10,
        'sodium': 0.10
    }
    
    @classmethod
    def validate_ocr_vs_database(cls, ocr_data, db_product):
        """
        Compares OCR extracted nutritional values against the official database specs.
        ocr_data: dict of float values
        db_product: Product model instance
        """
        discrepancies = {}
        weighted_error = 0.0
        
        # Mappings from ocr keys to database field names
        fields = {
            'calories': db_product.calories,
            'sugar': db_product.sugar,
            'fat': db_product.fat,
            'saturated_fat': db_product.saturated_fat,
            'proteins': db_product.protein,
            'fibers': db_product.fiber,
            'sodium': db_product.sodium
        }
        
        for key, db_val in fields.items():
            ocr_val = ocr_data.get(key)
            
            # If not detected by OCR, we flag it as not scanned, but don't heavily penalize it
            if ocr_val is None:
                discrepancies[key] = {
                    'ocr_value': None,
                    'db_value': db_val,
                    'diff_percent': 0.0,
                    'status': 'not_detected'
                }
                continue
                
            # Percentage difference calculation
            db_val = float(db_val)
            ocr_val = float(ocr_val)
            
            denominator = max(db_val, 1.0) # Avoid division by zero
            diff_percent = (abs(ocr_val - db_val) / denominator) * 100.0
            
            # Penalize discrepancy based on weight
            weighted_error += cls.WEIGHTS[key] * diff_percent
            
            # Status check for this specific nutrient
            if diff_percent < 5.0:
                status = 'match'
            elif diff_percent < 15.0:
                status = 'minor_discrepancy'
            else:
                status = 'major_discrepancy'
                
            discrepancies[key] = {
                'ocr_value': ocr_val,
                'db_value': db_val,
                'diff_percent': round(diff_percent, 2),
                'status': status
            }
            
        # Calculate Validation Confidence Score
        # Confidence decays as weighted error increases
        confidence_score = max(0.0, 100.0 - weighted_error)
        
        # Determine Overall Validation Status
        if confidence_score >= 90.0:
            status = 'validated'
            details = "All scanned values match the database specifications within tolerance limits."
        elif confidence_score >= 70.0:
            status = 'warning'
            details = "Minor nutritional differences detected. Packaging information might have updated."
        else:
            status = 'failed'
            details = "Significant nutritional discrepancies detected. Please verify package authenticity!"
            
        return {
            'confidence_score': round(confidence_score, 2),
            'status': status,
            'details': details,
            'discrepancies': discrepancies
        }
