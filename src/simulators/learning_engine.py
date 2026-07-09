# src/simulators/learning_engine.py
import random
from faker import Faker
from src.config.config import COURSE_CATALOG

# Seed for reproducibility
random.seed(42)
fake = Faker("en_IN")
Faker.seed(42)

def generate_learning(employee_id, department, start_limit, end_limit, is_exited):
    """
    Generates a realistic learning record.
    - Technical training matches the employee's department catalog.
    - There is a 20% chance of taking general corporate "Soft Skills" (HR catalog).
    - Ensures dates are strictly within active tenure.
    """
    # 80% chance of technical dept-specific training, 20% general corporate training (HR)
    if department != "HR" and random.random() < 0.20:
        category = "HR"
    else:
        category = department
        
    course = random.choice(COURSE_CATALOG[category])
    
    # Map the category key to a user-friendly skill category name
    # e.g., Engineering -> Programming, Cloud -> Cloud, HR -> Soft Skills
    category_display_map = {
        "Engineering": "Programming",
        "Data Science": "Data Science",
        "Cloud": "Cloud",
        "Cyber Security": "Cyber Security",
        "HR": "Soft Skills",
        "Finance": "Finance",
        "Sales": "Sales",
        "Marketing": "Marketing",
        "Support": "Support"
    }
    skill_category = category_display_map[category]
    
    hours = random.randint(4, 40)
    
    # Exited employees must have completed courses at exit date
    if is_exited:
        status = "Completed"
    else:
        status = random.choices(["Completed", "In Progress"], weights=[85, 15])[0]
        
    completion_date = None
    if status == "Completed":
        # Generate date between start_limit (joining_date) and end_limit (exit_date or today)
        if start_limit >= end_limit:
            completion_date = start_limit
        else:
            completion_date = fake.date_between(start_date=start_limit, end_date=end_limit)
            
    return {
        "employee_id": employee_id,
        "course_name": course,
        "skill_category": skill_category,
        "hours_completed": hours,
        "completion_status": status,
        "completion_date": completion_date
    }
