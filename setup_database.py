"""
setup_database.py

Run once to create and populate the local SQLite database (meridian.db)
used by the agent for structured queries (employees, departments, projects).

    python setup_database.py

Safe to re-run: it drops and recreates the tables each time so the data
stays consistent with this script.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "meridian.db"

SCHEMA = """
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    manager TEXT,
    budget INTEGER,
    location TEXT
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    department_id INTEGER,
    email TEXT,
    hire_date TEXT,
    manager_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER,
    status TEXT,
    start_date TEXT,
    end_date TEXT,
    budget INTEGER,
    lead_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (lead_id) REFERENCES employees(id)
);
"""

DEPARTMENTS = [
    (1, "Engineering", "Priya Nair", 4200000, "Austin, TX"),
    (2, "People Operations", "Marcus Chen", 950000, "Austin, TX"),
    (3, "Finance", "Dana Whitfield", 1100000, "New York, NY"),
    (4, "Sales", "Tomas Reyes", 2600000, "Chicago, IL"),
    (5, "IT & Security", "Yuki Tanaka", 1500000, "Austin, TX"),
    (6, "Marketing", "Alicia Gomez", 1300000, "New York, NY"),
]

EMPLOYEES = [
    (1, "Priya Nair", "VP of Engineering", 1, "priya.nair@meridian.co", "2018-03-12", None),
    (2, "Marcus Chen", "Head of People Ops", 2, "marcus.chen@meridian.co", "2019-01-08", None),
    (3, "Dana Whitfield", "CFO", 3, "dana.whitfield@meridian.co", "2017-06-01", None),
    (4, "Tomas Reyes", "VP of Sales", 4, "tomas.reyes@meridian.co", "2020-02-17", None),
    (5, "Yuki Tanaka", "Head of IT & Security", 5, "yuki.tanaka@meridian.co", "2018-11-05", None),
    (6, "Alicia Gomez", "Head of Marketing", 6, "alicia.gomez@meridian.co", "2021-04-19", None),
    (7, "Ben Carter", "Senior Backend Engineer", 1, "ben.carter@meridian.co", "2019-09-23", 1),
    (8, "Sofia Marin", "Frontend Engineer", 1, "sofia.marin@meridian.co", "2021-07-14", 1),
    (9, "Wei Zhang", "Data Engineer", 1, "wei.zhang@meridian.co", "2022-01-10", 1),
    (10, "Grace Liu", "QA Engineer", 1, "grace.liu@meridian.co", "2022-05-30", 1),
    (11, "Omar Haddad", "DevOps Engineer", 1, "omar.haddad@meridian.co", "2020-08-03", 1),
    (12, "Hannah Ford", "Recruiter", 2, "hannah.ford@meridian.co", "2021-02-22", 2),
    (13, "Leo Bianchi", "HR Business Partner", 2, "leo.bianchi@meridian.co", "2020-10-12", 2),
    (14, "Nina Petrov", "Financial Analyst", 3, "nina.petrov@meridian.co", "2021-09-06", 3),
    (15, "Carlos Ruiz", "Accountant", 3, "carlos.ruiz@meridian.co", "2019-04-28", 3),
    (16, "Ava Thompson", "Account Executive", 4, "ava.thompson@meridian.co", "2022-03-15", 4),
    (17, "Jamal Rivers", "Sales Development Rep", 4, "jamal.rivers@meridian.co", "2023-01-09", 4),
    (18, "Ethan Brooks", "Security Engineer", 5, "ethan.brooks@meridian.co", "2020-06-18", 5),
    (19, "Mia Alvarez", "IT Support Specialist", 5, "mia.alvarez@meridian.co", "2022-11-02", 5),
    (20, "Noah Kim", "Content Strategist", 6, "noah.kim@meridian.co", "2021-12-01", 6),
    (21, "Isabella Rossi", "Growth Marketer", 6, "isabella.rossi@meridian.co", "2022-08-19", 6),
]

PROJECTS = [
    (1, "Nimbus Platform Migration", 1, "in_progress", "2025-01-15", None, 850000, 7),
    (2, "Customer Portal Redesign", 1, "in_progress", "2025-03-01", None, 420000, 8),
    (3, "Data Warehouse Consolidation", 1, "planned", "2026-01-01", None, 600000, 9),
    (4, "Q3 Hiring Sprint", 2, "completed", "2025-06-01", "2025-09-01", 120000, 12),
    (5, "Benefits Platform Rollout", 2, "in_progress", "2025-05-01", None, 200000, 13),
    (6, "FY26 Budget Planning", 3, "in_progress", "2025-08-01", None, 90000, 14),
    (7, "Expense Automation Rollout", 3, "completed", "2024-11-01", "2025-02-01", 150000, 15),
    (8, "Enterprise Sales Expansion", 4, "in_progress", "2025-02-01", None, 700000, 16),
    (9, "Outbound SDR Program", 4, "in_progress", "2025-04-01", None, 300000, 17),
    (10, "Zero Trust Network Rollout", 5, "in_progress", "2025-01-20", None, 500000, 18),
    (11, "Helpdesk Ticketing Upgrade", 5, "completed", "2024-09-01", "2025-01-10", 80000, 19),
    (12, "Brand Refresh 2026", 6, "planned", "2026-01-15", None, 250000, 20),
    (13, "Q4 Demand Gen Campaign", 6, "in_progress", "2025-07-01", None, 310000, 21),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, ?)", DEPARTMENTS)
    cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", EMPLOYEES)
    cur.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)", PROJECTS)
    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with {len(DEPARTMENTS)} departments, "
          f"{len(EMPLOYEES)} employees, {len(PROJECTS)} projects.")


if __name__ == "__main__":
    main()
