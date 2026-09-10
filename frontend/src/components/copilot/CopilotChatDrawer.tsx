import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ArrowUp,
  Bot,
  CheckCircle2,
  Loader2,
  Sparkles,
  TrendingDown,
  TrendingUp,
  User,
  X,
} from 'lucide-react';
import { GuardianAPI } from '../../services/api';
import { AssistantQueryResponse, ComparisonMetric } from '../../types';

function directionColor(direction: ComparisonMetric['direction']): string {
  // Direction alone doesn't say if a metric getting bigger is good or bad
  // (more incidents = worse, but a longer response time is also worse) —
  // every metric this assistant compares is something you want to see
  // DECREASE, so that mapping holds for all of them today.
  if (direction === 'DECREASED') return '#15803d';
  if (direction === 'INCREASED') return '#b91c1c';
  return '#6F7F98';
}

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
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: 'Hello! I am GuardianEye Copilot, your grounded warehouse safety assistant. Ask me anything about active incidents, risk rules, root causes, or SOP compliance.',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

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
        text: resp.answer || 'I could not find verified evidence for that request in the warehouse records.',
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

  // Not wrapped in AnimatePresence: only the mount plays the slide-in
  // transition. Closing (Escape, header ✕) removes the drawer from the
  // DOM in the same tick as isOpen flips to false, rather than waiting
  // out an exit animation — keeps Escape-to-close synchronous.
  if (!isOpen) return null;

  return (
    <>
      <motion.div
        className="fixed inset-0 z-40 bg-[#18243A]/25 md:hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.15 }}
        onClick={onClose}
      />
      <motion.div
        className="fixed inset-y-0 right-0 w-96 md:w-[480px] bg-white border-l border-[#E9EDF2] z-50 flex flex-col shadow-[0_0_0_1px_rgba(4,23,43,0.05),0_20px_60px_rgba(0,0,0,0.12)]"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        transition={{ duration: 0.28, ease: [0.4, 0, 0.2, 1] }}
      >
        {/* Drawer Header */}
        <div className="h-16 px-6 border-b border-[#E9EDF2] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#EAF0FF] flex items-center justify-center text-[#2F52D6]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#18243A] flex items-center gap-1.5">
                Grounded AI Copilot
                <span className="px-1.5 py-0.5 rounded-full text-[9px] font-semibold bg-[rgba(21,128,61,0.1)] text-[#15803d]">
                  ZERO HALLUCINATION
                </span>
              </div>
              <div className="text-[10px] text-[#6F7F98]">
                Verified incidents, risk assessments &amp; SOP rules only
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close copilot"
            className="p-1.5 rounded-full text-[#6F7F98] hover:text-[#18243A] hover:bg-[#F1F5F9] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message History */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          {messages.map((m, idx) => (
            <motion.div
              key={idx}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-center gap-2 mb-1">
                {m.sender === 'assistant' ? (
                  <>
                    <Bot className="w-3.5 h-3.5 text-[#2F52D6]" />
                    <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#2F52D6]">
                      Guardian Copilot
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#6F7F98]">
                      Safety Officer
                    </span>
                    <User className="w-3.5 h-3.5 text-[#6F7F98]" />
                  </>
                )}
              </div>

              <div
                className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-[90%] ${
                  m.sender === 'user'
                    ? 'bg-[#5D87FF] text-white rounded-tr-md'
                    : 'bg-[#F1F5F9] border border-[#E9EDF2] text-[#18243A] rounded-tl-md'
                }`}
              >
                {m.text}

                {m.responseObj && (
                  <div className="mt-3 flex items-center gap-2 text-[9px] uppercase tracking-[0.14em]">
                    <span className={`inline-flex items-center rounded-full border px-1.5 py-0.5 ${m.responseObj.is_grounded ? 'border-[rgba(21,128,61,0.3)] bg-[rgba(21,128,61,0.1)] text-[#15803d]' : 'border-[rgba(146,64,14,0.3)] bg-[rgba(146,64,14,0.1)] text-[#92400e]'}`}>
                      {m.responseObj.is_grounded ? 'Grounded' : 'Insufficient evidence'}
                    </span>
                    <span className="text-[#6F7F98] normal-case tracking-normal">Confidence {(m.responseObj.confidence * 100).toFixed(0)}%</span>
                  </div>
                )}

                {/* Comparative answer: Answer -> Evidence -> Comparison -> Why it matters -> Recommended action */}
                {m.responseObj?.comparison && m.responseObj.comparison.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#E9EDF2] space-y-2">
                    <div className="text-[10px] text-[#6F7F98] uppercase tracking-wider">
                      {m.responseObj.period_a_label} vs {m.responseObj.period_b_label}
                    </div>
                    {m.responseObj.comparison.map((metric, mIdx) => (
                      <div key={mIdx} className="flex items-center justify-between gap-2 rounded-xl bg-white border border-[#E9EDF2] px-2.5 py-1.5">
                        <span className="text-[#18243A] font-medium">{metric.label}</span>
                        <span className="flex items-center gap-1" style={{ color: directionColor(metric.direction) }}>
                          {metric.direction === 'DECREASED' ? <TrendingDown className="w-3 h-3" /> : metric.direction === 'INCREASED' ? <TrendingUp className="w-3 h-3" /> : null}
                          {metric.period_a_value} → {metric.period_b_value}
                          {typeof metric.percent_change === 'number' && (
                            <span className="text-[9px]">({metric.percent_change > 0 ? '+' : ''}{metric.percent_change.toFixed(1)}%)</span>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {m.responseObj?.what_changed && (
                  m.responseObj.what_changed.improved.length > 0 ||
                  m.responseObj.what_changed.worsened.length > 0 ||
                  m.responseObj.what_changed.new_items.length > 0 ||
                  m.responseObj.what_changed.persistent.length > 0
                ) && (
                  <div className="mt-3 pt-3 border-t border-[#E9EDF2] space-y-2 text-[10px]">
                    {m.responseObj.what_changed.worsened.length > 0 && (
                      <div>
                        <span className="font-semibold text-[#b91c1c]">Worsened: </span>
                        <span className="text-[#18243A]">{m.responseObj.what_changed.worsened.join('; ')}</span>
                      </div>
                    )}
                    {m.responseObj.what_changed.improved.length > 0 && (
                      <div>
                        <span className="font-semibold text-[#15803d]">Improved: </span>
                        <span className="text-[#18243A]">{m.responseObj.what_changed.improved.join('; ')}</span>
                      </div>
                    )}
                    {m.responseObj.what_changed.new_items.length > 0 && (
                      <div>
                        <span className="font-semibold text-[#92400e]">New: </span>
                        <span className="text-[#18243A]">{m.responseObj.what_changed.new_items.join('; ')}</span>
                      </div>
                    )}
                    {m.responseObj.what_changed.persistent.length > 0 && (
                      <div>
                        <span className="font-semibold text-[#6F7F98]">Persistent: </span>
                        <span className="text-[#18243A]">{m.responseObj.what_changed.persistent.join('; ')}</span>
                      </div>
                    )}
                  </div>
                )}

                {m.responseObj?.why_it_matters && (
                  <div className="mt-3 pt-3 border-t border-[#E9EDF2]">
                    <div className="text-[10px] text-[#6F7F98] uppercase tracking-wider mb-1">Why it matters</div>
                    <div className="text-[#18243A]">{m.responseObj.why_it_matters}</div>
                  </div>
                )}

                {m.responseObj?.recommended_action && (
                  <div className="mt-3 pt-3 border-t border-[#E9EDF2]">
                    <div className="text-[10px] text-[#6F7F98] uppercase tracking-wider mb-1">Recommended action</div>
                    <div className="text-[#18243A]">{m.responseObj.recommended_action}</div>
                    <button
                      onClick={() => {
                        onClose();
                        navigate('/incidents');
                      }}
                      className="mt-2 text-[#2F52D6] hover:text-[#18243A] inline-flex items-center gap-1 transition-colors"
                    >
                      Open incident board <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                )}

                {/* Citations block */}
                {m.responseObj?.grounded_citations && m.responseObj.grounded_citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#E9EDF2] space-y-2">
                    <div className="text-[10px] text-[#6F7F98] uppercase tracking-wider flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-[#15803d]" />
                      Verified Evidence Citations
                    </div>
                    {m.responseObj.grounded_citations.map((c, cIdx) => (
                      <div
                        key={cIdx}
                        className="p-2 rounded-xl bg-white border border-[#E9EDF2] text-[11px] space-y-0.5"
                      >
                        <div className="font-semibold text-[#18243A] flex items-center justify-between gap-2">
                          <span>{c.title}</span>
                          <span className="text-[9px] font-semibold text-[#15803d]">
                            {(c.confidence * 100).toFixed(0)}% MATCH
                          </span>
                        </div>
                        <div className="text-[#6F7F98] text-[10px]">{c.snippet}</div>
                      </div>
                    ))}
                  </div>
                )}

                {!m.responseObj?.grounded_citations?.length && m.responseObj && (
                  <div className="mt-3 pt-3 border-t border-[#E9EDF2] text-[10px] text-[#92400e]">
                    This answer is limited to verified records. If the query cannot be matched to an incident, risk assessment, or SOP rule, the assistant will not invent a result.
                  </div>
                )}

                {/* Suggested followups */}
                {m.responseObj?.suggested_followups?.length ? (
                  <div className="mt-3 pt-2 border-t border-[#E9EDF2] space-y-1">
                    <div className="text-[10px] text-[#6F7F98]">Suggested Inquiries</div>
                    {m.responseObj.suggested_followups.map((f, fIdx) => (
                      <button
                        key={fIdx}
                        onClick={() => handleSend(f)}
                        className="w-full text-left text-[11px] text-[#2F52D6] hover:text-[#18243A] p-1.5 rounded-lg hover:bg-white transition-colors flex items-center justify-between group"
                      >
                        <span>{f}</span>
                        <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-[#2F52D6] py-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Consulting pgvector database knowledge base...</span>
            </div>
          )}
        </div>

        {/* Input Box */}
        <div className="p-4 border-t border-[#E9EDF2]">
          <div className="relative flex items-center bg-white border border-[#E9EDF2] rounded-2xl pl-4 pr-1.5 py-1.5">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question about warehouse safety rules, incidents..."
              className="w-full bg-transparent text-xs text-[#18243A] placeholder-[#9DAFC5] focus:outline-none py-1.5"
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputQuery.trim() || loading}
              aria-label="Send message"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#5D87FF] text-white disabled:opacity-30 transition-all"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </>
  );
};
