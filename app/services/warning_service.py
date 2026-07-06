class WarningService:
    
    SWEETENERS = [
        'aspartame', 'sucralose', 'acesulfame', 'saccharin', 'neotame', 
        'stevia', 'xylitol', 'erythritol', 'sorbitol', 'maltitol', 'isomalt'
    ]
    
    PALM_OIL_KEYWORDS = ['palm oil', 'palmolein', 'palm kernel']

    @classmethod
    def detect_warnings(cls, product_data):
        """
        Scans product data for safety and nutritional flags.
        product_data can be a Product instance or a dict with nutritional values.
        """
        if hasattr(product_data, 'calories'):
            # It's a DB model instance
            data = {
                'calories': product_data.calories,
                'sugar': product_data.sugar,
                'fat': product_data.fat,
                'saturated_fat': product_data.saturated_fat,
                'proteins': product_data.protein,
                'fibers': product_data.fiber,
                'sodium': product_data.sodium,
                'ingredients': getattr(product_data, 'ingredients', '') or ''
            }
        else:
            # It's a dictionary
            data = {
                'calories': product_data.get('calories', 0.0),
                'sugar': product_data.get('sugar', 0.0),
                'fat': product_data.get('fat', 0.0),
                'saturated_fat': product_data.get('saturated_fat', 0.0),
                'proteins': product_data.get('proteins', 0.0),
                'fibers': product_data.get('fibers', 0.0),
                'sodium': product_data.get('sodium', 0.0),
                'ingredients': product_data.get('ingredients', '') or ''
            }
            
        warnings = []
        ingredients_lower = data['ingredients'].lower()
        
        # 1. High Sugar
        if data['sugar'] > 15.0:
            warnings.append({
                'title': 'High Sugar Content',
                'type': 'danger',
                'description': f"Contains {data['sugar']}g of sugar per 100g, which exceeds the high-sugar threshold (15g). High sugar intake is linked to diabetes and cardiovascular risks."
            })
            
        # 2. High Sodium
        if data['sodium'] > 400.0:
            warnings.append({
                'title': 'High Sodium Level',
                'type': 'danger',
                'description': f"Contains {data['sodium']}mg of sodium per 100g, exceeding the high-sodium limit (400mg). Elevated sodium can lead to high blood pressure."
            })
            
        # 3. High Saturated Fat
        if data['saturated_fat'] > 5.0:
            warnings.append({
                'title': 'High Saturated Fat',
                'type': 'danger',
                'description': f"Contains {data['saturated_fat']}g of saturated fat per 100g, exceeding the recommended threshold (5g). Saturated fats can raise LDL cholesterol levels."
            })
            
        # 4. Low Fiber
        # Only check for products that have significant calorie density (> 150 kcal) to avoid flagging beverages
        if data['calories'] > 150.0 and data['fibers'] < 2.0:
            warnings.append({
                'title': 'Low Dietary Fiber',
                'type': 'warning',
                'description': f"Contains only {data['fibers']}g of fiber in a high-energy food. High-calorie foods should ideally contain more fiber (>2g) to assist digestion."
            })
            
        # 5. Artificial Sweeteners
        detected_sweeteners = [s for s in cls.SWEETENERS if s in ingredients_lower]
        if detected_sweeteners:
            warnings.append({
                'title': 'Artificial Sweeteners Detected',
                'type': 'warning',
                'description': f"Contains sweeteners: {', '.join(detected_sweeteners)}. Artificial sweeteners might impact gut health and alter glucose tolerance."
            })
            
        # 6. Palm Oil
        detected_palm = [p for p in cls.PALM_OIL_KEYWORDS if p in ingredients_lower]
        if detected_palm:
            warnings.append({
                'title': 'Contains Palm Oil',
                'type': 'warning',
                'description': "Contains palm oil derivatives. Palm oil is high in saturated fats and has significant environmental implications."
            })
            
        # 7. High Calories
        if data['calories'] > 400.0:
            warnings.append({
                'title': 'High Caloric Density',
                'type': 'warning',
                'description': f"Contains {data['calories']} kcal per 100g. This is a highly energy-dense food; consume in moderation."
            })
            
        return warnings
