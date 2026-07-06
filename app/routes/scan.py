from flask import Blueprint, request, render_template
from app.services import DBService, MLService, WarningService, LLMService
from app.utils.security import rate_limit, sanitize_input

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/scan', methods=['GET', 'POST'])
@rate_limit(limit=40, period=60)
def scan():
    message = None
    error = None
    product = None
    warnings = None
    explanations = None
    ai_summary = None
    ingredient_explanations = None
    alternatives = None
    alternatives_explanation = None
    
    preferences = request.values.getlist('preferences')

    if request.method == 'POST' or request.values.get('barcode'):
        barcode = sanitize_input(request.values.get('barcode', ''))

        print(f"Barcode search query received: {barcode}")
        
        # 1. Query database for barcode
        prod = DBService.get_product_by_barcode(barcode)
        
        if prod:
            product = prod
            # Log successful scan
            DBService.log_scan(barcode=barcode, status='found', product_id=prod.id)
            
            # 2. Get predictions & explanations
            features = [
                prod.calories,
                prod.sugar,
                prod.fat,
                prod.saturated_fat,
                prod.protein,
                prod.fiber,
                prod.sodium
            ]
            
            # Predict or use cached health score
            score = prod.health_score if prod.health_score is not None else MLService.predict_health_score(features)
            feedback = MLService.get_health_feedback(score)
            
            # 3. Smart Warnings
            warnings = WarningService.detect_warnings(prod)
            
            # 4. Feature explanations
            explanations = MLService.explain_score(features, score)
            
            # 5. AI Features (Summary, Ingredients, Recommendations)
            # Create a mock validation result since the product matched database perfectly
            validation_results = {
                'confidence_score': 100.0,
                'status': 'validated'
            }
            
            ai_summary = LLMService.generate_ai_summary(prod, validation_results, warnings, preferences)
            ingredient_explanations = LLMService.explain_ingredients(prod.ingredients)
            
            # Recommendations
            alternatives = DBService.get_similar_products(prod, limit=3)
            alternatives_explanation = LLMService.get_intelligent_alternatives_explanation(prod, alternatives, preferences)
            
            # Prepare display message
            message = f"Product: {prod.product_name}<br>Brand: {prod.brand or 'Generic'}<br>Health Score: {round(score, 1)}/100<br>Feedback: {feedback}"
        else:
            # Log failed scan
            DBService.log_scan(barcode=barcode, status='not_found', product_id=None)
            error = f"Product with barcode '{barcode}' not found in the database."

    return render_template(
        "scanner.html", 
        message=message, 
        error=error, 
        product=product,
        warnings=warnings,
        explanations=explanations,
        ai_summary=ai_summary,
        ingredient_explanations=ingredient_explanations,
        alternatives=alternatives,
        alternatives_explanation=alternatives_explanation,
        preferences=preferences
    )

