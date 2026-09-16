import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, CheckCircle2, FileText, Sparkles, RefreshCw } from "lucide-react";

const API_BASE_URL = "http://localhost:8000/api";

export default function App() {
  const [sessionId] = useState(() => "session-" + Math.random().toString(36).substring(2, 9));
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! Welcome to the Tech Incubator at Queens College (TIQC). I'm here to help scope your project. To start, could you tell me a bit about your business or project idea?",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [brief, setBrief] = useState(null);
  const [generatingBrief, setGeneratingBrief] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim() || loading || isComplete) return;

    const userMessage = { role: "user", content: inputValue.trim() };
    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setInputValue("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          messages: updatedMessages,
        }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const data = await response.json();
      setMessages((prev) => [...prev, data.message]);

      if (data.is_ready_for_brief) {
        setIsComplete(true);
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I had trouble connecting to the server. Please check your backend connection.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateBrief = async () => {
    setGeneratingBrief(true);
    try {
      const response = await fetch(`${API_BASE_URL}/brief/generate?session_id=${sessionId}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to generate brief");
      const data = await response.json();
      setBrief(data);
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingBrief(false);
    }
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.headerBrand}>
          <Sparkles size={22} color="#0052cc" />
          <h1 style={styles.title}>TIQC Client Intake Assistant</h1>
        </div>
        <span style={styles.badge}>Live Discovery</span>
      </header>

      <div style={styles.container}>
        {/* Chat Section */}
        <div style={styles.chatCard}>
          <div style={styles.messageList}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  ...styles.messageRow,
                  justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                {msg.role === "assistant" && (
                  <div style={{ ...styles.avatar, background: "#e9f2ff", color: "#0052cc" }}>
                    <Bot size={16} />
                  </div>
                )}
                <div
                  style={{
                    ...styles.bubble,
                    ...(msg.role === "user" ? styles.userBubble : styles.botBubble),
                  }}
                >
                  {msg.content}
                </div>
                {msg.role === "user" && (
                  <div style={{ ...styles.avatar, background: "#f0f0f0", color: "#333" }}>
                    <User size={16} />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div style={styles.typingIndicator}>
                <div style={styles.avatar}>
                  <Bot size={16} />
                </div>
                <div style={styles.typingBubble}>TIQC Bot is typing...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Completion Banner */}
          {isComplete && !brief && (
            <div style={styles.completionBanner}>
              <CheckCircle2 size={20} color="#16a34a" />
              <div style={{ flex: 1 }}>
                <strong>Intake details captured!</strong>
                <p style={{ margin: "2px 0 0", fontSize: "13px", color: "#475569" }}>
                  All baseline discovery details are ready for staff review.
                </p>
              </div>
              <button
                style={styles.actionBtn}
                onClick={handleGenerateBrief}
                disabled={generatingBrief}
              >
                {generatingBrief ? <RefreshCw size={14} className="spin" /> : <FileText size={14} />}
                Generate Draft Brief
              </button>
            </div>
          )}

          {/* Message Input */}
          <form onSubmit={handleSendMessage} style={styles.inputContainer}>
            <input
              type="text"
              placeholder={
                isComplete
                  ? "Intake complete. Review the project brief below!"
                  : "Type your answer here..."
              }
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={loading || isComplete}
              style={styles.input}
            />
            <button
              type="submit"
              disabled={loading || !inputValue.trim() || isComplete}
              style={{
                ...styles.sendBtn,
                opacity: loading || !inputValue.trim() || isComplete ? 0.5 : 1,
              }}
            >
              <Send size={16} />
            </button>
          </form>
        </div>

        {/* Generated Brief Display */}
        {brief && (
          <div style={styles.briefCard}>
            <div style={styles.briefHeader}>
              <FileText size={20} color="#0052cc" />
              <h2 style={styles.briefTitle}>Auto-Generated Project Brief (Internal Draft)</h2>
            </div>
            <div style={styles.briefMeta}>
              <div style={styles.briefItem}>
                <span style={styles.label}>Client / Business</span>
                <strong>{brief.client_name_or_business}</strong>
              </div>
              <div style={styles.briefItem}>
                <span style={styles.label}>Suggested TIQC Service</span>
                <span style={styles.servicePill}>{brief.suggested_service_category}</span>
              </div>
              <div style={styles.briefItem}>
                <span style={styles.label}>Timeline</span>
                <span>{brief.target_timeline}</span>
              </div>
              <div style={styles.briefItem}>
                <span style={styles.label}>Estimated Budget</span>
                <span>{brief.rough_budget_range}</span>
              </div>
            </div>

            <div style={styles.section}>
              <h3 style={styles.sectionHeading}>Current Situation</h3>
              <p style={styles.sectionText}>{brief.current_situation}</p>
            </div>

            <div style={styles.section}>
              <h3 style={styles.sectionHeading}>Goals & Key Needs</h3>
              <ul style={styles.bulletList}>
                {brief.goals_and_needs.map((goal, i) => (
                  <li key={i}>{goal}</li>
                ))}
              </ul>
            </div>

            <div style={styles.section}>
              <h3 style={{ ...styles.sectionHeading, color: "#b45309" }}>
                Flagged Unknowns for Discovery Call
              </h3>
              <ul style={styles.flaggedList}>
                {brief.flagged_unknowns.map((flag, i) => (
                  <li key={i}>{flag}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: "#f8fafc",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    padding: "16px 28px",
    backgroundColor: "#ffffff",
    borderBottom: "1px solid #e2e8f0",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerBrand: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  title: {
    fontSize: "18px",
    fontWeight: "700",
    color: "#0f172a",
    margin: 0,
  },
  badge: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#0052cc",
    backgroundColor: "#e9f2ff",
    padding: "4px 10px",
    borderRadius: "12px",
  },
  container: {
    flex: 1,
    maxWidth: "850px",
    width: "100%",
    margin: "24px auto",
    padding: "0 16px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  chatCard: {
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #e2e8f0",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    display: "flex",
    flexDirection: "column",
    height: "550px",
  },
  messageList: {
    flex: 1,
    overflowY: "auto",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },
  messageRow: {
    display: "flex",
    alignItems: "flex-end",
    gap: "8px",
  },
  avatar: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  bubble: {
    maxWidth: "75%",
    padding: "12px 16px",
    borderRadius: "14px",
    fontSize: "14px",
    lineHeight: "1.5",
  },
  botBubble: {
    backgroundColor: "#f1f5f9",
    color: "#1e293b",
    borderBottomLeftRadius: "4px",
  },
  userBubble: {
    backgroundColor: "#0052cc",
    color: "#ffffff",
    borderBottomRightRadius: "4px",
  },
  typingIndicator: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "#64748b",
    fontSize: "13px",
  },
  typingBubble: {
    backgroundColor: "#f1f5f9",
    padding: "8px 14px",
    borderRadius: "14px",
    fontStyle: "italic",
  },
  completionBanner: {
    margin: "0 16px 12px",
    padding: "12px 16px",
    backgroundColor: "#f0fdf4",
    border: "1px solid #bbf7d0",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  actionBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    backgroundColor: "#16a34a",
    color: "#fff",
    border: "none",
    padding: "8px 14px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: "600",
  },
  inputContainer: {
    display: "flex",
    padding: "12px 16px",
    borderTop: "1px solid #e2e8f0",
    gap: "10px",
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    fontSize: "14px",
    outline: "none",
  },
  sendBtn: {
    backgroundColor: "#0052cc",
    color: "#fff",
    border: "none",
    padding: "10px 14px",
    borderRadius: "8px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  briefCard: {
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px solid #e2e8f0",
    padding: "24px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  },
  briefHeader: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    borderBottom: "1px solid #f1f5f9",
    paddingBottom: "12px",
    marginBottom: "16px",
  },
  briefTitle: {
    fontSize: "16px",
    fontWeight: "700",
    color: "#0f172a",
    margin: 0,
  },
  briefMeta: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "14px",
    marginBottom: "20px",
  },
  briefItem: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  label: {
    fontSize: "11px",
    fontWeight: "600",
    textTransform: "uppercase",
    color: "#64748b",
  },
  servicePill: {
    display: "inline-block",
    backgroundColor: "#eff6ff",
    color: "#1d4ed8",
    padding: "4px 8px",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: "600",
    width: "fit-content",
  },
  section: {
    marginTop: "16px",
  },
  sectionHeading: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: "6px",
  },
  sectionText: {
    fontSize: "13px",
    color: "#475569",
    lineHeight: "1.5",
    margin: 0,
  },
  bulletList: {
    margin: "4px 0 0 18px",
    padding: 0,
    fontSize: "13px",
    color: "#475569",
  },
  flaggedList: {
    margin: "4px 0 0 18px",
    padding: 0,
    fontSize: "13px",
    color: "#92400e",
  },
};