# src/simulators/promotion_engine.py
from src.config.config import PROMOTION_RULES

def check_promotion(current_level, years_in_level, ratings, learning_hours):
    """
    Evaluates whether an employee is eligible for promotion.
    Requires:
    - Minimum tenure (years in level)
    - Minimum average rating
    - Minimum learning hours completed
    """
    if current_level == "L5":
        return current_level, False
        
    rule = PROMOTION_RULES[current_level]
    
    if not ratings:
        return current_level, False
        
    average_rating = sum(ratings) / len(ratings)
    
    if (
        years_in_level >= rule["min_years"]
        and average_rating >= rule["min_avg_rating"]
        and learning_hours >= rule["min_learning_hours"]
    ):
        return rule["next"], True
        
    return current_level, False
