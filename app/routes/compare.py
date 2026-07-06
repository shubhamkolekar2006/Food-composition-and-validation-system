from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services import DBService, WarningService

compare_bp = Blueprint('compare', __name__)

@compare_bp.route('/compare', methods=['GET', 'POST'])
def compare():
    products = DBService.get_all_products()
    
    product_a_id = request.values.get('product_a')
    product_b_id = request.values.get('product_b')
    
    if not product_a_id or not product_b_id:
        # Initial render of compare page
        return render_template('compare.html', products=products, result=None)
        
    # Load products from database
    product_a = DBService.get_product_by_id(product_a_id)
    product_b = DBService.get_product_by_id(product_b_id)
    
    if not product_a or not product_b:
        error = "One or both selected products could not be found."
        return render_template('compare.html', products=products, error=error, result=None)
        
    # Log the comparison in database
    DBService.log_comparison(product_a_id=product_a.id, product_b_id=product_b.id)
    
    # Calculate differences (A - B)
    diff = {
        'calories': round(product_a.calories - product_b.calories, 2),
        'sugar': round(product_a.sugar - product_b.sugar, 2),
        'fat': round(product_a.fat - product_b.fat, 2),
        'saturated_fat': round(product_a.saturated_fat - product_b.saturated_fat, 2),
        'protein': round(product_a.protein - product_b.protein, 2),
        'fiber': round(product_a.fiber - product_b.fiber, 2),
        'sodium': round(product_a.sodium - product_b.sodium, 2),
        'health_score': round(product_a.health_score - product_b.health_score, 2)
    }
    
    # Get warnings
    warnings_a = WarningService.detect_warnings(product_a)
    warnings_b = WarningService.detect_warnings(product_b)
    
    # Heuristics comparison decider
    decision = generate_comparison_decision(product_a, product_b, diff)
    
    result = {
        'product_a': product_a,
        'product_b': product_b,
        'diff': diff,
        'warnings_a': warnings_a,
        'warnings_b': warnings_b,
        'decision': decision
    }
    
    return render_template('compare.html', products=products, result=result)

def generate_comparison_decision(prod_a, prod_b, diff):
    better_product = None
    reasoning = []
    
    score_diff = diff['health_score']
    
    if abs(score_diff) > 5.0:
        # Significant health score difference
        if score_diff > 0:
            better_product = prod_a
            reasoning.append(f"It has a significantly higher health score ({round(prod_a.health_score, 1)} vs {round(prod_b.health_score, 1)}).")
        else:
            better_product = prod_b
            reasoning.append(f"It has a significantly higher health score ({round(prod_b.health_score, 1)} vs {round(prod_a.health_score, 1)}).")
    else:
        # Scores are close, compare individual parameters
        reasons_a = 0
        reasons_b = 0
        
        # Sugar
        if diff['sugar'] < 0:
            reasons_a += 1
            reasoning.append(f"**{prod_a.product_name}** has less sugar ({prod_a.sugar}g vs {prod_b.sugar}g).")
        elif diff['sugar'] > 0:
            reasons_b += 1
            reasoning.append(f"**{prod_b.product_name}** has less sugar ({prod_b.sugar}g vs {prod_a.sugar}g).")
            
        # Protein
        if diff['protein'] > 0:
            reasons_a += 1
            reasoning.append(f"**{prod_a.product_name}** is richer in proteins ({prod_a.protein}g vs {prod_b.protein}g).")
        elif diff['protein'] < 0:
            reasons_b += 1
            reasoning.append(f"**{prod_b.product_name}** is richer in proteins ({prod_b.protein}g vs {prod_a.protein}g).")
            
        # Fiber
        if diff['fiber'] > 0:
            reasons_a += 1
            reasoning.append(f"**{prod_a.product_name}** provides more dietary fiber ({prod_a.fiber}g vs {prod_b.fiber}g).")
        elif diff['fiber'] < 0:
            reasons_b += 1
            reasoning.append(f"**{prod_b.product_name}** provides more dietary fiber ({prod_b.fiber}g vs {prod_a.fiber}g).")
            
        # Sodium
        if diff['sodium'] < 0:
            reasons_a += 1
            reasoning.append(f"**{prod_a.product_name}** contains less sodium ({prod_a.sodium}mg vs {prod_b.sodium}mg).")
        elif diff['sodium'] > 0:
            reasons_b += 1
            reasoning.append(f"**{prod_b.product_name}** contains less sodium ({prod_b.sodium}mg vs {prod_a.sodium}mg).")
            
        if reasons_a > reasons_b:
            better_product = prod_a
        elif reasons_b > reasons_a:
            better_product = prod_b
        else:
            # Absolute tie-breaker on health score
            better_product = prod_a if score_diff >= 0 else prod_b
            reasoning.append("Both products are nutritionally very similar.")
            
    decision_text = f"**{better_product.product_name}** is the recommended option. "
    if reasoning:
        decision_text += " ".join(reasoning)
    else:
        decision_text += "It offers a slightly better overall nutritional profile."
        
    return {
        'better_product': better_product,
        'explanation': decision_text
    }
