import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const chatEndRef = useRef(null);

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const sendMessage = async () => {
    if (!query.trim()) return;

    const userMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");

    try {
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      const botMessage = { role: "bot", content: data.response || "No response received." };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [...prev, { role: "bot", content: "Error retrieving response." }]);
    }
  };


  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message-container ${msg.role}`}>
            {msg.role === "bot" && <div className="profile-icon bot">🤖</div>}
            <div className={`message ${msg.role}`}>
              {msg.role === "bot" ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
            </div>
            {msg.role === "user" && <div className="profile-icon user">🧑</div>}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <div className="input-container">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask something..."
          className="input-box"
        />
        <button onClick={sendMessage} className="send-button">Send</button>
      </div>
    </div>
  );
}

export default App;
