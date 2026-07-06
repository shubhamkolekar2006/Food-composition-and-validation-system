from flask import Blueprint, render_template, request, jsonify
from app.services import DBService, LLMService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/ocr')
def ocr():
    return render_template('ocr.html')

@main_bp.route('/dashboard')
def dashboard():
    stats = DBService.get_dashboard_statistics()
    return render_template('dashboard.html', stats=stats)

@main_bp.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 415
        
    data = request.get_json()
    user_message = data.get('message', '').strip()
    chat_history = data.get('history', [])
    preferences = data.get('preferences', [])
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
        
    product_id = data.get('product_id')
    product = None
    if product_id:
        product = DBService.get_product_by_id(product_id)
        
    if not product:
        # Build a temporary in-memory product model if not in database
        from app.models import Product as ProductModel
        product = ProductModel(
            product_name=data.get('name', 'This Product'),
            calories=float(data.get('calories', 0)),
            sugar=float(data.get('sugar', 0)),
            fat=float(data.get('fat', 0)),
            saturated_fat=float(data.get('saturated_fat', 0)),
            protein=float(data.get('proteins', 0)),
            fiber=float(data.get('fibers', 0)),
            sodium=float(data.get('sodium', 0)),
            ingredients=data.get('ingredients', ''),
            health_score=float(data.get('score', 50))
        )
        
    try:
        response_text = LLMService.chat_about_product(
            product=product,
            user_message=user_message,
            chat_history=chat_history,
            preferences=preferences
        )
        return jsonify({'response': response_text})
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

