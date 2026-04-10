"use client";
import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";

function renderMarkdown(text: string) {
  // Split into lines, process each
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  lines.forEach((line, i) => {
    // Bold: **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
    // Bullet: lines starting with • or -
    const trimmed = line.trim();
    if (trimmed.startsWith("•") || trimmed.startsWith("- ")) {
      elements.push(<div key={i} style={{ paddingLeft: 8 }}>{rendered}</div>);
    } else {
      elements.push(<span key={i}>{rendered}</span>);
    }
    if (i < lines.length - 1) elements.push(<br key={`br-${i}`} />);
  });
  return <>{elements}</>;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED_QUESTIONS = [
  "How much time did Jordan spend on Insights Agent & Scaled AI?",
  "Which PM has the lowest priority alignment?",
  "Compare meeting hours across all PMs",
  "What are the biggest time sinks for Morgan?",
  "Show me Taylor's activity breakdown by source",
  "Give me a team overview",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(text, sessionId || undefined);
      setSessionId(res.context?.session_id || sessionId);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 pb-3">
        <h1 className="text-[24px] font-semibold flex items-center gap-2">
          <span style={{ color: "var(--ai-teal)" }}>✦</span> Ask the Agent
        </h1>
        <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
          Ask questions about your team&apos;s activities, time allocation, and priorities. All answers cite source data.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 space-y-4">
        {messages.length === 0 && (
          <div className="py-8">
            <div className="text-[14px] font-medium mb-4" style={{ color: "var(--text-secondary)" }}>
              Try asking:
            </div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-[12px] px-3 py-2 rounded-lg transition-colors"
                  style={{ background: "var(--card-bg)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-xl px-4 py-3 text-[13px] ${
                msg.role === "user" ? "text-white" : ""
              }`}
              style={{
                background: msg.role === "user" ? "var(--accent-blue)" : "var(--card-bg)",
                border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                color: msg.role === "user" ? "white" : "var(--text-primary)",
              }}
            >
              {msg.role === "assistant" && (
                <div className="flex items-center gap-1 mb-1">
                  <span style={{ color: "var(--ai-teal)" }}>✦</span>
                  <span className="text-[11px] font-medium" style={{ color: "var(--ai-teal)" }}>PM Agent</span>
                </div>
              )}
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="card px-4 py-3">
              <div className="flex items-center gap-2 text-[13px]" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--ai-teal)" }}>✦</span>
                Thinking...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-6 pt-3">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder="Ask about your team's activities..."
            className="flex-1 px-4 py-3 rounded-xl text-[13px]"
            style={{ background: "var(--card-bg)", border: "1px solid var(--border)" }}
            disabled={loading}
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl text-[13px] font-medium text-white disabled:opacity-50"
            style={{ background: "var(--accent-blue)" }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
