import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { API_BASE_URL } from '../../config';

export default function DiscoveryStage() {
  const { sessionData, refreshContext } = useOutletContext();
  const [input, setInput] = useState("");
  // In a real app, messages would come from sessionData.messages
  const [messages, setMessages] = useState(sessionData?.messages || []);

  const handleSend = async () => {
    // 1. Optimistic UI update
    const newMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, newMsg]);
    setInput("");

    // 2. Call your agent API
    // const res = await fetchWithAuth(...)
    
    // 3. Refresh context to update the Sidebar with new extracted info
    // await refreshContext();
  };

  // Extracted "Memory" from the database (VacationSession.data)
  const memory = sessionData?.data || {};

  return (
    <div className="flex w-full h-full">
      {/* Left: Chat Interface */}
      <div className="w-2/3 flex flex-col border-r border-gray-200 bg-white">
        <div className="flex-grow overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-4 rounded-2xl ${
                msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-gray-100 text-gray-800 rounded-tl-none'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-gray-100">
          <div className="flex gap-2">
            <input
              className="flex-grow border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Tell me about your dream trip..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend} className="bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 transition">
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Right: Live Context Panel (The "Brain") */}
      <div className="w-1/3 bg-gray-50 p-6 overflow-y-auto">
        <h3 className="text-gray-400 font-bold text-xs uppercase tracking-wider mb-4">Trip Parameters</h3>
        
        <div className="space-y-4">
          <ParameterCard label="Destination" value={memory.destination} icon="📍" />
          <ParameterCard label="Dates" value={memory.departure_date ? `${memory.departure_date} - ${memory.return_date}` : null} icon="jq" />
          <ParameterCard label="Budget" value={memory.budget ? `$${memory.budget}` : null} icon="💰" />
          <ParameterCard label="Travelers" value={memory.adults ? `${memory.adults} Adults, ${memory.children || 0} Kids` : null} icon="yw" />
          
          <div className="mt-8">
            <h4 className="text-sm font-bold text-gray-700 mb-2">Vibe & Activities</h4>
            <div className="flex flex-wrap gap-2">
               {/* This would come from memory.description analysis */}
               <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs font-semibold">Relaxing</span>
               <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold">Beach</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ParameterCard({ label, value, icon }) {
  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-xl">
        {icon}
      </div>
      <div>
        <div className="text-xs text-gray-500 font-medium">{label}</div>
        <div className={`text-sm font-bold ${value ? 'text-gray-900' : 'text-gray-300 italic'}`}>
          {value || "Pending..."}
        </div>
      </div>
    </div>
  );
}