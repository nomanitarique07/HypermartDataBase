from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import sqlite3
import logging
import ollama
from sqldatabase.sql_dbconnection import generate_sql_query, get_db_connection, generate_sql_with_llm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()
client = ollama.Client()

class QueryRequest(BaseModel):
    user_query: str

@app.post("/query")
async def execute_query(request: Request, request_body: QueryRequest):
    try:
        
        raw_body = await request.body()
        logging.info(f"Raw request body: {raw_body.decode()}")

        cleaned_query = request_body.user_query.strip()
        logging.info(f"Received user query: {cleaned_query}")

        #sql_query = generate_sql_query(cleaned_query)
        sql_query = generate_sql_with_llm(cleaned_query)
        logging.info(f"Generated SQL query: {sql_query}")

        conn = get_db_connection()
        cursor = conn.cursor()
        #print("before execute")
        cursor.execute(sql_query)
        #print("after execute")
        results = cursor.fetchall()
        conn.close()
        logging.info(f"SQL Query Results: {results}")

        prompt = f"""You are a smart and professional query responder of a hypermart database. \n Use below chain of thought for response generation.
        
        STEP 1: Based on the user query received: {cleaned_query} and Generated SQL query: {sql_query} and response: {results}. Respond to the user as a sales expert in most professional way about the result.
        STEP 2: Once you have the response, try to give it in form table or markdown.
        STEP 3: Results are mostly about cost, total sales, products type or product name, customer name, date etc. Articulate the response based on the query context in ONLY two or three line.
        
        IMPORTANT NOTE: 
        1) DO NOT assume or guess the data. Give the accurate, concise and to the point response to a query. DO NOT generate any extra text which is out of context.
        2) Only give response and not the sql query and do not explain the response.
        3) DO NOT add salutation in the beggening or end.
        
        """
        #llm_response = ollama.chat(model="deepseek-r1", messages=[{"role": "user", "content": str(results)}])
        llm_response = client.generate(model="llama3.1", prompt= str(prompt)) #deepseek-r1:7b
        logging.info(f"LLM Response: {llm_response.response}")

        return {"query": sql_query, "results": results, "llm_response": llm_response}
    
    except sqlite3.Error as e:
        logging.error(f"SQL execution error: {e}")
        raise HTTPException(status_code=500, detail=f"SQL execution failed: {str(e)}")
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
