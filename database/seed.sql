-- ══════════════════════════════════════════════════════════════════════════════
-- PeopleLens — Seed Data (minimal reference data for development)
-- ══════════════════════════════════════════════════════════════════════════════

-- Location dimension seed
INSERT INTO marts.dim_location (location_name, city, state, tier) VALUES
    ('Bengaluru',   'Bengaluru',   'Karnataka',     'T1'),
    ('Hyderabad',   'Hyderabad',   'Telangana',     'T1'),
    ('Chennai',     'Chennai',     'Tamil Nadu',    'T1'),
    ('Pune',        'Pune',        'Maharashtra',   'T1'),
    ('Mumbai',      'Mumbai',      'Maharashtra',   'T1'),
    ('Delhi NCR',   'Gurugram',    'Haryana',       'T1'),
    ('Kolkata',     'Kolkata',     'West Bengal',   'T2'),
    ('Ahmedabad',   'Ahmedabad',   'Gujarat',       'T2'),
    ('Kochi',       'Kochi',       'Kerala',        'T2'),
    ('Bhubaneswar', 'Bhubaneswar', 'Odisha',        'T3')
ON CONFLICT (location_name) DO NOTHING;

-- Minimal dim_manager seed (a few test managers)
INSERT INTO marts.dim_manager (manager_id, level, department, location) VALUES
    ('MGR_0001', 'L4', 'Engineering',  'Bengaluru'),
    ('MGR_0002', 'L4', 'Engineering',  'Hyderabad'),
    ('MGR_0003', 'L5', 'Analytics',    'Bengaluru'),
    ('MGR_0004', 'L4', 'Operations',   'Chennai'),
    ('MGR_0005', 'L5', 'Engineering',  'Pune')
ON CONFLICT DO NOTHING;
