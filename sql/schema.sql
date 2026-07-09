-- Database Schema DDL for NimbusTech HR Database

-- 1. Manager Master Table
CREATE TABLE managers (
    manager_id VARCHAR(50) PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    team_size INT NOT NULL,
    experience_years INT NOT NULL
);

-- 2. Employee Master Table
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    gender VARCHAR(20) NOT NULL,
    age INT NOT NULL,
    location VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    joining_date DATE NOT NULL,
    college_tier VARCHAR(20) NOT NULL,
    manager_id VARCHAR(50),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Active', 'Exited')),
    FOREIGN KEY (manager_id) REFERENCES managers(manager_id)
);


-- 3. Compensation History Table
CREATE TABLE compensation (
    comp_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    effective_date DATE NOT NULL,
    level VARCHAR(50) NOT NULL,
    salary DECIMAL(12, 2) NOT NULL,
    bonus DECIMAL(12, 2) NOT NULL,
    stock DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);


-- 4. Project Assignments Table
CREATE TABLE projects (
    assignment_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    project_name VARCHAR(150) NOT NULL,
    client_name VARCHAR(150) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    billable BOOLEAN NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);


-- 5. Performance Ratings Table
CREATE TABLE performance (
    rating_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    review_year INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    promotion VARCHAR(5) NOT NULL CHECK (promotion IN ('Yes', 'No')),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);

-- 6. Learning Records Table
CREATE TABLE learning (
    learning_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    skill_category VARCHAR(100) NOT NULL,
    hours_completed FLOAT NOT NULL CHECK (hours_completed >= 0),
    completion_status VARCHAR(20) NOT NULL CHECK (completion_status IN ('Completed', 'In Progress')),
    completion_date DATE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);


-- 7. Exit Records Table
CREATE TABLE exits (
    exit_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL UNIQUE,
    exit_date DATE NOT NULL,
    exit_reason VARCHAR(150) NOT NULL,
    voluntary BOOLEAN NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);
