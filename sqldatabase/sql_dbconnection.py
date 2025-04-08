import sqlite3
import random
import datetime
from fastapi import HTTPException
import ollama
import logging
from configs.attributes import *

client = ollama.Client()

class SQLQueryBuilder:
    def __init__(self):
        self.table = Attributes.TABLE_NAME
        self.keyword_map = {
            "sales": Attributes.AMOUNT,
            "total": "SUM",
            "sum": "SUM",
            "id": Attributes.CUSTOMER_ID,
            "customer": Attributes.NAME,
            "phone": Attributes.PHONE,
            "furniture": ("filter", Attributes.PRODUCT_TYPE, "Furniture"),
            "electronics": ("filter", Attributes.PRODUCT_TYPE, "Electronics"),
            "appliances": ("filter", Attributes.PRODUCT_TYPE, "Appliances"),
            "groceries": ("filter", Attributes.PRODUCT_TYPE, "Groceries"),
            "ac": ("filter", Attributes.PRODUCT_NAME, "AC"),
            "air conditioner": ("filter", Attributes.PRODUCT_NAME, "AC"),
            "last month": ("time_filter", Attributes.DATE, "last_month"),
            "last 7 days": ("time_filter", Attributes.DATE, "last_7_days"),
        }

    def get_time_condition(self, field: str, phrase: str):
        if phrase == "last_month":
            return f"strftime('%Y-%m', {field}) = strftime('%Y-%m', 'now', '-1 month')"
        elif phrase == "last_7_days":
            return f"date({field}) >= date('now', '-7 days')"
        return ""

    def generate_sql_query(self, user_query: str) -> str:
        user_query = user_query.lower()
        select_func = None
        target_column = None
        conditions = []

        for phrase, mapping in self.keyword_map.items():
            if phrase in user_query:
                if isinstance(mapping, tuple):
                    if mapping[0] == "filter":
                        conditions.append(f"{mapping[1]} = '{mapping[2]}'")
                    elif mapping[0] == "time_filter":
                        time_cond = self.get_time_condition(mapping[1], mapping[2])
                        if time_cond:
                            conditions.append(time_cond)
                elif mapping == "SUM":
                    select_func = "SUM"
                else:
                    target_column = mapping

        if not target_column:
            target_column = Attributes.AMOUNT

        if select_func == "SUM":
            select_part = f"SUM({target_column})"
        else:
            select_part = "*"

        # Final SQL query
        query = f"SELECT {select_part} FROM {self.table}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return query

def get_db_connection():
    try:
        conn = sqlite3.connect("TariqueDB.db")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def generate_sql_with_llm(user_query: str) -> str:
    try:
        prompt = f"""
        You are an expert in converting natural language to SQL.
        Convert the following user query into a valid SQLite query:

        User query: "{user_query}"

        Refer to below information related to database 
            Table name: transactions
            Columns: customer_id, name, phone, product_type, product_name, amount, date

        Use below chain of thought to construct accurate and valid SQLite query.
            STEP 1: Analyze the intent of the user query like SELECT, SUM, COUNT etc.
            STEP 2: Target the column, that is which column id being queried for. (e.g., sales -> amount)
            STEP 3: Look for the filters, that what WHERE conditions apply. (e.g., "furniture", "last month")
            STEP 4: If STEP 1, STEP 2 and STEP 3 are successful then construct the sqlite query.
        
        Example 1:
            input: give me the total sales of electronics in last month
            output: output: SELECT SUM(amount) FROM transactions WHERE product_type = 'Electronics' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now', '-1 month')

        Example 2:
            input: Top-selling electronics products
            output: SELECT product_name FROM transactions WHERE product_type = 'Electronics' ORDER BY amount DESC LIMIT 1
        
        IMPORTANT NOTE: ONLY generate the SQL QUERY, and strictly NO TEXT should be generated along with the sql query. Look at the above example for reference. It should always start with 'SELECT'.
        """
        response = client.generate(model="llama3.1", prompt= str(prompt))
        #response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
        #sql_text = response['message']['content'].strip()
        sql_text = response.response
        print(":::sql_text:::",sql_text)
        if not sql_text.lower().startswith("select"):
            raise ValueError("LLM did not return a valid SQL SELECT query.")
        return sql_text
    except Exception as e:
        logging.error(f"LLM SQL generation failed: {e}")
        raise HTTPException(status_code=500, detail="SQL generation from LLM failed")


def generate_sql_query(user_query: str):
    builder = SQLQueryBuilder()
    return builder.generate_sql_query(user_query)

def save_response():
    pass 

def generate_dummy_data():
    conn = sqlite3.connect("TariqueDB.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        customer_id INTEGER,
        name TEXT,
        phone TEXT,
        product_type TEXT,
        product_name TEXT,
        amount REAL,
        date TEXT
    )
    """)

    first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Martinez"]
    product_types = ["Electronics", "Appliances", "Furniture", "Groceries"]
    products = {
        "Electronics": ["Laptop", "Smartphone", "Headphones", "Smartwatch", "Tablet"],
        "Appliances": ["AC", "Refrigerator", "Microwave", "Washing Machine", "Water Heater"],
        "Furniture": ["Sofa", "Dining Table", "Chair", "Bed", "Bookshelf"],
        "Groceries": ["Rice", "Flour", "Sugar", "Salt", "Oil"]
    }

    dummy_data = []
    start_date = datetime.datetime.today().replace(day=1) - datetime.timedelta(days=30)

    for _ in range(100):
        customer_id = random.randint(1000, 9999)
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        phone = "".join([str(random.randint(0, 9)) for _ in range(10)])
        product_type = random.choice(product_types)
        product_name = random.choice(products[product_type])
        amount = round(random.uniform(100, 5000), 2)
        date_of_purchase = (start_date + datetime.timedelta(days=random.randint(0, 29))).strftime("%Y-%m-%d")
        dummy_data.append((customer_id, name, phone, product_type, product_name, amount, date_of_purchase))

    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", dummy_data)
    conn.commit()
    conn.close()
    print("INSIDE DB::")
    print(dummy_data[:5])
    print("::END::")
