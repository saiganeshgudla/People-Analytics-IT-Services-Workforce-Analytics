# src/config/config.py
# Centralized business rules and simulation settings for NimbusTech

NUM_EMPLOYEES = 35000
TARGET_ATTRITION_RATE = 0.18
NUM_MANAGERS = 1500

LEVELS = ["L1", "L2", "L3", "L4", "L5"]

# Salary Bands (annual salary in INR)
SALARY_BANDS = {
    "L1": (370000, 550000),
    "L2": (600000, 950000),
    "L3": (1000000, 1500000),
    "L4": (1600000, 2400000),
    "L5": (2500000, 4500000)
}

DEPARTMENTS = [
    "Engineering",
    "Data Science",
    "Cloud",
    "Cyber Security",
    "HR",
    "Finance",
    "Sales",
    "Marketing",
    "Support"
]

LOCATIONS = [
    "Bengaluru",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Noida",
    "Mumbai"
]

COLLEGE_TIERS = [
    "Tier-1",
    "Tier-2",
    "Tier-3"
]

# Exit Reason Distribution (Sum of probabilities = 1.0)
EXIT_REASONS = {
    "Better Opportunity": 0.39,
    "Career Growth": 0.22,
    "Personal Reasons": 0.14,
    "Compensation": 0.13,
    "Performance Issues": 0.05,
    "Relocation": 0.04,
    "Higher Education": 0.03
}

# Performance Rating Distribution (Sum of probabilities = 1.0)
RATING_DISTRIBUTION = {
    1: 0.02,
    2: 0.08,
    3: 0.58,
    4: 0.22,
    5: 0.10
}

# Promotion Probability (base chance per year)
PROMOTION_PROBABILITY = {
    "L1": 0.12,
    "L2": 0.10,
    "L3": 0.08,
    "L4": 0.05,
    "L5": 0.00
}

# Role mappings by department and level
ROLES_MAP = {
    "Engineering": {
        "L1": "Associate Software Engineer",
        "L2": "Software Engineer",
        "L3": "Senior Software Engineer",
        "L4": "Lead Engineer",
        "L5": "Engineering Manager"
    },
    "Data Science": {
        "L1": "Associate Data Scientist",
        "L2": "Data Scientist",
        "L3": "Senior Data Scientist",
        "L4": "Lead Data Scientist",
        "L5": "Data Science Manager"
    },
    "Cloud": {
        "L1": "Cloud Associate",
        "L2": "Cloud Engineer",
        "L3": "Senior Cloud Engineer",
        "L4": "Cloud Lead",
        "L5": "Cloud Architect"
    },
    "Cyber Security": {
        "L1": "Security Analyst",
        "L2": "Security Engineer",
        "L3": "Senior Security Engineer",
        "L4": "Security Lead",
        "L5": "Security Manager"
    },
    "HR": {
        "L1": "HR Associate",
        "L2": "HR Specialist",
        "L3": "Senior HR Specialist",
        "L4": "HR Manager",
        "L5": "HR Director"
    },
    "Finance": {
        "L1": "Finance Associate",
        "L2": "Finance Analyst",
        "L3": "Senior Finance Analyst",
        "L4": "Finance Lead",
        "L5": "Finance Manager"
    },
    "Sales": {
        "L1": "Sales Associate",
        "L2": "Account Executive",
        "L3": "Senior Account Executive",
        "L4": "Sales Director",
        "L5": "VP Sales"
    },
    "Marketing": {
        "L1": "Marketing Associate",
        "L2": "Marketing Specialist",
        "L3": "Senior Marketing Specialist",
        "L4": "Marketing Manager",
        "L5": "Marketing Director"
    },
    "Support": {
        "L1": "Support Analyst",
        "L2": "Senior Support Analyst",
        "L3": "Support Lead",
        "L4": "Support Manager",
        "L5": "Support Director"
    }
}

