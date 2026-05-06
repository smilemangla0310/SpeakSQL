"""
SpeakSQL — Demo database seeder.
Creates and populates a SQLite database with HR + Sales data.
"""

import os, random, datetime
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import StaticPool

DEPARTMENTS = [
    ("Engineering", "San Francisco"), ("Marketing", "New York"),
    ("Sales", "Chicago"), ("Human Resources", "New York"),
    ("Finance", "San Francisco"), ("Operations", "Austin"),
    ("Customer Support", "Denver"), ("Research & Development", "Seattle"),
]

FIRST_NAMES = [
    "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "David","Elizabeth","William","Barbara","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Christopher","Karen","Charles","Lisa","Daniel","Nancy",
    "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Steven","Emily",
    "Andrew","Michelle","Joshua","Carol","Kenneth","Amanda","Kevin","Dorothy",
    "Brian","Melissa","George","Deborah","Timothy","Stephanie","Ronald","Rebecca",
    "Jason","Laura","Jeffrey","Cynthia","Ryan","Kathleen","Jacob","Amy",
    "Nicholas","Angela","Eric","Anna","Jonathan","Brenda","Stephen","Pamela",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Clark","Lewis","Robinson","Walker","Young","Allen",
    "King","Wright","Scott","Torres","Nguyen","Hill","Green","Adams","Nelson",
    "Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts","Phillips",
]

CITIES = [
    "New York","Los Angeles","Chicago","Houston","Phoenix","San Diego",
    "Dallas","San Francisco","Austin","Seattle","Denver","Boston","Portland","Miami",
]

PRODUCTS = [
    ("Laptop Pro 15","Electronics",1299.99),("Wireless Mouse","Electronics",29.99),
    ("Mechanical Keyboard","Electronics",149.99),("4K Monitor 27in","Electronics",449.99),
    ("USB-C Hub","Electronics",59.99),("Noise Cancelling Headphones","Electronics",299.99),
    ("Webcam HD","Electronics",79.99),("External SSD 1TB","Electronics",109.99),
    ("Standing Desk","Furniture",599.99),("Ergonomic Chair","Furniture",449.99),
    ("Desk Lamp LED","Furniture",45.99),("Monitor Stand","Furniture",89.99),
    ("Cable Management Kit","Accessories",24.99),("Laptop Stand","Accessories",49.99),
    ("Mouse Pad XL","Accessories",19.99),("Screen Protector","Accessories",14.99),
    ("Bluetooth Speaker","Electronics",89.99),("Smart Watch","Electronics",249.99),
    ("Tablet 10in","Electronics",399.99),("Power Bank 20000mAh","Electronics",39.99),
    ("Office Whiteboard","Furniture",129.99),("Filing Cabinet","Furniture",199.99),
    ("Desk Organizer","Accessories",34.99),("Wireless Charger","Electronics",29.99),
    ("Graphics Tablet","Electronics",199.99),("Docking Station","Electronics",179.99),
    ("Webcam Ring Light","Accessories",25.99),("Laptop Bag","Accessories",69.99),
    ("Privacy Screen Filter","Accessories",39.99),("Surge Protector","Electronics",34.99),
]

JOB_TITLES = [
    "Software Engineer","Senior Software Engineer","Staff Engineer",
    "Product Manager","Marketing Specialist","Sales Representative",
    "Account Executive","HR Coordinator","HR Manager","Financial Analyst",
    "Operations Manager","Support Specialist","Data Analyst",
    "Research Scientist","UX Designer","DevOps Engineer","QA Engineer",
    "Technical Lead","Engineering Manager","Marketing Manager",
    "Sales Manager","Finance Manager","Director of Sales",
]


