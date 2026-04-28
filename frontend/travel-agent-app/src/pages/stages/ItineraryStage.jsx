import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { Send, Loader2, Calendar, MapPin, ExternalLink, CheckCircle2, Lock } from 'lucide-react';

import { fetchWithAuth } from '../../authService'; 
import { API_BASE_URL } from '../../config';
import PageTransition from '../../components/PageTransition';

// --- NEW TRANSIT CARD COMPONENT ---
const TransitStrategyCard = ({ strategy }) => {
  if (!strategy || Object.keys(strategy).length === 0) return null;

  return (
    <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 mb-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6 transition-all hover:shadow-md">
      <div className="flex items-start gap-4">
        <div className="bg-blue-600 text-white p-3 rounded-xl shadow-md mt-1 shrink-0">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </div>
        <div>
          <h4 className="text-[11px] font-black tracking-widest text-blue-600 uppercase mb-1.5">
            Local Transit Strategy
          </h4>
          <h3 className="text-xl font-black text-gray-900 mb-1.5">
            {strategy.pass_name} <span className="text-gray-500 font-medium">— {strategy.price}</span>
          </h3>
          <p className="text-gray-600 text-sm leading-relaxed max-w-xl">
            {strategy.description}
          </p>
        </div>
      </div>

      {strategy.purchase_url && (
        <a 
          href={strategy.purchase_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="shrink-0 w-full md:w-auto text-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-sm hover:shadow hover:-translate-y-0.5"
        >
          Get Official Pass
        </a>
      )}
    </div>
  );
};

export default function ItineraryStage() {
  const { sessionData, refreshContext } = useOutletContext();
  const params = useParams();
  
  const session = sessionData?.data || sessionData;
  const sessionId = session?.id || params.sessionId || params.id;

  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [agentStatus, setAgentStatus] = useState(null);
  
  const [dailyThemes, setDailyThemes] = useState({});
  const [dailyPlans, setDailyPlans] = useState({});
  const [dailyLinks, setDailyLinks] = useState({});
  const [areThemesConfirmed, setAreThemesConfirmed] = useState(false);
  const [transitStrategy, setTransitStrategy] = useState(null); // <--- NEW STATE

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentStatus]);

  useEffect(() => {
    if (sessionId) {
      fetchInitialState();
    }
  }, [sessionId]);

  useEffect(() => {
    if (!isStreaming && areThemesConfirmed && Object.keys(dailyPlans).length > 0) {
      saveItineraryToSession();
    }
  }, [isStreaming, areThemesConfirmed, dailyPlans, dailyThemes, dailyLinks]);

  const fetchInitialState = async () => {
    setIsLoading(true);
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/chat/itinerary/messages/${sessionId}`, {}, 'GET');
      
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setDailyThemes(data.daily_themes || {});
        setDailyPlans(data.daily_plans || {});
        setDailyLinks(data.daily_links || {});
        setAreThemesConfirmed(data.are_themes_confirmed || false);
        // <--- SET TRANSIT STRATEGY FROM DB --->
        if (data.transit_strategy && Object.keys(data.transit_strategy).length > 0) {
            setTransitStrategy(data.transit_strategy);
        }
      } else {
        console.error("Failed to fetch initial state:", response.status);
      }
    } catch (error) {
      console.error("Error fetching state:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveItineraryToSession = async () => {
    const sortedDays = Object.keys(dailyThemes).sort((a, b) => parseInt(a) - parseInt(b));
    if (sortedDays.length === 0) return;

    const finalItinerary = sortedDays.map(dayStr => {
      const dayNum = parseInt(dayStr);
      return {
        day: dayNum,
        title: dailyThemes[dayStr] || `Day ${dayNum}`,
        description: dailyPlans[dayStr] || "",
        links: dailyLinks[dayStr] || []
      };
    });

    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/session/${sessionId}/details`, {
        itinerary_data: finalItinerary,
        transit_strategy: transitStrategy
      }, 'PATCH');
      
      if (response.ok) {
        console.log("Itinerary data structured and auto-saved!");
        if (refreshContext) refreshContext();
      }
    } catch (err) {
      console.error("Failed to auto-save structured itinerary:", err);
    }
  };

  const handleFinalize = async () => {
    setIsFinalizing(true);
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/chat/itinerary/confirm_themes/${sessionId}`, {}, 'POST');
      
      if (response.ok) {
        setAreThemesConfirmed(true);
        setMessages(prev => [...prev, { 
          sender: 'ai', 
          text: 'Awesome! The skeleton is locked in. Let me know which day you want to detail first, or I can start from Day 1.' 
        }]);
      }
    } catch (error) {
      console.error("Error finalizing:", error);
    } finally {
      setIsFinalizing(false);
    }
  };

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isStreaming || !sessionId) return;

    const userMsg = { sender: 'user', text: inputMessage };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage("");
    setIsStreaming(true);
    setAgentStatus("Reading message...");

    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/chat/itinerary/${sessionId}`, 
        { message: userMsg.text },
        'POST'
      );

      if (!response.ok) throw new Error("Failed to send message");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let done = false;
      let buffer = "";
      
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop();
          
          for (let line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.substring(6).trim();
              if (dataStr) {
                try {
                  const data = JSON.parse(dataStr);
                  handleStreamEvent(data);
                } catch (err) {
                  console.error("Error parsing stream JSON chunk:", err);
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { sender: 'ai', text: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsStreaming(false);
      setAgentStatus(null);
    }
  };

  const handleStreamEvent = (data) => {
    if (data.status === "processing") {
      setAgentStatus("Updating itinerary...");
      if (data.daily_themes) setDailyThemes(data.daily_themes);
      if (data.daily_plans) setDailyPlans(data.daily_plans);
      if (data.daily_links) setDailyLinks(data.daily_links);
      // <--- SET TRANSIT STRATEGY FROM STREAM --->
      if (data.transit_strategy && Object.keys(data.transit_strategy).length > 0) {
        setTransitStrategy(data.transit_strategy);
      }
    } else if (data.status === "complete") {
      let finalString = "";
      try {
        const parsedMsg = typeof data.ai_message === 'string' ? JSON.parse(data.ai_message) : data.ai_message;
        if (Array.isArray(parsedMsg)) {
          finalString = parsedMsg.map(block => block.text || block.content || "").join("");
        } else if (parsedMsg && typeof parsedMsg === 'object') {
          finalString = parsedMsg.text || parsedMsg.content || "";
        }
      } catch (e) {
        finalString = data.ai_message;
      }
      if (!finalString) {
        finalString = typeof data.ai_message === 'string' ? data.ai_message : JSON.stringify(data.ai_message);
      }
      setMessages(prev => [...prev, { sender: 'ai', text: finalString }]);
    }
  };

  const sortedDays = Object.keys(dailyThemes).sort((a, b) => parseInt(a) - parseInt(b));

  if (isLoading) {
    return (
      <div className="flex w-full h-full items-center justify-center bg-white">
        <div className="flex flex-col items-center gap-4 text-blue-600">
          <Loader2 className="animate-spin" size={40} />
          <p className="font-medium text-gray-500 animate-pulse">Loading your itinerary...</p>
        </div>
      </div>
    );
  }

  return (
    <PageTransition className="flex w-full h-full bg-white overflow-hidden font-sans relative">

      <div className="flex-1 lg:max-w-md flex flex-col bg-gray-50/50 border-r border-gray-200 z-10 shrink-0">

        <div className="px-6 py-4 border-b border-gray-200 bg-white shadow-sm shrink-0">
          <h2 className="text-lg font-black text-gray-800 flex items-center gap-2">
            <MapPin className="text-blue-600" size={20} />
            Itinerary Architect
          </h2>
          <p className="text-xs text-gray-500 font-medium mt-1">
            {areThemesConfirmed ? "Phase 2: Deep Detailing & Booking" : "Phase 1: Sketching the Skeleton"}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.length === 0 && (
            <div className="text-center mt-10 opacity-70">
              <Calendar size={40} className="mx-auto mb-3 text-gray-400" />
              <p className="text-sm text-gray-500 font-medium">Say hi to generate your initial trip skeleton!</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div 
                className={`max-w-[90%] px-5 py-4 shadow-sm text-[14px] leading-relaxed ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm whitespace-pre-wrap' 
                    : 'bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-tl-sm'
                }`}
              >
                {msg.sender === 'ai' ? (
                  <ReactMarkdown 
                    className="[&>p]:mb-3 last:[&>p]:mb-0 [&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-3 [&>ol]:list-decimal [&>ol]:ml-6 [&>strong]:font-bold"
                  >
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  msg.text
                )}
              </div>
            </div>
          ))}

          {agentStatus && (
            <div className="flex justify-start">
              <div className="bg-white border border-blue-100 text-blue-700 text-sm font-medium rounded-2xl rounded-tl-sm px-5 py-3 shadow-sm flex items-center gap-3">
                <Loader2 className="animate-spin text-blue-500" size={16} />
                <span className="animate-pulse">{agentStatus}</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-white border-t border-gray-200 shrink-0">
          <form onSubmit={handleSendMessage} className="flex gap-2 relative w-full">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={areThemesConfirmed ? "Let's detail Day 2..." : "Change Day 3 to a beach day..."}
              className="w-full rounded-2xl border border-gray-300 pl-4 pr-14 py-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:bg-gray-50 disabled:text-gray-400 text-sm"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isStreaming}
              className="absolute right-1.5 top-1.5 bottom-1.5 w-10 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-xl flex items-center justify-center transition-all"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>

      <div className="flex-[2] overflow-y-auto bg-gray-50 p-6 md:p-10 relative">
        <div className="max-w-4xl mx-auto w-full">

          <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-8 bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
            <div>
              <h1 className="text-xl font-black text-gray-800">Trip Blueprint</h1>
              <p className="text-gray-500 text-sm mt-1 font-medium">Watch your plan evolve in real-time.</p>
            </div>

            {!areThemesConfirmed && sortedDays.length > 0 ? (
              <button 
                onClick={handleFinalize} 
                disabled={isFinalizing || isStreaming}
                className="flex items-center justify-center gap-2 px-5 py-2.5 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow hover:-translate-y-0.5"
              >
                {isFinalizing ? <Loader2 className="animate-spin" size={18} /> : <Lock size={18} />}
                Lock Skeleton & Detail
              </button>
            ) : areThemesConfirmed ? (
              <span className="flex items-center justify-center gap-2 px-4 py-2 bg-green-50 text-green-700 border border-green-200 rounded-xl font-bold text-sm">
                <CheckCircle2 size={18} />
                Skeleton Locked
              </span>
            ) : null}
          </div>

          {/* --- RENDER THE TRANSIT CARD HERE --- */}
          <TransitStrategyCard strategy={transitStrategy} />

          {sortedDays.length === 0 ? (
             <div className="flex flex-col items-center justify-center mt-10 p-10 border-2 border-dashed border-gray-200 rounded-3xl bg-gray-50">
               <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mb-4">
                 <Calendar className="text-blue-500" size={28} />
               </div>
               <h3 className="text-lg font-bold text-gray-700">No itinerary generated yet</h3>
               <p className="text-gray-500 text-sm mt-2 max-w-md text-center">
                 Ask the architect to create an initial skeleton for your trip based on your destination and dates.
               </p>
             </div>
          ) : (
            <div className="space-y-6 pb-10">
              {sortedDays.map(day => (
                <div key={day} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden transition-all hover:shadow-md">

                  <div className="bg-gray-50/50 border-b border-gray-100 px-6 py-4 flex items-center justify-between">
                    <h3 className="text-lg font-black text-gray-800 flex items-center gap-3">
                      <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-100 text-blue-700 text-sm font-black shadow-sm">
                        {day}
                      </span>
                      {dailyThemes[day]}
                    </h3>
                  </div>

                  {areThemesConfirmed && dailyPlans[day] && (
                    <div className="p-6">
                      <div className="prose prose-sm max-w-none text-gray-700 [&>p]:mb-3 last:[&>p]:mb-0 [&>strong]:text-gray-900">
                        <ReactMarkdown>{dailyPlans[day]}</ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {areThemesConfirmed && dailyLinks[day] && dailyLinks[day].length > 0 && (
                    <div className="bg-blue-50/50 px-6 py-4 border-t border-blue-100/50">
                      <h4 className="text-[10px] font-black text-blue-800 uppercase tracking-widest mb-3">Suggested Links</h4>
                      <div className="flex flex-wrap gap-2">
                        {dailyLinks[day].map((link, idx) => (
                          <a 
                            key={idx} 
                            href={link.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-blue-200 text-blue-700 hover:bg-blue-600 hover:text-white rounded-lg text-xs font-bold transition-colors shadow-sm"
                          >
                            <ExternalLink size={14} />
                            {link.name}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  );
}