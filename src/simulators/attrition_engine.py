# src/simulators/attrition_engine.py
import random

# Seed for reproducibility
random.seed(42)

def check_attrition(rating, salary_ratio, years_since_promotion, project_stress, learning_hours, total_tenure, college_tier):
    """
    Computes an attrition probability score based on multiple career factors.
    Values are scaled down so that annual probability compounds to ~18% cumulative attrition.
    """
    # Base probability
    prob = 0.015
    
    # 1. Performance Rating factor
    if rating == 1:
        prob += 0.08
    elif rating == 2:
        prob += 0.04
    elif rating == 4:
        prob -= 0.01
    elif rating == 5:
        prob -= 0.02
        
    # 2. College Tier
    if college_tier == "Tier-2":
        prob += 0.005
    elif college_tier == "Tier-3":
        prob += 0.01
        
    # 3. Promotion Delay (Stagnation)
    if years_since_promotion >= 4:
        prob += 0.025
    elif years_since_promotion >= 3:
        prob += 0.01
        
    # 4. Project Stress (Difficulty)
    if project_stress == "High":
        prob += 0.01
    elif project_stress == "Low":
        prob -= 0.005
        
    # 5. Learning Hours
    if learning_hours >= 40:
        prob -= 0.01
    elif learning_hours < 8:
        prob += 0.01
        
    # 6. Salary Position (Salary Ratio)
    if salary_ratio < 0.85:
        prob += 0.02
    elif salary_ratio > 1.15:
        prob -= 0.01
        
    # 7. Tenure factor
    if total_tenure <= 1:
        prob -= 0.005
    elif total_tenure >= 5:
        prob -= 0.01
    else:
        prob += 0.005
        
    # Cap between 0.1% and 60%
    prob = max(0.001, min(prob, 0.60))
    
    return random.random() < prob