# Skill development catalog by department
COURSE_CATALOG = {
    "Engineering": ["Python Fundamentals", "Java Programming", "Advanced SQL", "Data Structures", "System Design"],
    "Data Science": ["Machine Learning", "Deep Learning", "Power BI", "Statistics", "Pandas for Analytics"],
    "Cloud": ["AWS Cloud Practitioner", "Azure AZ-900", "Docker Essentials", "Kubernetes Basics", "Terraform Fundamentals"],
    "Cyber Security": ["Network Security", "Ethical Hacking", "OWASP Top 10", "SOC Fundamentals"],
    "HR": ["Leadership Essentials", "Communication Skills", "Time Management", "Agile Scrum", "Stakeholder Management"],
    "Finance": ["Financial Accounting", "Corporate Finance", "Excel for Finance", "Tally ERP", "Risk Management"],
    "Sales": ["Negotiation Skills", "Account Management", "CRM Tools", "Sales Pitching", "Market Research"],
    "Marketing": ["Digital Marketing", "SEO Optimization", "Content Strategy", "Brand Management", "Google Analytics"],
    "Support": ["ITIL Foundations", "Customer Service Essentials", "Helpdesk Operations", "Troubleshooting Basics", "SLA Management"]
}

# Project catalog by department
PROJECTS_CATALOG = {
    "Engineering": [
        {"project_name": "Apollo Core", "client_name": "Microsoft", "difficulty": "High"},
        {"project_name": "Phoenix Rewrite", "client_name": "Google", "difficulty": "Medium"},
        {"project_name": "Orion API", "client_name": "Amazon", "difficulty": "High"}
    ],
    "Data Science": [
        {"project_name": "DataHub Predictive", "client_name": "JP Morgan", "difficulty": "High"},
        {"project_name": "Retail Analytics", "client_name": "Adobe", "difficulty": "Medium"},
        {"project_name": "AI Recommendation Engine", "client_name": "Internal", "difficulty": "High"}
    ],
    "Cloud": [
        {"project_name": "CloudMigrate v2", "client_name": "Oracle", "difficulty": "High"},
        {"project_name": "Kubernetes Migration", "client_name": "Infosys", "difficulty": "Medium"},
        {"project_name": "DevOps Automation", "client_name": "Internal", "difficulty": "Medium"}
    ],
    "Cyber Security": [
        {"project_name": "Sentinel Security", "client_name": "Deloitte", "difficulty": "High"},
        {"project_name": "Penetration Testing", "client_name": "Accenture", "difficulty": "High"},
        {"project_name": "Vulnerability Patcher", "client_name": "Internal", "difficulty": "Medium"}
    ],
    "HR": [
        {"project_name": "Recruitment Automation", "client_name": "Internal", "difficulty": "Low"},
        {"project_name": "PeopleLens Portal", "client_name": "Internal", "difficulty": "Medium"}
    ],
    "Finance": [
        {"project_name": "Ledger Reconciliation", "client_name": "TCS", "difficulty": "Medium"},
        {"project_name": "Tax Calculator Portal", "client_name": "Internal", "difficulty": "Low"}
    ],
    "Sales": [
        {"project_name": "CRM Integration", "client_name": "Salesforce", "difficulty": "Medium"},
        {"project_name": "Global Account Pitching", "client_name": "TechGiant", "difficulty": "High"}
    ],
    "Marketing": [
        {"project_name": "SEO & Content Campaign", "client_name": "Internal", "difficulty": "Low"},
        {"project_name": "Digital Brand Relaunch", "client_name": "RetailCorp", "difficulty": "Medium"}
    ],
    "Support": [
        {"project_name": "SLA Helpdesk Migration", "client_name": "TelcoGroup", "difficulty": "Medium"},
        {"project_name": "Desktop Automation Support", "client_name": "Internal", "difficulty": "Low"}
    ]
}

# Promotion Rules (Tenure, performance, and learning thresholds)
PROMOTION_RULES = {
    "L1": {
        "next": "L2",
        "min_years": 2,
        "min_avg_rating": 4.0,
        "min_learning_hours": 40
    },
    "L2": {
        "next": "L3",
        "min_years": 3,
        "min_avg_rating": 4.0,
        "min_learning_hours": 60
    },
    "L3": {
        "next": "L4",
        "min_years": 4,
        "min_avg_rating": 4.2,
        "min_learning_hours": 80
    },
    "L4": {
        "next": "L5",
        "min_years": 5,
        "min_avg_rating": 4.3,
        "min_learning_hours": 100
    }
}

# Hike percentages based on performance rating
HIKE_PERCENTAGE = {
    1: 0.00,
    2: 0.04,
    3: 0.08,
    4: 0.12,
    5: 0.16
}

# Bonus percentages based on performance rating
BONUS_PERCENTAGE = {
    1: 0.00,
    2: 0.03,
    3: 0.05,
    4: 0.08,
    5: 0.12
}


