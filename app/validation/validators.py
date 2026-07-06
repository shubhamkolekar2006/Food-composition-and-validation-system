class InputValidator:
    
    REQUIRED_FIELDS = ['calories', 'sugar', 'fat', 'saturated_fat', 'proteins', 'fibers', 'sodium']
    
    @classmethod
    def validate_nutrients(cls, data):
        """
        Validates nutritional inputs.
        data: dict of values
        Returns (is_valid, error_message, cleaned_data)
        """
        if not data:
            return False, "No data received", None
            
        missing_fields = [field for field in cls.REQUIRED_FIELDS if field not in data or data[field] is None]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}", None
            
        from app.utils.security import sanitize_input
        cleaned_data = {}
        # Optional fields sanitized
        cleaned_data['name'] = sanitize_input(data.get('name', 'Unknown Product'))
        cleaned_data['barcode'] = sanitize_input(data.get('barcode', '')) or None
        cleaned_data['ingredients'] = sanitize_input(data.get('ingredients', ''))

        
        try:
            for field in cls.REQUIRED_FIELDS:
                val = float(data[field])
                if val < 0:
                    return False, f"Nutrient value for '{field}' cannot be negative", None
                cleaned_data[field] = val
        except (ValueError, TypeError) as e:
            return False, "All nutrient values must be valid numbers", None
            
        return True, None, cleaned_data
