# 🚀 Dodge AI – Order to Cash Graph System

## 📌 Overview
This project is an AI-powered Order-to-Cash system using a Neo4j graph database with a chat-based interface.

Users can:
- Trace orders
- Visualize relationships (Order → Customer → Items → Products)
- View full business flow
- Run basic analytics

---

## 🏗️ Architecture

### 🔹 Frontend
- React (Vite)
- vis-network (Graph visualization)

### 🔹 Backend
- FastAPI (Python)
- Neo4j Graph Database

### 🔹 AI Layer
- HuggingFace API (optional fallback enabled)

---

## 🔥 Features

### 1️⃣ Trace Order
trace order 740506
Returns:
- Customer
- Items
- Products
- Graph visualization

---

### 2️⃣ Full Flow
Full flow 740506
Returns:
Order → Delivery → Billing → Journal

---

### 3️⃣ Analytics
top products
Returns:
- Most used products

---

## 🧠 Guardrails

- Validates user input
- Prevents invalid queries
- Safe fallback if LLM fails
- Ensures structured responses

---

## ⚠️ Note on AI (LLM)

HuggingFace API is integrated but optional due to API limits.  
Core functionality works independently without it.

---

## ▶️ Run Locally

### 🔹 Backend
```bash
cd backend
uvicorn main:app --reload

### 🔹 Frontend

cd frontend
npm install
npm run dev

🌐 Access App

Frontend:
http://localhost:5173

Backend:
http://127.0.0.1:8000

📊 Tech Stack
React
FastAPI
Neo4j
vis-network
HuggingFace API

### Author
### Manu Jain ###
