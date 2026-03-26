import { useEffect, useRef } from "react";
import { Network } from "vis-network/standalone";

function GraphView({ data }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
  console.log("FINAL GRAPH DATA:", data);

  if (!containerRef.current) return;

  let nodes = [];
  let edges = [];

  // =========================
  // 🔥 TRACE ORDER
  // =========================
  if (data?.order_id) {
    const orderId = data.order_id;

    nodes.push({
      id: orderId,
      label: `Order ${orderId}`,
      color: "#FFD700",
      size: 25
    });

    if (data.customer) {
      nodes.push({
        id: data.customer,
        label: `Customer ${data.customer}`,
        color: "#FF6B6B"
      });

      edges.push({
        from: orderId,
        to: data.customer,
        arrows: "to"
      });
    }

    data.items?.forEach((item) => {
      const itemId = `item_${item}`;

      nodes.push({
        id: itemId,
        label: `Item ${item}`,
        color: "#00C49F"
      });

      edges.push({
        from: orderId,
        to: itemId,
        arrows: "to"
      });
    });
  }

  // =========================
  // 🔥 FULL FLOW
  // =========================
  else if (data?.order) {
    nodes.push({
      id: data.order,
      label: `Order ${data.order}`,
      color: "#FFD700",
      size: 25
    });

    if (data.delivery) {
      nodes.push({ id: data.delivery, label: "Delivery", color: "#00C49F" });
      edges.push({ from: data.order, to: data.delivery, arrows: "to" });
    }

    if (data.billing) {
      nodes.push({ id: data.billing, label: "Billing", color: "#FF8042" });
      edges.push({ from: data.delivery, to: data.billing, arrows: "to" });
    }

    if (data.journal) {
      nodes.push({ id: data.journal, label: "Journal", color: "#AF19FF" });
      edges.push({ from: data.billing, to: data.journal, arrows: "to" });
    }
  }

  // =========================
  // 🔥 TOP PRODUCTS (FORCE FIX)
  // =========================
  else if (data && data.length) {

    const center = "TOP";

    nodes.push({
      id: center,
      label: "Top Products",
      color: "#FFD700",
      size: 30
    });

    data.forEach((p, i) => {
      const id = `p_${i}`;

      nodes.push({
        id,
        label: `${p.product}\n(${p.usage})`,
        color: "#36A2EB",
        size: 20
      });

      edges.push({
        from: center,
        to: id,
        arrows: "to"
      });
    });
  }

  // =========================
  // EMPTY
  // =========================
  else {
    nodes.push({ id: 1, label: "Ask something 👇" });
  }

  if (networkRef.current) networkRef.current.destroy();

  networkRef.current = new Network(
    containerRef.current,
    { nodes, edges },
    {
      nodes: { shape: "dot" },
      edges: { arrows: "to" },
      physics: { stabilization: false }
    }
  );
}, [data]);
  return (
    <div
      ref={containerRef}
      style={{
        height: "100%",
        width: "100%",
        background: "#f9f9f9"
      }}
    />
  );
}

export default GraphView;