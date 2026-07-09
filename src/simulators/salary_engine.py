# src/simulators/salary_engine.py
import random
from src.config.config import SALARY_BANDS, HIKE_PERCENTAGE, BONUS_PERCENTAGE

# Seed for reproducibility
random.seed(42)

def update_salary(current_salary, level, rating, promoted):
    """
    Updates employee salary based on performance ratings and promotion status.
    - Applies a merit hike based on rating.
    - If promoted, moves salary into the new level's band (max of hike salary and random floor entry).
    - Caps salary at level ceiling if not promoted to prevent band drift.
    - Calculates annual performance bonus and stock options (10% for L4/L5).
    """
    salary = current_salary
    hike = HIKE_PERCENTAGE[rating]
    salary *= (1 + hike)
    
    min_sal, max_sal = SALARY_BANDS[level]
    
    if promoted:
        # Enforce range of the new level
        salary = max(salary, random.randint(min_sal, int(min_sal + 0.25 * (max_sal - min_sal))))
    else:
        # Cap at current level's ceiling to maintain strict database consistency
        if salary > max_sal:
            salary = max_sal
            
    bonus = salary * BONUS_PERCENTAGE[rating]
    
    stock = 0
    if level in ["L4", "L5"]:
        stock = salary * 0.10
        
    return (
        int(salary),
        int(bonus),
        int(stock)
    )
