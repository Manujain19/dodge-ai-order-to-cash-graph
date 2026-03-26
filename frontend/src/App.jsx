import { useState } from "react";
import GraphView from "./GraphView";
import Chat from "./Chat";

function App() {
  const [graphData, setGraphData] = useState(null);

  return (
    <div className="app-container">

      {/* LEFT GRAPH */}
      <div className="graph-container">
        <div className="graph-header">Graph View (Neo4j)</div>
        <GraphView data={graphData} />
      </div>

      {/* RIGHT CHAT */}
      <div className="chat-container">
        <div className="chat-header">Dodge AI 🤖</div>
        <Chat setGraphData={setGraphData} />
      </div>

    </div>
  );
}

export default App;