import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

// --- MOCK DATA FOR THE SKELETON ---
const ALL_CURRENCIES = [
  { code: 'EUR', name: 'Euro' },
  { code: 'USD', name: 'US Dollar' },
  { code: 'GBP', name: 'British Pound' },
  { code: 'RON', name: 'Romanian Leu' },
  { code: 'JPY', name: 'Japanese Yen' },
  { code: 'AUD', name: 'Australian Dollar' },
  { code: 'CAD', name: 'Canadian Dollar' },
  { code: 'CHF', name: 'Swiss Franc' },
];

// Mock API response for airport search (simulating your OptionsStage logic)
const MOCK_AIRPORTS_DB = [
  { code: 'OTP', city: 'Bucharest', name: 'Henri Coandă' },
  { code: 'BBU', city: 'Bucharest', name: 'Băneasa' },
  { code: 'LHR', city: 'London', name: 'Heathrow' },
  { code: 'LGW', city: 'London', name: 'Gatwick' },
  { code: 'JFK', city: 'New York', name: 'John F. Kennedy' },
];

export default function Profile() {
  const [activeTab, setActiveTab] = useState('preferences');

  // --- CURRENCY STATE ---
  const [currencySearch, setCurrencySearch] = useState('EUR');
  const [showCurrencyDropdown, setShowCurrencyDropdown] = useState(false);
  const currencyRef = useRef(null);

  // Filter currencies based on input
  const filteredCurrencies = ALL_CURRENCIES.filter(c => 
    c.code.toLowerCase().startsWith(currencySearch.toLowerCase()) || 
    c.name.toLowerCase().startsWith(currencySearch.toLowerCase())
  );

  // --- AIRPORT STATE ---
  const [airports, setAirports] = useState(['OTP']); 
  const [airportSearch, setAirportSearch] = useState('');
  const [showAirportDropdown, setShowAirportDropdown] = useState(false);
  const airportRef = useRef(null);

  // Filter airports based on city or code
  const filteredAirports = MOCK_AIRPORTS_DB.filter(a => 
    a.city.toLowerCase().includes(airportSearch.toLowerCase()) ||
    a.code.toLowerCase().includes(airportSearch.toLowerCase())
  );

  const handleAddAirport = (airportCode) => {
    if (!airports.includes(airportCode)) {
      setAirports([...airports, airportCode]);
    }
    setAirportSearch('');
    setShowAirportDropdown(false);
  };

  const removeAirport = (codeToRemove) => {
    setAirports(airports.filter(code => code !== codeToRemove));
  };

  // --- TRAVELER VAULT STATE ---
  const [companions, setCompanions] = useState([
    { id: 1, name: 'Jane Doe', dob: '1992-05-14' }
  ]);

  // Click outside listener to close custom dropdowns
  useEffect(() => {
    function handleClickOutside(event) {
      if (currencyRef.current && !currencyRef.current.contains(event.target)) setShowCurrencyDropdown(false);
      if (airportRef.current && !airportRef.current.contains(event.target)) setShowAirportDropdown(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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
          <div className="flex-1 p-8 min-h-[500px]">
            
            {/* --- TRAVEL PREFERENCES TAB --- */}
            {activeTab === 'preferences' && (
              <div className="space-y-8 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">AI Travel Preferences</h2>
                
                {/* Searchable Currency Dropdown */}
                <div className="relative w-full md:w-1/2" ref={currencyRef}>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Default Currency</label>
                  <input
                    type="text"
                    value={currencySearch}
                    onChange={(e) => {
                      setCurrencySearch(e.target.value);
                      setShowCurrencyDropdown(true);
                    }}
                    onFocus={() => setShowCurrencyDropdown(true)}
                    placeholder="Search currency (e.g., EUR)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none uppercase"
                  />
                  {showCurrencyDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                      {filteredCurrencies.length > 0 ? (
                        filteredCurrencies.map(c => (
                          <div 
                            key={c.code} 
                            onClick={() => {
                              setCurrencySearch(c.code);
                              setShowCurrencyDropdown(false);
                            }}
                            className="px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm"
                          >
                            <span className="font-bold text-gray-800 mr-2">{c.code}</span>
                            <span className="text-gray-500">{c.name}</span>
                          </div>
                        ))
                      ) : (
                        <div className="px-4 py-2 text-sm text-gray-500">No currencies found</div>
                      )}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-2">The AI will use this to calculate your trip budgets.</p>
                </div>

                {/* Searchable Multi-Airport Selection */}
                <div className="relative" ref={airportRef}>
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

                  {/* Airport Search Input */}
                  <input 
                    type="text" 
                    value={airportSearch}
                    onChange={(e) => {
                      setAirportSearch(e.target.value);
                      setShowAirportDropdown(true);
                    }}
                    onFocus={() => setShowAirportDropdown(true)}
                    placeholder="Search by city (e.g., Bucharest) or code"
                    className="w-full md:w-2/3 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none"
                  />
                  
                  {/* Airport Dropdown Results */}
                  {showAirportDropdown && airportSearch.trim() !== '' && (
                    <div className="absolute z-10 w-full md:w-2/3 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                      {filteredAirports.length > 0 ? (
                        filteredAirports.map(a => (
                          <div 
                            key={a.code} 
                            onClick={() => handleAddAirport(a.code)}
                            className="px-4 py-3 hover:bg-blue-50 cursor-pointer border-b last:border-0"
                          >
                            <div className="flex justify-between items-center">
                              <div>
                                <p className="text-sm font-bold text-gray-800">{a.city}</p>
                                <p className="text-xs text-gray-500">{a.name} Airport</p>
                              </div>
                              <span className="bg-gray-100 text-gray-700 text-xs font-bold px-2 py-1 rounded">{a.code}</span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="px-4 py-3 text-sm text-gray-500">
                          Press Enter to search external API for "{airportSearch}"...
                        </div>
                      )}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-2">Add all the airport codes in your city you are willing to fly from.</p>
                </div>

                <div className="pt-4 border-t">
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

                {/* Added User DOB */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Your Date of Birth</label>
                  <input type="date" className="w-full md:w-1/2 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none text-gray-700" />
                  <p className="text-xs text-gray-500 mt-1">Required to accurately calculate your traveler type (Adult, Child, etc.) for bookings.</p>
                </div>

                <div>
                  <button className="text-blue-600 font-medium hover:underline mt-2">Change Password</button>
                </div>
                
                <div className="pt-8 border-t mt-8">
                  <button className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition mb-6 block">Save Account Details</button>
                  <button className="text-red-500 font-medium hover:text-red-700 transition text-sm">Delete Account</button>
                </div>
              </div>
            )}

            {/* --- TRAVELER VAULT TAB --- */}
            {activeTab === 'vault' && (
              <div className="space-y-6 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">Traveler Vault</h2>
                <p className="text-gray-600 text-sm mb-4">
                  Save the dates of birth for the people you travel with frequently. This allows the AI to automatically secure the correct pricing for adults, children, and infants.
                </p>
                
                {/* Companions List */}
                <div className="space-y-3 mb-6">
                  {companions.map(comp => (
                    <div key={comp.id} className="flex justify-between items-center p-4 border border-gray-200 rounded-xl bg-gray-50">
                      <div>
                        <p className="font-semibold text-gray-900">{comp.name}</p>
                        <p className="text-sm text-gray-500">DOB: {comp.dob}</p>
                      </div>
                      <button className="text-gray-400 hover:text-red-500 transition">
                        {/* Trash Icon */}
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                      </button>
                    </div>
                  ))}
                </div>

                <div className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:bg-gray-50 transition cursor-pointer">
                  <h3 className="text-sm font-semibold text-blue-600">+ Add New Companion</h3>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}