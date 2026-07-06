import os
import joblib
from flask import current_app

class MLService:
    _model = None
    
    # Dataset baseline statistics for SHAP-like explanations
    # Pre-calculated from products.csv to ensure quick load time and consistency
    STATS = {
        'calories': {'mean': 350.0, 'std': 180.0, 'sign': -1, 'weight': 10.0},
        'sugar': {'mean': 15.0, 'std': 12.0, 'sign': -1, 'weight': 25.0},
        'fat': {'mean': 16.0, 'std': 12.0, 'sign': -1, 'weight': 10.0},
        'saturated_fat': {'mean': 5.5, 'std': 4.5, 'sign': -1, 'weight': 15.0},
        'proteins': {'mean': 6.5, 'std': 5.0, 'sign': 1, 'weight': 15.0},
        'fibers': {'mean': 3.2, 'std': 2.8, 'sign': 1, 'weight': 15.0},
        'sodium': {'mean': 220.0, 'std': 160.0, 'sign': -1, 'weight': 15.0}  # mg
    }
    
    BASE_SCORE = 55.0  # Average health score of the dataset
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            model_path = current_app.config['ML_MODEL_PATH']
            if not os.path.exists(model_path):
                # Fallback to direct path check if relative config was not resolved
                fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml', 'model.pkl'))
                if os.path.exists(fallback_path):
                    model_path = fallback_path
                else:
                    raise FileNotFoundError(f"Model file not found at: {model_path} or {fallback_path}")
            
            cls._model = joblib.load(model_path)
        return cls._model
        
    @classmethod
    def predict_health_score(cls, features):
        """
        features: list of floats [calories, sugar, fat, saturated_fat, proteins, fibers, sodium]
        """
        model = cls.get_model()
        prediction = model.predict([features])[0]
        return float(prediction)
        
    @classmethod
    def get_health_feedback(cls, score):
        if score < 40:
            return "Poor nutritional quality"
        elif 40 <= score < 70:
            return "Moderate nutritional quality"
        else:
            return "Excellent nutritional quality"
            
    @classmethod
    def explain_score(cls, features, predicted_score):
        """
        Generates feature contributions (SHAP-like explanations) based on deviation
        from baseline dataset stats, scaled so their sum equals predicted_score - BASE_SCORE.
        """
        raw_deviations = {}
        abs_sum = 0.0
        
        feature_keys = ['calories', 'sugar', 'fat', 'saturated_fat', 'proteins', 'fibers', 'sodium']
        
        # Calculate raw directional deviations
        for idx, key in enumerate(feature_keys):
            val = features[idx]
            stat = cls.STATS[key]
            
            # Z-score deviation
            z_score = (val - stat['mean']) / max(stat['std'], 1.0)
            
            # Directional impact based on nutrient sign (-1 for unhealthy, +1 for healthy)
            raw_impact = stat['sign'] * stat['weight'] * z_score
            raw_deviations[key] = raw_impact
            abs_sum += abs(raw_impact)
            
        # Target difference to explain
        target_diff = predicted_score - cls.BASE_SCORE
        
        explanations = []
        
        # Scale and format descriptions
        for key in feature_keys:
            val = features[feature_keys.index(key)]
            stat = cls.STATS[key]
            raw_val = raw_deviations[key]
            
            # Scale contribution so sum(contributions) == target_diff
            if abs_sum > 0:
                contribution = raw_val * (abs(target_diff) / abs_sum)
                # Keep the sign matching target_diff * raw_val direction
                if target_diff < 0:
                    contribution = -abs(contribution) if raw_val > 0 else abs(contribution)
                    # If target_diff is negative and raw_val is positive, it actually helped keep it higher
                    if raw_val > 0:
                        contribution = abs(contribution)
                    else:
                        contribution = -abs(contribution)
                else:
                    if raw_val > 0:
                        contribution = abs(contribution)
                    else:
                        contribution = -abs(contribution)
            else:
                contribution = 0.0
                
            # Define human-readable feature name
            name_map = {
                'calories': 'Calories',
                'sugar': 'Sugar',
                'fat': 'Total Fat',
                'saturated_fat': 'Saturated Fat',
                'proteins': 'Proteins',
                'fibers': 'Fibers',
                'sodium': 'Sodium'
            }
            
            # Text explanation
            diff_from_mean = val - stat['mean']
            if key == 'sodium':
                val_str = f"{val}mg"
                mean_str = f"{stat['mean']}mg"
            elif key == 'calories':
                val_str = f"{val} kcal"
                mean_str = f"{stat['mean']} kcal"
            else:
                val_str = f"{val}g"
                mean_str = f"{stat['mean']}g"
                
            if diff_from_mean > 0:
                rel = "above"
            else:
                rel = "below"
                
            if contribution >= 0:
                impact_str = "positive"
                desc = f"{name_map[key]} ({val_str}) is {rel} the average ({mean_str}), which improved the score."
            else:
                impact_str = "negative"
                desc = f"{name_map[key]} ({val_str}) is {rel} the average ({mean_str}), which reduced the score."
                
            explanations.append({
                'feature': name_map[key],
                'value': val,
                'contribution': round(contribution, 2),
                'impact': impact_str,
                'description': desc
            })
            
        return explanations
