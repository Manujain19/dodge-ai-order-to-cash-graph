import { useState } from "react";

function Chat({ setGraphData }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await fetch("https://dodge-ai-order-to-cash-graph.onrender.com/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });

      const data = await res.json();

      console.log("FINAL GRAPH DATA:", data);

      // 🔥 THIS UPDATES GRAPH
      setGraphData({ ...data });

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: JSON.stringify(data, null, 2),
        },
      ]);
    } catch (err) {
      console.error(err);
    }

    setInput("");
  };

  return (
    <>
      <div style={{ flex: 1, padding: "10px", overflowY: "auto" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.role === "user" ? "right" : "left", margin: "10px 0" }}>
            <span
              style={{
                background: msg.role === "user" ? "#007bff" : "#eee",
                color: msg.role === "user" ? "#fff" : "#000",
                padding: "8px",
                borderRadius: "10px",
                display: "inline-block",
                maxWidth: "90%"
              }}
            >
              {msg.text}
            </span>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", padding: "10px", borderTop: "1px solid #ddd" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ flex: 1, padding: "8px" }}
          placeholder="Ask something..."
        />
        <button onClick={sendMessage} style={{ marginLeft: "10px" }}>
          Send
        </button>
      </div>
    </>
  );
}

export default Chat;
