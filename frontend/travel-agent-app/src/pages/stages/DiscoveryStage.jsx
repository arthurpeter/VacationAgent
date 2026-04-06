import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../../config';
import { fetchWithAuth } from '../../authService';
import ReactMarkdown from 'react-markdown';
import PageTransition from '../../components/PageTransition';

const DiscoveryStage = () => {
  const { sessionData, refreshContext } = useOutletContext();
  const navigate = useNavigate();
  
  const session = sessionData?.data || sessionData;
  const sessionId = session?.id || sessionData?.id;
  
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [agentStatus, setAgentStatus] = useState(null);
  
  // Mobile Drawer State
  const [showMobilePlan, setShowMobilePlan] = useState(false);
  
  const [tripData, setTripData] = useState({
    departure: null, destination: null, from_date: null, to_date: null,
    adults: null, children: null, budget: null, currency: null, room_qty: null
  });

  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (session) {
      setTripData({
        departure: session.departure || null,
        destination: session.destination || null,
        from_date: session.from_date ? session.from_date.split('T')[0] : null,
        to_date: session.to_date ? session.to_date.split('T')[0] : null,
        adults: session.adults || null,
        children: session.children || null,
        budget: session.budget || null,
        currency: session.currency || null,
        room_qty: session.room_qty || null
      });
    }
  }, [sessionData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentStatus]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!sessionId) return;
      try {
        const response = await fetchWithAuth(`${API_BASE_URL}/chat/discovery/messages/${sessionId}`, null, 'GET');
        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
          }
        }
      } catch (err) {
        console.error("Failed to load chat history:", err);
      }
    };
    fetchHistory();
  }, [sessionId]);

  const handleSendMessage = async (e, overrideText = null) => {
    if (e) e.preventDefault();
    
    const textToSend = overrideText || inputValue;
    if (!textToSend.trim() || isProcessing || !sessionId) return;

    setInputValue("");
    setMessages(prev => [...prev, { sender: 'user', text: textToSend }]);
    setIsProcessing(true);
    setAgentStatus("Reading message...");

    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/chat/discovery/${sessionId}`, 
        { message: textToSend }, 
        'POST'
      );

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

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
      setMessages(prev => [...prev, { sender: 'ai', text: "Sorry, I encountered an error connecting to the server." }]);
    } finally {
      setIsProcessing(false);
      setAgentStatus(null);
    }
  };

  const handleStreamEvent = (data) => {
    if (data.status === "processing") {
      if (data.current_node === "information_collector") setAgentStatus("Extracting trip details...");
      else if (data.current_node === "db_validator") setAgentStatus("Validating requirements...");
      else if (data.current_node === "responder") setAgentStatus("Formulating response...");
      else if (data.current_node === "tools") setAgentStatus("Searching the web for info...");

      if (data.extracted_data && Object.keys(data.extracted_data).length > 0) {
        setTripData(prev => ({ ...prev, ...data.extracted_data }));
        if (refreshContext) refreshContext();
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

  // Calculate Progress
  const requiredFields = ['departure', 'destination', 'from_date', 'to_date', 'adults', 'currency', 'room_qty'];
  const filledCount = requiredFields.filter(field => tripData[field]).length;
  const progressPercent = Math.round((filledCount / requiredFields.length) * 100);

  const SUGGESTED_PROMPTS = [
    "I need inspiration for a weekend getaway. We haven't picked a destination yet.",
    "Help me plan a family vacation for this summer. We need somewhere kid-friendly.",
    "I want to travel somewhere new on a tight budget. What are some good options?"
  ];

  // A reusable component for the Plan Cards so we can show it in the Desktop Sidebar AND the Mobile Drawer
  const BlueprintContent = () => (
    <div className="space-y-4">
      {/* Progress Bar Section */}
      <div className="mb-6">
        <div className="flex justify-between items-end mb-2">
            <h3 className="text-[11px] font-black text-gray-400 uppercase tracking-widest">Plan Progress</h3>
            <span className="text-xs font-bold text-gray-500">{progressPercent}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mb-3 overflow-hidden">
          <div 
            className={`h-2 rounded-full transition-all duration-700 ease-out ${progressPercent === 100 ? 'bg-green-500' : 'bg-blue-500'}`} 
            style={{ width: `${progressPercent}%` }}
          ></div>
        </div>
        <div className={`transition-all duration-500 overflow-hidden ${progressPercent === 100 ? 'max-h-20 opacity-100' : 'max-h-0 opacity-0'}`}>
          <button 
            onClick={() => {
              setShowMobilePlan(false);
              navigate(`/plan/${sessionId}/options`);
            }}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-xl transition-all flex justify-center items-center gap-2 transform hover:-translate-y-0.5 mt-1"
          >
            See Flight & Hotel Options <span>➔</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-4 md:p-5 shadow-sm border border-gray-200">
        <h4 className="text-blue-600 text-[10px] font-black uppercase mb-3 tracking-widest">Locations</h4>
        <div className="space-y-4">
          <div>
            <p className="text-[10px] uppercase text-gray-400 font-bold mb-1">Departure</p>
            <p className="font-bold text-gray-800 text-sm">{tripData.departure || <span className="text-gray-300 italic">Thinking...</span>}</p>
          </div>
          <div className="w-full h-px bg-gray-100 relative">
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white px-2 text-gray-300 text-xs">✈️</span>
          </div>
          <div>
            <p className="text-[10px] uppercase text-gray-400 font-bold mb-1">Destination</p>
            <p className="font-bold text-gray-800 text-sm">{tripData.destination || <span className="text-gray-300 italic">Thinking...</span>}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-4 md:p-5 shadow-sm border border-gray-200">
        <h4 className="text-blue-600 text-[10px] font-black uppercase mb-3 tracking-widest">Timeline</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] uppercase text-gray-400 font-bold mb-1">Check-in</p>
            <p className="font-bold text-gray-800 text-sm">{tripData.from_date || <span className="text-gray-300 italic">TBD</span>}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase text-gray-400 font-bold mb-1">Check-out</p>
            <p className="font-bold text-gray-800 text-sm">{tripData.to_date || <span className="text-gray-300 italic">TBD</span>}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-4 md:p-5 shadow-sm border border-gray-200">
        <h4 className="text-blue-600 text-[10px] font-black uppercase mb-3 tracking-widest">Travel Party</h4>
        <div className="flex justify-between items-center mb-3">
          <span className="text-gray-500 text-sm font-medium">Adults</span>
          <span className="font-bold text-gray-800">{tripData.adults ?? '-'}</span>
        </div>
        <div className="flex justify-between items-center mb-3">
          <span className="text-gray-500 text-sm font-medium">Children</span>
          <span className="font-bold text-gray-800">{tripData.children ?? '-'}</span>
        </div>
        <div className="flex justify-between items-center pt-3 border-t border-gray-50">
          <span className="text-gray-500 text-sm font-medium">Hotel Rooms</span>
          <span className="font-bold text-gray-800">{tripData.room_qty ?? '-'}</span>
        </div>
      </div>

      <div className={`rounded-2xl p-4 md:p-5 shadow-sm border transition-colors duration-500 ${tripData.budget ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`${tripData.budget ? 'text-green-700' : 'text-gray-500'} text-[10px] font-black uppercase mb-3 tracking-widest`}>Target Budget</h4>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-black ${tripData.budget ? 'text-green-700' : 'text-gray-400'}`}>
              {tripData.budget ? tripData.budget.toLocaleString() : '--'}
            </span>
            <span className={`text-sm font-bold ${tripData.budget ? 'text-green-600' : 'text-gray-400'}`}>
              {tripData.currency || ''}
            </span>
          </div>
      </div>
    </div>
  );

  return (
    <PageTransition className="flex w-full h-full bg-white overflow-hidden font-sans relative">
      
      {/* LEFT PANEL: Chat Interface (Takes 100% on mobile, flex-1 on desktop) */}
      <div className="flex-1 flex flex-col relative bg-gray-50/50 min-h-0 w-full">
        
        {/* Header */}
        <div className="px-6 md:px-8 py-4 border-b border-gray-200 bg-white z-10 flex justify-between items-center shadow-sm">
          <div>
            <h2 className="text-lg md:text-xl font-black text-gray-800">Trip Discovery</h2>
            <p className="text-xs md:text-sm text-gray-500 font-medium hidden sm:block">Chat with your AI agent to build your perfect itinerary.</p>
          </div>

          {/* Mobile "View Plan" Toggle Button */}
          <button 
            onClick={() => setShowMobilePlan(true)}
            className="md:hidden flex items-center gap-2 bg-blue-50 hover:bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-bold text-sm shadow-sm border border-blue-100 transition-colors"
          >
            <span>📋 Blueprint</span>
            <span className={`${progressPercent === 100 ? 'bg-green-500' : 'bg-blue-600'} text-white px-2 py-0.5 rounded-full text-xs`}>
              {progressPercent}%
            </span>
          </button>
        </div>

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          
          {/* Cold Start View */}
          {messages.length === 0 && (
            <div className="text-center mt-6 md:mt-16 flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-700">
              <div className="w-16 h-16 md:w-20 md:h-20 bg-blue-50 rounded-full flex items-center justify-center mb-4 border border-blue-100 shadow-sm">
                <span className="text-3xl md:text-4xl">✈️</span>
              </div>
              <h3 className="text-xl font-black text-gray-800 mb-2">Where are we going?</h3>
              <p className="text-sm text-gray-500 max-w-sm px-4 mb-8">Tell me about your dream trip, your available budget, or who you're traveling with.</p>
              
              {/* Quick Start Chips */}
              <div className="flex flex-col gap-3 w-full max-w-md px-4">
                {SUGGESTED_PROMPTS.map((prompt, i) => (
                  <button 
                    key={i}
                    onClick={() => handleSendMessage(null, prompt)}
                    className="text-left text-sm bg-white border border-gray-200 hover:border-blue-400 hover:bg-blue-50 text-gray-700 hover:text-blue-800 py-3 px-5 rounded-2xl shadow-sm transition-all transform hover:-translate-y-0.5"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Messages */}
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div 
                className={`max-w-[90%] lg:max-w-[70%] px-5 py-4 shadow-sm text-[15px] leading-relaxed ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm whitespace-pre-wrap' 
                    : 'bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-tl-sm'
                }`}
              >
                {/* AI Markdown Render vs User Plain Text Render */}
                {msg.sender === 'ai' ? (
                  <ReactMarkdown 
                    className="[&>p]:mb-3 last:[&>p]:mb-0 [&>ul]:list-disc [&>ul]:ml-6 [&>ul]:mb-3 [&>ol]:list-decimal [&>ol]:ml-6 [&>strong]:font-bold [&>h1]:font-black [&>h1]:text-lg [&>h1]:mb-2 [&>h2]:font-bold [&>h2]:mb-2"
                  >
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  msg.text
                )}
              </div>
            </div>
          ))}

          {/* Loading Status */}
          {agentStatus && (
            <div className="flex justify-start">
              <div className="bg-white border border-blue-100 text-blue-700 text-sm font-medium rounded-2xl rounded-tl-sm px-5 py-3 shadow-sm flex items-center gap-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="animate-pulse">{agentStatus}</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-3 md:p-4 bg-white border-t border-gray-200 shrink-0">
          <form onSubmit={handleSendMessage} className="flex gap-2 md:gap-3 relative max-w-4xl mx-auto">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isProcessing || !sessionId}
              placeholder="E.g., I want to go to Paris next week..."
              className="flex-1 rounded-2xl border border-gray-300 pl-4 md:pl-6 pr-24 md:pr-32 py-3 md:py-4 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:bg-gray-50 disabled:text-gray-400 text-sm md:text-base"
            />
            <button 
              type="submit" 
              disabled={isProcessing || (!inputValue.trim() && messages.length > 0) || !sessionId}
              className="absolute right-1.5 md:right-2 top-1.5 md:top-2 bottom-1.5 md:bottom-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-xl px-4 md:px-8 font-bold transition-all flex items-center justify-center text-sm md:text-base"
            >
              Send
            </button>
          </form>
        </div>
      </div>

      {/* DESKTOP RIGHT PANEL (Hidden on Mobile) */}
      <div className="hidden md:flex flex-col w-80 lg:w-96 bg-gray-50 border-l border-gray-200 overflow-y-auto p-5 md:p-6 shadow-inner shrink-0">
        <BlueprintContent />
      </div>

      {/* MOBILE DRAWER OVERLAY (Hidden on Desktop) */}
      <div 
        className={`md:hidden fixed inset-0 z-50 bg-gray-900/60 backdrop-blur-sm transition-opacity duration-300 ${
          showMobilePlan ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setShowMobilePlan(false)} // Close if they click the dark background
      >
        <div 
          className={`absolute bottom-0 left-0 right-0 bg-gray-50 rounded-t-3xl h-[85vh] flex flex-col transition-transform duration-300 shadow-2xl ${
            showMobilePlan ? 'translate-y-0' : 'translate-y-full'
          }`}
          onClick={(e) => e.stopPropagation()} // Prevent clicks inside the drawer from closing it
        >
          {/* Drawer Header */}
          <div className="flex justify-between items-center p-5 bg-white rounded-t-3xl border-b border-gray-200 shrink-0">
             <div>
               <h3 className="font-black text-gray-800 text-lg">Trip Blueprint</h3>
               <p className="text-xs text-gray-500 font-medium">Your collected trip details</p>
             </div>
             <button 
               onClick={() => setShowMobilePlan(false)} 
               className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold transition-colors"
             >
               ✕
             </button>
          </div>
          
          {/* Drawer Scrollable Content */}
          <div className="overflow-y-auto p-5 pb-10 flex-1">
             <BlueprintContent />
          </div>
        </div>
      </div>
      
    </PageTransition>
  );
};

export default DiscoveryStage;