import React, { useState } from "react";
import axios from "axios";

function ChatBox() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false); // New state

  const sendMessage = async () => {
    if (!message.trim()) return;
    const userMsg = { role: "user", content: message };
    setChat(prev => [...prev, userMsg]);
    setMessage("");
    setLoading(true); // Show typing indicator

    try {
      const res = await axios.post("http://localhost:4000/chat", { message });
      const botReply = { role: "bot", content: res.data.response };
      setChat(prev => [...prev, botReply]);
    } catch {
      setChat(prev => [...prev, { role: "bot", content: " Server error." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      <h2>Chatbot</h2>
      <div style={{
        border: "1px solid #ccc", padding: 10, height: 300,
        overflowY: "auto", position: "relative"
      }}>
        {chat.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.role === "user" ? "right" : "left" }}>
            <strong>{msg.role === "user" ? "You" : "Bot"}:</strong> {msg.content}
          </div>
        ))}

        {loading && (
          <div style={{ position: "absolute", bottom: 10, left: 10, fontStyle: "italic" }}>
            Bot is typing...
          </div>
        )}
      </div>

      <div style={{ marginTop: 10 }}>
        <input
          type="text"
          value={message}
          onChange={e => setMessage(e.target.value)}
          style={{ width: "80%", padding: 10 }}
          placeholder="Type your message..."
          onKeyDown={e => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage} style={{ padding: 10, marginLeft: 10 }} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatBox;
