# 🧠 Natural Language to SQL Query Generator

This project demonstrates a streamlined NLP-to-SQL pipeline that converts layman-style user queries into executable SQL queries using rule-based logic and a large language model (LLaMA 3). Built with **FastAPI** and **SQLite**, it serves as a learning project for database-driven query systems enhanced by large language models.

---

## 📁 Project Structure

```
├── main.py           
├── sql_engine.py     
├── configs/
│   └── attributes.py 
├── TariqueDB.db     
└── README.md
```

---

## 🚀 Features

- 🔎 Converts natural language queries into SQL  
- 🧱 Uses SQLite for backend database  
- 🤖 Employs LLaMA 3 via Ollama for SQL generation  
- 📊 Outputs tabular results and a brief summary  

---

## 💡 Example

- **Input (User Query):**

```json
{ "user_query": "Top-selling groceries products" }
```

- **Output:**

```json
{
  "query": "SELECT product_name FROM transactions WHERE product_type = 'Groceries' ORDER BY amount DESC LIMIT 1",
  "results": ["Flour"]
}
```

- **Console Output:**  
  `Flour` is the top-selling grocery product, indicating a high demand for baking essentials.

---

## 🧰 Tech Stack

| Component     | Technology            |
|---------------|------------------------|
| API           | FastAPI (RESTful API) |
| Database      | SQLite (lightweight DB)|
| LLM           | LLaMA 3 via Ollama     |
| Language      | Python (3.10+)         |
