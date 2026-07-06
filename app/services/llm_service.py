import os
import json
import google.generativeai as genai
from flask import current_app

class LLMService:
    _configured = False
    
    @classmethod
    def configure(cls):
        if not cls._configured:
            api_key = current_app.config.get('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                cls._configured = True
                print("Gemini API configured successfully.")
            else:
                cls._configured = False
        return cls._configured

    @classmethod
    def get_model(cls):
        if cls.configure():
            return genai.GenerativeModel('gemini-1.5-flash')
        return None

    @classmethod
    def generate_ai_summary(cls, product, validation, warnings, preferences):
        """
        Generates a concise AI-powered nutrition summary report.
        """
        model = cls.get_model()
        
        pref_str = ", ".join(preferences) if preferences else "General health guidelines"
        warnings_str = ", ".join([w['title'] for w in warnings]) if warnings else "None detected"
        val_str = f"Confidence: {validation['confidence_score']}% ({validation['status']})" if validation else "No database validation performed (manual entry)"
        
        prompt = f"""
        Act as an expert AI nutritionist. Generate a concise, engaging nutrition validation report for the food product:
        - Product Name: {product.product_name}
        - Brand: {product.brand or 'Generic'}
        - Health Score: {product.health_score}/100
        - Calories: {product.calories} kcal
        - Sugar: {product.sugar}g
        - Saturated Fat: {product.saturated_fat}g
        - Protein: {product.protein}g
        - Fiber: {product.fiber}g
        - Sodium: {product.sodium}mg
        - Ingredients: {product.ingredients or 'Not provided'}
        - Validation Status: {val_str}
        - Nutrition Warnings: {warnings_str}
        - User Focus/Preferences: {pref_str}
        
        Format the output nicely using Markdown. The report should include:
        1. **Product Overview**: A brief summary of the product's nutritional standing.
        2. **Validation & Integrity**: Interpret the validation confidence (if applicable) and warnings.
        3. **Personalized Recommendations**: Address the user's specific health goals ({pref_str}) regarding this product.
        
        Keep the tone professional, clear, and encouraging. Limit the response to 3 short paragraphs.
        """
        
        if not model:
            # Fallback Mock Summary
            goals = f"focused on **{pref_str}**" if preferences else "general wellness"
            return f"""
            ### AI Nutrition Report (API Offline)
            
            This is a mock nutritional summary for **{product.product_name}** because no `GEMINI_API_KEY` was found in the environment.
            
            - **Overview**: {product.product_name} has a predicted health score of **{round(product.health_score, 1)}/100**. It contains {product.calories} kcal, {product.sugar}g of sugar, and {product.protein}g of protein per 100g.
            - **Personalized Insights**: For your profile ({goals}), products with this score are generally best consumed in moderation. Keep an eye on ingredients for hidden sugars or saturated fats.
            - **How to Activate**: To get intelligent, personalized AI reports, set the `GEMINI_API_KEY` environment variable and restart the server!
            """
            
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error in generate_ai_summary: {e}")
            return "Unable to generate AI summary at this moment. Please check your network connection and API key."

    @classmethod
    def explain_ingredients(cls, ingredients_string):
        """
        Generates detailed explanations for the main ingredients in a product.
        """
        if not ingredients_string:
            return []
            
        model = cls.get_model()
        
        prompt = f"""
        Given the following ingredients list: "{ingredients_string}"
        Extract the main/important ingredients (up to 5). For each of these ingredients, provide:
        1. What it is (simple definition).
        2. Why manufacturers use it in packaged food.
        3. Health considerations or effects.
        
        Return the result ONLY as a valid JSON array of objects. Do not include markdown code block syntax (like ```json). Ensure keys are exactly: "name", "what_it_is", "manufacturer_use", "health_considerations".
        """
        
        if not model:
            # Fallback Rule-based simple explainer for common ingredients
            common_db = {
                'sugar': {
                    'name': 'Sugar (Sucrose)',
                    'what_it_is': 'A simple carbohydrate that provides sweet flavor.',
                    'manufacturer_use': 'Enhances flavor, acts as a preservative, and improves texture.',
                    'health_considerations': 'High intake is linked to obesity, type 2 diabetes, and cardiovascular diseases.'
                },
                'palm oil': {
                    'name': 'Palm Oil / Palmolein',
                    'what_it_is': 'An edible vegetable oil derived from palm fruit.',
                    'manufacturer_use': 'Provides shelf-stability, smooth texture, and is a cheap replacement for animal fats.',
                    'health_considerations': 'High in saturated fats which can raise LDL cholesterol. It also has significant environmental impacts.'
                },
                'aspartame': {
                    'name': 'Aspartame',
                    'what_it_is': 'An artificial low-calorie sweetener.',
                    'manufacturer_use': 'Provides intense sweetness without the calories of sugar.',
                    'health_considerations': 'Subject to ongoing research; some reports suggest potential impacts on gut microbiome.'
                },
                'salt': {
                    'name': 'Salt (Sodium Chloride)',
                    'what_it_is': 'A mineral compound essential for human health in small quantities.',
                    'manufacturer_use': 'Enhances flavor, preserves food, and extends shelf life.',
                    'health_considerations': 'Excessive consumption is associated with hypertension, cardiovascular diseases, and stroke.'
                }
            }
            
            explanations = []
            lower_ing = ingredients_string.lower()
            for key in common_db:
                if key in lower_ing:
                    explanations.append(common_db[key])
                    
            if not explanations:
                explanations.append({
                    'name': 'Ingredients List Scanned',
                    'what_it_is': 'Ingredients parsed by OCR/Manual Entry.',
                    'manufacturer_use': 'Required for product labeling.',
                    'health_considerations': 'Configure your GEMINI_API_KEY to unlock automated AI explanations for every ingredient in this product!'
                })
            return explanations

        try:
            response = model.generate_content(prompt)
            clean_text = response.text.strip()
            # Handle markdown code blocks if the model ignored instructions
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            
            return json.loads(clean_text)
        except Exception as e:
            print(f"Gemini API error in explain_ingredients: {e}")
            return []

    @classmethod
    def get_intelligent_alternatives_explanation(cls, product, alternatives, preferences):
        """
        Generates an explanation of why the recommended alternative products are better choice.
        """
        model = cls.get_model()
        pref_str = ", ".join(preferences) if preferences else "General health guidelines"
        
        alt_details = []
        for alt in alternatives:
            alt_details.append(f"- {alt.product_name} (Brand: {alt.brand or 'Generic'}, Health Score: {alt.health_score}/100, Sugar: {alt.sugar}g, Fat: {alt.fat}g, Protein: {alt.protein}g, Sodium: {alt.sodium}mg)")
            
        alts_str = "\n".join(alt_details)
        
        prompt = f"""
        Compare the scanned product:
        - {product.product_name} (Health Score: {product.health_score}/100, Sugar: {product.sugar}g, Fat: {product.fat}g, Protein: {product.protein}g, Sodium: {product.sodium}mg)
        
        With these healthier alternatives from our database:
        {alts_str}
        
        Write a very brief comparative explanation (2-3 sentences) explaining why these alternatives are better choices, specifically focusing on the user's preference/profile: {pref_str}.
        """
        
        if not model:
            # Rule-based fallback summary
            if alternatives:
                best = alternatives[0]
                score_gain = round(best.health_score - product.health_score, 1)
                return f"**{best.product_name}** offers a superior health profile (+{score_gain} score difference) compared to your scanned product, with healthier distributions of fats and sugars."
            return "No healthier alternatives are registered in the database currently."
            
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error in alternatives explanation: {e}")
            return "Database alternatives are superior due to higher overall ML health scores and lower sugar levels."

    @classmethod
    def chat_about_product(cls, product, user_message, chat_history, preferences):
        """
        Handles real-time conversation about the food product.
        """
        model = cls.get_model()
        pref_str = ", ".join(preferences) if preferences else "General health"
        
        # Build prompt context
        context = f"""
        You are an expert AI Nutritionist. You are talking to a user about the food product: {product.product_name}.
        Here are the official specifications of the product:
        - Calories: {product.calories} kcal
        - Sugar: {product.sugar}g
        - Saturated Fat: {product.saturated_fat}g
        - Total Fat: {product.fat}g
        - Protein: {product.protein}g
        - Fiber: {product.fiber}g
        - Sodium: {product.sodium}mg
        - Ingredients: {product.ingredients or 'Not listed'}
        - ML Health Score: {product.health_score}/100
        
        User Goal/Profile: {pref_str}
        
        Instructions:
        - Answer the user's question accurately based on this context.
        - Give clear explanations about whether the product fits their goal ({pref_str}).
        - Keep answers concise, helpful, and friendly.
        - If they ask for alternatives, suggest they look at the 'Healthier Alternatives' list on their screen.
        """
        
        if not model:
            # Fallback simple answering
            msg = user_message.lower()
            if 'sugar' in msg:
                return f"{product.product_name} contains {product.sugar}g of sugar per 100g. Sugar plays a large role in metabolic health."
            elif 'protein' in msg:
                return f"This product contains {product.protein}g of protein per 100g, which is important for muscle synthesis."
            elif 'diabetes' in msg or 'diabetic' in msg:
                if product.sugar > 10.0:
                    return f"With {product.sugar}g of sugar, this product is high in simple sugars and may not be optimal for individuals managing diabetes."
                return "This product is relatively low in sugar and may be incorporated with care into a diabetic-friendly meal plan."
            else:
                return "I am currently running in offline mode. Please configure GEMINI_API_KEY in the environment variables to activate full AI conversational capabilities!"

        try:
            # Build conversation history
            contents = []
            # We can prefix the context as a system instruction
            system_instruction = context
            
            # Simple manual chat history construction
            chat_prompt = f"System Context:\n{system_instruction}\n\nChat History:\n"
            for chat in chat_history:
                role = "User" if chat['role'] == 'user' else "Assistant"
                chat_prompt += f"{role}: {chat['content']}\n"
                
            chat_prompt += f"User: {user_message}\nAssistant:"
            
            response = model.generate_content(chat_prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error in chat: {e}")
            return "Sorry, I am having trouble answering right now. Please try again in a moment."
