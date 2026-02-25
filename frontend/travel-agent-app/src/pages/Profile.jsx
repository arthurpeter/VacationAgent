import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Profile() {
  const { user, logout } = useAuth(); // Assuming your auth context provides the user object
  const [activeTab, setActiveTab] = useState('preferences');

  // Dummy state for the multi-airport UI
  const [airports, setAirports] = useState(['OTP', 'CLJ']); 
  const [newAirport, setNewAirport] = useState('');

  const handleAddAirport = (e) => {
    e.preventDefault();
    if (newAirport.trim() && !airports.includes(newAirport.toUpperCase())) {
      setAirports([...airports, newAirport.toUpperCase()]);
      setNewAirport('');
    }
  };

  const removeAirport = (codeToRemove) => {
    setAirports(airports.filter(code => code !== codeToRemove));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900">Your Profile</h1>
          <p className="text-gray-500 mt-2">Manage your account and teach the AI how you like to travel.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row">
          
          {/* Sidebar Navigation */}
          <div className="w-full md:w-64 bg-gray-50 border-b md:border-b-0 md:border-r border-gray-100 p-6 space-y-2">
            <button 
              onClick={() => setActiveTab('preferences')}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'preferences' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              Travel Preferences
            </button>
            <button 
              onClick={() => setActiveTab('account')}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'account' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              Account Details
            </button>
            <button 
              onClick={() => setActiveTab('vault')}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'vault' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              Traveler Vault
            </button>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-8">
            
            {/* --- TRAVEL PREFERENCES TAB --- */}
            {activeTab === 'preferences' && (
              <div className="space-y-8 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">AI Travel Preferences</h2>
                
                {/* Default Currency */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Default Currency</label>
                  <select className="w-full md:w-1/2 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none">
                    <option value="EUR">€ EUR - Euro</option>
                    <option value="USD">$ USD - US Dollar</option>
                    <option value="GBP">£ GBP - British Pound</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-2">The AI will use this to calculate your trip budgets.</p>
                </div>

                {/* Multiple Home Airports */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Preferred Departure Airports</label>
                  
                  {/* Airport Tags */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {airports.map(code => (
                      <span key={code} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
                        ✈️ {code}
                        <button onClick={() => removeAirport(code)} className="ml-2 text-blue-400 hover:text-blue-600 focus:outline-none">
                          &times;
                        </button>
                      </span>
                    ))}
                    {airports.length === 0 && <span className="text-sm text-gray-400 italic">No airports added yet.</span>}
                  </div>

                  {/* Add Airport Input */}
                  <form onSubmit={handleAddAirport} className="flex gap-2 w-full md:w-1/2">
                    <input 
                      type="text" 
                      value={newAirport}
                      onChange={(e) => setNewAirport(e.target.value)}
                      placeholder="e.g., JFK or LHR"
                      maxLength="3"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none uppercase"
                    />
                    <button type="submit" className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 font-medium transition">
                      Add
                    </button>
                  </form>
                  <p className="text-xs text-gray-500 mt-2">Add all the airport codes in your city you are willing to fly from.</p>
                </div>

                <div className="pt-4">
                  <button className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">Save Preferences</button>
                </div>
              </div>
            )}

            {/* --- ACCOUNT DETAILS TAB --- */}
            {activeTab === 'account' && (
              <div className="space-y-6 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">Account Details</h2>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  <input type="email" disabled value="user@example.com" className="w-full md:w-2/3 px-4 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-500 cursor-not-allowed" />
                </div>
                <div>
                  <button className="text-blue-600 font-medium hover:underline">Change Password</button>
                </div>
                <div className="pt-8 border-t mt-8">
                  <button className="text-red-500 font-medium hover:text-red-700 transition">Delete Account</button>
                </div>
              </div>
            )}

            {/* --- TRAVELER VAULT TAB --- */}
            {activeTab === 'vault' && (
              <div className="space-y-6 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">Traveler Vault</h2>
                <p className="text-gray-600 text-sm mb-4">
                  Securely save details for the people you travel with frequently to make the final booking process seamless.
                </p>
                
                {/* Empty State for Vault */}
                <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center bg-gray-50">
                  <div className="text-4xl mb-3">🛂</div>
                  <h3 className="text-lg font-semibold text-gray-900">No travelers saved</h3>
                  <p className="text-gray-500 text-sm mt-1 mb-4">Add passports and frequent flyer numbers here.</p>
                  <button className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 transition shadow-sm">
                    + Add New Traveler
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}