def seed_demo_database(db_path: str) -> str:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_engine(f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, _):
        dbapi_conn.cursor().execute("PRAGMA foreign_keys=ON")

    random.seed(42)

    with engine.connect() as c:
        # ── DDL ──────────────────────────────────────────────────────
        c.execute(text("CREATE TABLE departments (department_id INTEGER PRIMARY KEY AUTOINCREMENT, department_name TEXT NOT NULL, location TEXT NOT NULL)"))
        c.execute(text("CREATE TABLE employees (employee_id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, hire_date TEXT NOT NULL, job_title TEXT NOT NULL, department_id INTEGER NOT NULL, manager_id INTEGER, FOREIGN KEY(department_id) REFERENCES departments(department_id), FOREIGN KEY(manager_id) REFERENCES employees(employee_id))"))
        c.execute(text("CREATE TABLE salaries (salary_id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL, amount REAL NOT NULL, effective_date TEXT NOT NULL, FOREIGN KEY(employee_id) REFERENCES employees(employee_id))"))
        c.execute(text("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL, registration_date TEXT NOT NULL)"))
        c.execute(text("CREATE TABLE products (product_id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, category TEXT NOT NULL, unit_price REAL NOT NULL, stock_quantity INTEGER NOT NULL DEFAULT 100)"))
        c.execute(text("CREATE TABLE orders (order_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, order_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'completed', total_amount REAL NOT NULL DEFAULT 0, FOREIGN KEY(customer_id) REFERENCES customers(customer_id))"))
        c.execute(text("CREATE TABLE order_items (item_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL, line_total REAL NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(order_id), FOREIGN KEY(product_id) REFERENCES products(product_id))"))
        c.commit()

        # ── Departments ──────────────────────────────────────────────
        for n, l in DEPARTMENTS:
            c.execute(text("INSERT INTO departments(department_name,location) VALUES(:n,:l)"), {"n": n, "l": l})
        c.commit()

        # ── Employees (120) ──────────────────────────────────────────
        emails = set()
        for i in range(120):
            fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            em = f"{fn.lower()}.{ln.lower()}@company.com"
            s = 1
            while em in emails:
                em = f"{fn.lower()}.{ln.lower()}{s}@company.com"; s += 1
            emails.add(em)
            hd = datetime.date(random.randint(2018,2025), random.randint(1,12), random.randint(1,28)).isoformat()
            jt = random.choice(JOB_TITLES)
            did = random.randint(1, len(DEPARTMENTS))
            mid = random.randint(1, max(1, i)) if i > 5 else None
            c.execute(text("INSERT INTO employees(first_name,last_name,email,hire_date,job_title,department_id,manager_id) VALUES(:a,:b,:c,:d,:e,:f,:g)"),
                      {"a":fn,"b":ln,"c":em,"d":hd,"e":jt,"f":did,"g":mid})
        c.commit()

        # ── Salaries ─────────────────────────────────────────────────
        for eid in range(1, 121):
            base = random.randint(55000, 180000)
            for j in range(random.randint(1, 3)):
                amt = base + j * random.randint(3000, 12000)
                dt = datetime.date(2022+j, random.randint(1,12), 1).isoformat()
                c.execute(text("INSERT INTO salaries(employee_id,amount,effective_date) VALUES(:a,:b,:c)"), {"a":eid,"b":amt,"c":dt})
        c.commit()

        # ── Customers (50) ───────────────────────────────────────────
        states = ["CA","NY","TX","IL","AZ","PA","WA","CO","FL","GA","OR","MA"]
        cemails = set()
        for _ in range(50):
            fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            em = f"{fn.lower()}.{ln.lower()}@email.com"
            s = 1
            while em in cemails:
                em = f"{fn.lower()}.{ln.lower()}{s}@email.com"; s += 1
            cemails.add(em)
            c.execute(text("INSERT INTO customers(first_name,last_name,email,city,state,registration_date) VALUES(:a,:b,:c,:d,:e,:f)"),
                      {"a":fn,"b":ln,"c":em,"d":random.choice(CITIES),"e":random.choice(states),
                       "f":datetime.date(random.randint(2021,2024),random.randint(1,12),random.randint(1,28)).isoformat()})
        c.commit()

        # ── Products ─────────────────────────────────────────────────
        for n, cat, p in PRODUCTS:
            c.execute(text("INSERT INTO products(product_name,category,unit_price,stock_quantity) VALUES(:a,:b,:c,:d)"),
                      {"a":n,"b":cat,"c":p,"d":random.randint(20,500)})
        c.commit()

        # ── Orders (200) + Items ─────────────────────────────────────
        statuses = ["completed"]*3 + ["shipped","processing","cancelled"]
        for oid in range(1, 201):
            od = datetime.date(random.choice([2023,2023,2024,2024,2024,2025]), random.randint(1,12), random.randint(1,28)).isoformat()
            c.execute(text("INSERT INTO orders(customer_id,order_date,status,total_amount) VALUES(:a,:b,:c,0)"),
                      {"a":random.randint(1,50),"b":od,"c":random.choice(statuses)})
        c.commit()

        for oid in range(1, 201):
            total = 0.0
            used = set()
            for _ in range(random.randint(1, 4)):
                pid = random.randint(1, len(PRODUCTS))
                while pid in used: pid = random.randint(1, len(PRODUCTS))
                used.add(pid)
                qty = random.randint(1, 5)
                pr = PRODUCTS[pid-1][2]
                lt = round(qty * pr, 2)
                total += lt
                c.execute(text("INSERT INTO order_items(order_id,product_id,quantity,unit_price,line_total) VALUES(:a,:b,:c,:d,:e)"),
                          {"a":oid,"b":pid,"c":qty,"d":pr,"e":lt})
            c.execute(text("UPDATE orders SET total_amount=:t WHERE order_id=:o"), {"t":round(total,2),"o":oid})
        c.commit()

    engine.dispose()
    return f"Demo database created at {db_path}"


if __name__ == "__main__":
    print(seed_demo_database(os.path.join(os.path.dirname(__file__), "demo.db")))
