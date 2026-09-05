import React, { useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  Bot,
  CheckCircle2,
  FileText,
  Loader2,
  Send,
  Sparkles,
  User,
  X,
} from 'lucide-react';
import { GuardianAPI } from '../../services/api';
import { AssistantQueryResponse } from '../../types';

interface CopilotChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  sender: 'user' | 'assistant';
  text: string;
  responseObj?: AssistantQueryResponse;
}

export const CopilotChatDrawer: React.FC<CopilotChatDrawerProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: 'Hello! I am GuardianEye Copilot, your grounded warehouse safety assistant. Ask me anything about active incidents, risk rules, root causes, or SOP compliance.',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSend = async (queryToSend?: string) => {
    const q = queryToSend || inputQuery;
    if (!q.trim() || loading) return;

    const userMsg: Message = { sender: 'user', text: q };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const resp = await GuardianAPI.queryAssistant(q);
      const botMsg: Message = {
        sender: 'assistant',
        text: resp.answer,
        responseObj: resp,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Unable to reach the assistant reasoning service. Please check your network connection.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 md:w-[480px] bg-[#0E131F] border-l border-white/10 z-50 flex flex-col shadow-2xl backdrop-blur-xl animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="h-16 px-6 border-b border-white/10 flex items-center justify-between bg-[#0B0F17]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white flex items-center gap-1.5">
              Grounded AI Copilot
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ZERO HALLUCINATION
              </span>
            </div>
            <div className="text-[10px] font-mono text-gray-400">
              Grounded in PostgreSQL & pgvector Logs
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Message History */}
      <div className="flex-1 p-6 overflow-y-auto space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-2 mb-1">
              {m.sender === 'assistant' ? (
                <>
                  <Bot className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-[10px] font-mono font-medium text-purple-300">
                    GUARDIAN COPILOT
                  </span>
                </>
              ) : (
                <>
                  <span className="text-[10px] font-mono font-medium text-blue-300">
                    SAFETY OFFICER
                  </span>
                  <User className="w-3.5 h-3.5 text-blue-400" />
                </>
              )}
            </div>

            <div
              className={`p-3.5 rounded-xl text-xs leading-relaxed max-w-[90%] ${
                m.sender === 'user'
                  ? 'bg-blue-600/30 border border-blue-500/40 text-blue-100 rounded-tr-none'
                  : 'bg-white/[0.04] border border-white/10 text-gray-200 rounded-tl-none'
              }`}
            >
              {m.text}

              {/* Citations block */}
              {m.responseObj?.grounded_citations && m.responseObj.grounded_citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
                  <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    Verified Evidence Citations:
                  </div>
                  {m.responseObj.grounded_citations.map((c, cIdx) => (
                    <div
                      key={cIdx}
                      className="p-2 rounded bg-black/40 border border-white/5 text-[11px] space-y-0.5"
                    >
                      <div className="font-semibold text-blue-300 flex items-center justify-between">
                        <span>{c.title}</span>
                        <span className="text-[9px] font-mono text-emerald-400">
                          {(c.confidence * 100).toFixed(0)}% MATCH
                        </span>
                      </div>
                      <div className="text-gray-400 text-[10px]">{c.snippet}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Suggested followups */}
              {m.responseObj?.suggested_followups && (
                <div className="mt-3 pt-2 border-t border-white/5 space-y-1">
                  <div className="text-[10px] text-gray-400">Suggested Inquiries:</div>
                  {m.responseObj.suggested_followups.map((f, fIdx) => (
                    <button
                      key={fIdx}
                      onClick={() => handleSend(f)}
                      className="w-full text-left text-[11px] text-purple-300 hover:text-white p-1.5 rounded hover:bg-purple-500/10 transition-colors flex items-center justify-between group"
                    >
                      <span>{f}</span>
                      <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-purple-400 font-mono py-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Consulting pgvector database knowledge base...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-white/10 bg-[#0B0F17]">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question about warehouse safety rules, incidents..."
            className="w-full bg-[#111827] border border-white/10 rounded-xl pl-4 pr-12 py-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 transition-colors"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputQuery.trim() || loading}
            className="absolute right-2 p-2 rounded-lg bg-purple-600/30 text-purple-400 border border-purple-500/40 hover:bg-purple-600/50 disabled:opacity-40 transition-all"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
