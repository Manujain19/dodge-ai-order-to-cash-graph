import os
import json
import random
from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "Password123" 

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# ---------------------------
# LOAD JSONL
# ---------------------------
def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data


# ---------------------------
# GET CUSTOMER IDS (ROBUST)
# ---------------------------
def get_customer_ids(base):
    ids = []
    path = os.path.join(base, "business_partners")

    for file in os.listdir(path):
        rows = load_jsonl(os.path.join(path, file))

        for r in rows:
            cid = (
                r.get("BusinessPartner") or
                r.get("businessPartner") or
                r.get("id")
            )

            if cid:
                ids.append(str(cid))

    print(f"Loaded customer IDs: {len(ids)}")

    if not ids:
        raise Exception("❌ No customer IDs found! Check dataset format.")

    return ids


# ---------------------------
# INGEST CUSTOMERS
# ---------------------------
def ingest_customers(tx, rows):
    tx.run("""
    UNWIND $rows AS row
    WITH row
    WHERE row.BusinessPartner IS NOT NULL OR row.businessPartner IS NOT NULL OR row.id IS NOT NULL

    MERGE (c:Customer {
        id: coalesce(row.BusinessPartner, row.businessPartner, row.id)
    })
    """, rows=rows)


# ---------------------------
# INGEST ORDERS
# ---------------------------
def ingest_orders(tx, rows, customer_ids):
    new_rows = []

    for r in rows:
        order_id = r.get("salesOrder") or r.get("SalesOrder")

        if order_id:
            new_rows.append({
                "id": str(order_id),
                "customer_id": random.choice(customer_ids)
            })

    tx.run("""
    UNWIND $rows AS row
    MERGE (o:SalesOrder {id: row.id})
    SET o.customer_id = row.customer_id
    """, rows=new_rows)


# ---------------------------
# INGEST ITEMS
# ---------------------------
def ingest_items(tx, rows):
    for r in rows:
        tx.run("""
            MERGE (i:Item {id: $id})
            SET i.product_id = $product_id
        """, id=r["salesOrderItem"], product_id=r["material"])

# ---------------------------
# INGEST PRODUCTS
# ---------------------------
def ingest_products(tx, rows):
    tx.run("""
    UNWIND $rows AS row
    WITH row
    WHERE row.material IS NOT NULL

    MERGE (p:Product {id: row.material})
    """, rows=rows)

def ingest_flow(tx, rows):
    for r in rows:
        tx.run("""
        MERGE (o:SalesOrder {id:$order})
        MERGE (d:Delivery {id:$delivery})
        MERGE (b:Billing {id:$billing})
        MERGE (j:Journal {id:$journal})

        MERGE (o)-[:HAS_DELIVERY]->(d)
        MERGE (d)-[:HAS_BILLING]->(b)
        MERGE (b)-[:HAS_JOURNAL]->(j)
        """,
        order=r["salesOrder"],
        delivery=r.get("delivery_id", "D"+r["salesOrder"]),
        billing=r.get("billing_id", "B"+r["salesOrder"]),
        journal=r.get("journal_id", "J"+r["salesOrder"]))


# ---------------------------
# LINK ITEM → PRODUCT
# ---------------------------
def link_item_product(tx, rows):
    tx.run("""
    UNWIND $rows AS row
    WITH row
    WHERE row.salesOrderItem IS NOT NULL AND row.material IS NOT NULL

    MATCH (i:Item {id: row.salesOrderItem})
    MATCH (p:Product {id: row.material})

    MERGE (i)-[:OF_PRODUCT]->(p)
    """, rows=rows)


# ---------------------------
# LINK ORDER → CUSTOMER
# ---------------------------
def link_order_customer(tx):
    tx.run("""
    MATCH (o:SalesOrder)
    MATCH (c:Customer {id: o.customer_id})
    MERGE (o)-[:PLACED_BY]->(c)
    """)


# ---------------------------
# MAIN INGEST
# ---------------------------
def ingest_all(base):
    with driver.session() as session:

        print("Loading customer IDs...")
        customer_ids = get_customer_ids(base)

        # Customers
        print("Ingesting customers...")
        for f in os.listdir(base + "/business_partners"):
            rows = load_jsonl(base + "/business_partners/" + f)
            session.execute_write(ingest_customers, rows)

        # Orders
        print("Ingesting orders...")
        for f in os.listdir(base + "/sales_order_headers"):
            rows = load_jsonl(base + "/sales_order_headers/" + f)
            session.execute_write(ingest_orders, rows, customer_ids)
            print("Ingesting flow (Delivery → Billing → Journal)...")
            session.execute_write(ingest_flow, rows)

        # Items + product link
        print("Ingesting items...")
        for f in os.listdir(base + "/sales_order_items"):
            rows = load_jsonl(base + "/sales_order_items/" + f)
            session.execute_write(ingest_items, rows)
            session.execute_write(link_item_product, rows)

        # Products
        print("Ingesting products...")
        for f in os.listdir(base + "/products"):
            rows = load_jsonl(base + "/products/" + f)
            session.execute_write(ingest_products, rows)

        # Final relationship
        print("Linking orders to customers...")
        session.execute_write(link_order_customer)

        print("✅ Ingestion completed!")


# ---------------------------
if __name__ == "__main__":
    ingest_all("../../data/sap-order-to-cash-dataset")