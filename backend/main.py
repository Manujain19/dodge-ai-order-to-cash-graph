from fastapi import FastAPI
from pydantic import BaseModel
from neo4j import GraphDatabase
import requests
from fastapi.middleware.cors import CORSMiddleware
import os

# =========================
# 🔌 CONFIG
# =========================

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Password123"   # change this

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 👉 Hugging Face API Key
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 📦 REQUEST MODEL
# =========================

class QueryRequest(BaseModel):
    query: str


# =========================
# 🛡️ GUARDRAILS
# =========================

def is_valid_query(query: str):
    keywords = [
        "order", "customer", "product", "item",
        "billing", "delivery", "journal", "flow"
    ]
    return any(k in query.lower() for k in keywords)


# =========================
# 🧠 INTENT PARSER
# =========================

def parse_query(q):
    q = q.lower()

    if "trace" in q and "order" in q:
        return "TRACE_ORDER"

    elif "full flow" in q or "flow" in q:
        return "FULL_FLOW"

    elif "top product" in q or "most used" in q:
        return "ANALYTICS"

    elif "broken" in q or "missing" in q:
        return "ANOMALY"

    else:
        return "UNKNOWN"


# =========================
# 🔍 TRACE ORDER
# =========================

def trace_order(order_id):
    with driver.session() as session:
        result = session.run("""
        MATCH (o:Order {id:$id})
        OPTIONAL MATCH (o)-[:PLACED_BY]->(c:Customer)
        OPTIONAL MATCH (o)-[:HAS_ITEM]->(i:Item)
        OPTIONAL MATCH (i)-[:OF_PRODUCT]->(p:Product)

        RETURN o.id AS order_id,
               c.id AS customer,
               collect(DISTINCT i.id) AS items,
               collect(DISTINCT p.id) AS products
        """, id=order_id)

        record = result.single()

        if not record:
            return {"error": "Order not found"}

        return {
            "order_id": record["order_id"],
            "customer": record["customer"],
            "items": record["items"],
            "products": record["products"],
            "summary": f"Order {order_id} contains {len(record['items'])} items"
        }

# =========================
# 🔗 FULL FLOW
# =========================

def run_full_flow(order_id):
    with driver.session() as session:
        result = session.run("""
        MATCH (o:Order {id:$id})
        OPTIONAL MATCH (o)-[:HAS_DELIVERY]->(d)
        OPTIONAL MATCH (d)-[:HAS_BILLING]->(b)
        OPTIONAL MATCH (b)-[:HAS_JOURNAL]->(j)

        RETURN o.id AS order,
               d.id AS delivery,
               b.id AS billing,
               j.id AS journal
        """, id=order_id)

        record = result.single()

        return {
            "order": record["order"],
            "delivery": record["delivery"],
            "billing": record["billing"],
            "journal": record["journal"],
            "summary": f"Order {order_id} → Delivery {record['delivery']} → Billing {record['billing']} → Journal {record['journal']}"
        }


# =========================
# 📊 ANALYTICS
# =========================

def top_products():
    with driver.session() as session:
        result = session.run("""
        MATCH (i:Item)-[:OF_PRODUCT]->(p:Product)
        RETURN p.id AS product, count(*) AS usage
        ORDER BY usage DESC
        LIMIT 5
        """)
        return [dict(r) for r in result]


# =========================
# 🚨 ANOMALY DETECTION
# =========================

def detect_anomalies():
    with driver.session() as session:
        result = session.run("""
        MATCH (o:SalesOrder)

        OPTIONAL MATCH (o)-[:HAS_DELIVERY]->(d)
        OPTIONAL MATCH (d)-[:HAS_BILLING]->(b)
        OPTIONAL MATCH (b)-[:HAS_JOURNAL]->(j)

        WITH o,
             CASE 
                WHEN d IS NULL THEN "Missing Delivery"
                WHEN b IS NULL THEN "Missing Billing"
                WHEN j IS NULL THEN "Missing Journal"
                ELSE "OK"
             END AS status

        WHERE status <> "OK"

        RETURN o.id AS order_id, status
        LIMIT 20
        """)

        return [dict(r) for r in result]


# =========================
# 🤖 HUGGING FACE → CYPHER
# =========================

def gpt_to_cypher(user_query):
    prompt = f"""
    Convert the following natural language into a Neo4j Cypher query.

    Schema:
    SalesOrder-[:HAS_ITEM]->Item-[:OF_PRODUCT]->Product
    SalesOrder-[:PLACED_BY]->Customer
    SalesOrder-[:HAS_DELIVERY]->Delivery-[:HAS_BILLING]->Billing-[:HAS_JOURNAL]->Journal

    Query: {user_query}

    Only return Cypher query.
    """

    response = requests.post(
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={"inputs": prompt}
    )

    result = response.json()

    try:
        return result[0]["generated_text"]
    except:
        return "MATCH (o:SalesOrder) RETURN o LIMIT 5"

import requests

def test_huggingface():
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }

    payload = {
        "inputs": "Explain order to cash process in 1 line"
    }

    response = requests.post(HF_URL, headers=headers, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())

def run_dynamic_query(user_query):
    cypher = gpt_to_cypher(user_query)

    try:
        with driver.session() as session:
            result = session.run(cypher)
            return {
                "generated_cypher": cypher,
                "result": [dict(r) for r in result]
            }
    except Exception as e:
        return {
            "error": str(e),
            "generated_cypher": cypher
        }


# =========================
# 🚀 MAIN API
# =========================

@app.post("/query")
def query(request: QueryRequest):

    user_query = request.query

    # 🛡️ Guardrail
    if not is_valid_query(user_query):
        return {
            "error": "This system only answers Order-to-Cash dataset queries."
        }

    intent = parse_query(user_query)

    try:
        if intent == "TRACE_ORDER":
            order_id = user_query.split()[-1]
            return trace_order(order_id)

        elif intent == "FULL_FLOW":
            order_id = user_query.split()[-1]
            return run_full_flow(order_id)

        elif intent == "ANALYTICS":
            return top_products()

        elif intent == "ANOMALY":
            return detect_anomalies()

        elif intent == "UNKNOWN":
            return run_dynamic_query(user_query)

        else:
            return {"error": "Could not understand query"}

    except Exception as e:
        return {"error": str(e)}


# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {"message": "Order-to-Cash Graph API (HF Powered) 🚀"}

if __name__ == "__main__":
    test_huggingface()