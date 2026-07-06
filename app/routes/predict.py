from flask import Blueprint, request, render_template, jsonify
from app.validation import InputValidator
from app.services import MLService, WarningService, DBService, ValidationService, LLMService
from app.utils.security import rate_limit

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/manual', methods=['GET', 'POST'])
@rate_limit(limit=40, period=60)
def manual():
    if request.method == 'GET':

        return render_template('manual_entry.html')
        
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 415
        
    data = request.get_json()
    preferences = data.get('preferences', [])
    
    # 1. Input Validation
    is_valid, err_msg, cleaned_data = InputValidator.validate_nutrients(data)
    if not is_valid:
        return jsonify({'error': err_msg}), 400
        
    # Prepare features for ML model [calories, sugar, fat, saturated_fat, proteins, fibers, sodium]
    features = [
        cleaned_data['calories'],
        cleaned_data['sugar'],
        cleaned_data['fat'],
        cleaned_data['saturated_fat'],
        cleaned_data['proteins'],
        cleaned_data['fibers'],
        cleaned_data['sodium']
    ]
    
    # 2. ML Prediction & Feedback
    try:
        score = MLService.predict_health_score(features)
        feedback = MLService.get_health_feedback(score)
    except Exception as e:
        print(f"ML Prediction failed: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
        
    # 3. Explainable Health Score (SHAP-like contributions)
    explanations = MLService.explain_score(features, score)
    
    # 4. Smart Nutrition Warnings
    warnings = WarningService.detect_warnings(cleaned_data)
    
    # 5. Nutrition Validation Engine (OCR vs Database comparison)
    validation_results = None
    db_product = None
    saved_product = None
    
    barcode = cleaned_data.get('barcode')
    if barcode:
        db_product = DBService.get_product_by_barcode(barcode)
        
    if db_product:
        # We found a matching product in database. Compare OCR/Scan values with DB values!
        validation_results = ValidationService.validate_ocr_vs_database(cleaned_data, db_product)
        # Log the validation log
        DBService.log_validation(
            product_id=db_product.id,
            validation_type='ocr' if data.get('is_ocr') else 'barcode',
            confidence_score=validation_results['confidence_score'],
            status=validation_results['status'],
            details=validation_results
        )
    else:
        # Save manually entered product to the database (original project behavior)
        saved_product = DBService.save_manual_product(
            name=cleaned_data.get('name'),
            calories=cleaned_data['calories'],
            sugar=cleaned_data['sugar'],
            fat=cleaned_data['fat'],
            saturated_fat=cleaned_data['saturated_fat'],
            protein=cleaned_data['proteins'],
            fiber=cleaned_data['fibers'],
            sodium=cleaned_data['sodium'],
            health_score=score
        )
        if saved_product:
            # Transfer manual ingredients text to database record
            saved_product.ingredients = cleaned_data.get('ingredients', '')
            from app.database import db
            db.session.commit()
            
            DBService.log_validation(
                product_id=saved_product.id,
                validation_type='manual',
                confidence_score=100.0,
                status='validated',
                details='Manual entry saved to database.'
            )
            
    # Build active product in-memory object for LLM context
    from app.models import Product as ProductModel
    active_product = ProductModel(
        product_name=cleaned_data.get('name') or "Analyzed Product",
        barcode=cleaned_data.get('barcode'),
        calories=cleaned_data['calories'],
        sugar=cleaned_data['sugar'],
        fat=cleaned_data['fat'],
        saturated_fat=cleaned_data['saturated_fat'],
        protein=cleaned_data['proteins'],
        fiber=cleaned_data['fibers'],
        sodium=cleaned_data['sodium'],
        ingredients=cleaned_data.get('ingredients', ''),
        health_score=score
    )
    
    product_id = db_product.id if db_product else (saved_product.id if saved_product else None)
    
    # 6. AI Features (Summary, Ingredients, Recommendations)
    ai_summary = LLMService.generate_ai_summary(active_product, validation_results, warnings, preferences)
    ingredient_explanations = LLMService.explain_ingredients(active_product.ingredients)
    
    # Query database for healthier recommendations
    alternatives = DBService.get_similar_products(active_product, limit=3)
    alternatives_explanation = LLMService.get_intelligent_alternatives_explanation(active_product, alternatives, preferences)
    
    serialized_alternatives = [{
        'product_name': alt.product_name,
        'brand': alt.brand or 'Generic',
        'barcode': alt.barcode,
        'health_score': alt.health_score,
        'calories': alt.calories,
        'sugar': alt.sugar,
        'fat': alt.fat,
        'protein': alt.protein,
        'sodium': alt.sodium
    } for alt in alternatives]
            
    return jsonify({
        'score': score,
        'feedback': feedback,
        'warnings': warnings,
        'explanations': explanations,
        'validation': validation_results,
        'ai_summary': ai_summary,
        'ingredient_explanations': ingredient_explanations,
        'product_id': product_id,
        'alternatives': serialized_alternatives,
        'alternatives_explanation': alternatives_explanation
    })

