import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../authService'; 
import { API_BASE_URL } from '../config'; 
import { toast, Toaster } from 'react-hot-toast';
import { ALL_CURRENCIES } from '../utils/currencies';

export default function Profile() {
  const { isAuthenticated } = useAuth(); 
  const [activeTab, setActiveTab] = useState('preferences');
  const [loading, setLoading] = useState(true);

  // --- USER PROFILE STATE ---
  const [email, setEmail] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [userDescription, setUserDescription] = useState('');
  
  // --- PREFERENCES STATE ---
  const [airports, setAirports] = useState([]);
  const [currencySearch, setCurrencySearch] = useState('');
  
  // --- VAULT STATE ---
  const [companions, setCompanions] = useState([]);
  const [newCompanion, setNewCompanion] = useState({
    name: '',
    date_of_birth: '',
    description: '',
    is_infant_on_lap: false
  });

  // --- UI TOGGLE STATE ---
  const [showCurrencyDropdown, setShowCurrencyDropdown] = useState(false);
  const [showAirportDropdown, setShowAirportDropdown] = useState(false);
  const [airportSearch, setAirportSearch] = useState('');
  
  // --- DYNAMIC AIRPORT SEARCH STATE ---
  const [airportOptions, setAirportOptions] = useState([]);
  const [isSearchingAirports, setIsSearchingAirports] = useState(false);
  
  const currencyRef = useRef(null);
  const airportRef = useRef(null);

  const API_URL = API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // --- 1. FETCH PROFILE DATA ON MOUNT ---
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetchWithAuth(`${API_URL}/users/me`, {}, 'GET');
        
        if (response && response.ok) {
          const data = await response.json();
          setEmail(data.email || '');
          setDateOfBirth(data.date_of_birth ? data.date_of_birth.split('T')[0] : '');
          setUserDescription(data.user_description || '');
          setAirports(data.home_airports || []); 
          setCurrencySearch(data.currency_preference || '');
          setCompanions(data.companions || []);
        }
      } catch (error) {
        console.error("Failed to fetch profile", error);
      } finally {
        setLoading(false);
      }
    };
    
    if (isAuthenticated) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [API_URL, isAuthenticated]);

  // Click outside listeners for custom dropdowns
  useEffect(() => {
    function handleClickOutside(event) {
      if (currencyRef.current && !currencyRef.current.contains(event.target)) setShowCurrencyDropdown(false);
      if (airportRef.current && !airportRef.current.contains(event.target)) setShowAirportDropdown(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // --- DEBOUNCED AIRPORT SEARCH ---
  useEffect(() => {
    if (airportSearch.trim().length < 2) {
      setAirportOptions([]);
      return;
    }

    const delayDebounceFn = setTimeout(async () => {
      setIsSearchingAirports(true);
      try {
        const response = await fetchWithAuth(`${API_URL}/search/airports/autocomplete?q=${encodeURIComponent(airportSearch)}`, {}, 'GET');
        
        if (response && response.ok) {
          const data = await response.json();
          setAirportOptions(data);
        }
      } catch (error) {
        console.error("Failed to fetch airports", error);
      } finally {
        setIsSearchingAirports(false);
      }
    }, 300); // Wait 300ms before calling API

    return () => clearTimeout(delayDebounceFn);
  }, [airportSearch, API_URL]);

  // --- 2. UPDATE PROFILE (PATCH /users/me) ---
  const saveProfileUpdates = async (updateData) => {
    const loadingToast = toast.loading('Saving updates...');
    
    try {
      const response = await fetchWithAuth(`${API_URL}/users/me`, updateData, 'PATCH');
      
      if (response && response.ok) {
        toast.success('Profile updated successfully!', { id: loadingToast });
      } else {
        toast.error('Failed to update profile.', { id: loadingToast });
      }
    } catch (error) {
      toast.error('Network error occurred.', { id: loadingToast });
    }
  };

  // --- 3. ADD COMPANION (POST /users/me/companions) ---
  const handleAddCompanion = async () => {
    if (!newCompanion.name || !newCompanion.date_of_birth) return;

    const payload = {
      name: newCompanion.name.trim(),
      date_of_birth: new Date(newCompanion.date_of_birth).toISOString(),
      description: newCompanion.description.trim() ? newCompanion.description.trim() : null,
      is_infant_on_lap: Boolean(newCompanion.is_infant_on_lap)
    };

    const loadingToast = toast.loading('Adding companion...');

    try {
      const response = await fetchWithAuth(`${API_URL}/users/me/companions`, payload, 'POST');
      
      if (response && response.ok) {
        const addedCompanion = await response.json();
        addedCompanion.date_of_birth = addedCompanion.date_of_birth.split('T')[0];
        
        setCompanions([...companions, addedCompanion]);
        setNewCompanion({ name: '', date_of_birth: '', description: '', is_infant_on_lap: false });
        toast.success('Companion added to vault!', { id: loadingToast });
      } else {
        toast.error('Failed to add companion. Please check details.', { id: loadingToast });
      }
    } catch (error) {
      toast.error('Failed to add companion.', { id: loadingToast });
    }
  };

  // --- 4. REMOVE COMPANION (DELETE /users/me/companions/{id}) ---
  const handleRemoveCompanion = async (companionId) => {
    try {
      const response = await fetchWithAuth(`${API_URL}/users/me/companions/${companionId}`, {}, 'DELETE');
      
      if (response && response.ok) {
        setCompanions(companions.filter(c => c.id !== companionId));
        toast.success('Companion removed!');
      } else {
        toast.error('Failed to remove companion.');
      }
    } catch (error) {
      console.error("Failed to remove companion", error);
      toast.error('Network error occurred.');
    }
  };

  // --- HELPERS ---
  const handleAddAirport = (code) => {
    // Only add it if it's not already in the array
    if (!airports.includes(code)) {
      setAirports([...airports, code]);
    }
    // Deliberately not clearing the search or closing the dropdown
    // so users can select multiple airports in one go.
  };

  const removeAirport = (code) => {
    setAirports(airports.filter(a => a !== code));
  };

  const isInfant = (dobString) => {
    if (!dobString) return false;
    const diff = Date.now() - new Date(dobString).getTime();
    const ageDate = new Date(diff); 
    return Math.abs(ageDate.getUTCFullYear() - 1970) < 2;
  };

  const filteredCurrencies = ALL_CURRENCIES.filter(c => c.code.toLowerCase().startsWith(currencySearch.toLowerCase()));

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading profile...</div>;

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <Toaster position="bottom-right" /> 

      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Your Profile</h1>
            <p className="text-gray-500 mt-2">Manage your account and teach the AI how you like to travel.</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row">
          
          {/* Sidebar Navigation */}
          <div className="w-full md:w-64 bg-gray-50 border-b md:border-b-0 md:border-r border-gray-100 p-6 space-y-2">
            <button onClick={() => setActiveTab('preferences')} className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'preferences' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}>Travel Preferences</button>
            <button onClick={() => setActiveTab('account')} className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'account' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}>Account Details</button>
            <button onClick={() => setActiveTab('vault')} className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'vault' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}>Traveler Vault</button>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-8 min-h-[500px]">
            
            {/* --- TRAVEL PREFERENCES TAB --- */}
            {activeTab === 'preferences' && (
              <div className="space-y-8 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">AI Travel Preferences</h2>
                
                {/* Currency */}
                <div className="relative w-full md:w-1/2" ref={currencyRef}>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Default Currency</label>
                  <input
                    type="text"
                    value={currencySearch}
                    onChange={(e) => { setCurrencySearch(e.target.value); setShowCurrencyDropdown(true); }}
                    onFocus={() => setShowCurrencyDropdown(true)}
                    placeholder="Search currency (e.g., EUR)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none uppercase"
                  />
                  {showCurrencyDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                      {filteredCurrencies.map(c => (
                        <div key={c.code} onClick={() => { setCurrencySearch(c.code); setShowCurrencyDropdown(false); }} className="px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm">
                          <span className="font-bold text-gray-800 mr-2">{c.code}</span><span className="text-gray-500">{c.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Airports */}
                <div className="relative" ref={airportRef}>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Preferred Departure Airports</label>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {airports.map(code => (
                      <span key={code} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
                        ✈️ {code} <button onClick={() => removeAirport(code)} className="ml-2 text-blue-400 hover:text-blue-600">&times;</button>
                      </span>
                    ))}
                  </div>
                  <input 
                    type="text" 
                    value={airportSearch}
                    onChange={(e) => { setAirportSearch(e.target.value); setShowAirportDropdown(true); }}
                    onFocus={() => setShowAirportDropdown(true)}
                    placeholder="Search by city (e.g., Bucharest) or code"
                    className="w-full md:w-2/3 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none"
                  />
                  {/* Dynamic Dropdown */}
                  {showAirportDropdown && airportSearch.trim().length >= 2 && (
                    <div className="absolute z-10 w-full md:w-2/3 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                      {isSearchingAirports ? (
                        <div className="px-4 py-3 text-sm text-gray-500 font-medium animate-pulse">
                          Searching airports...
                        </div>
                      ) : airportOptions.length > 0 ? (
                        airportOptions.map(a => {
                          const isSelected = airports.includes(a.code);
                          
                          return (
                            <div 
                              key={a.code} 
                              onClick={() => handleAddAirport(a.code)} 
                              className={`px-4 py-3 border-b last:border-0 transition-colors ${
                                isSelected ? 'bg-gray-50 opacity-60 cursor-default' : 'hover:bg-blue-50 cursor-pointer'
                              }`}
                            >
                              <div className="flex justify-between items-center">
                                <div>
                                  <p className="text-sm font-bold text-gray-800">{a.city}</p>
                                  <p className="text-xs text-gray-500">{a.name} Airport</p>
                                </div>
                                <div className="flex items-center gap-2">
                                  {isSelected && <span className="text-xs text-green-600 font-bold">Added ✓</span>}
                                  <span className="bg-white text-gray-700 text-xs font-bold px-2 py-1 rounded border border-gray-200 shadow-sm">
                                    {a.code}
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="px-4 py-3 text-sm text-gray-500">
                          No airports found. Try a different city or code.
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t">
                  <button onClick={() => saveProfileUpdates({ currency_preference: currencySearch, home_airports: airports })} className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">
                    Save Preferences
                  </button>
                </div>
              </div>
            )}

            {/* --- ACCOUNT DETAILS TAB --- */}
            {activeTab === 'account' && (
              <div className="space-y-6 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">Account Details</h2>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  <input type="email" disabled value={email} className="w-full md:w-2/3 px-4 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-500 cursor-not-allowed" />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Your Date of Birth</label>
                  <input 
                    type="date" 
                    value={dateOfBirth} 
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full md:w-1/2 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none text-gray-700" 
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">About You (For the AI)</label>
                  <textarea 
                    rows="3" 
                    value={userDescription}
                    onChange={(e) => setUserDescription(e.target.value)}
                    placeholder="E.g., I love history, avoiding crowded tourist traps, and I'm a vegetarian."
                    className="w-full md:w-2/3 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none text-gray-700 resize-none"
                  ></textarea>
                  <p className="text-xs text-gray-500 mt-1">Describe your travel style. The AI uses this to personalize your trips.</p>
                </div>
                
                <div className="pt-8 border-t mt-8">
                  <button 
                    onClick={() => saveProfileUpdates({ 
                      date_of_birth: dateOfBirth ? new Date(dateOfBirth).toISOString() : null, 
                      user_description: userDescription 
                    })} 
                    className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition mb-6 block"
                  >
                    Save Account Details
                  </button>
                </div>
              </div>
            )}

            {/* --- TRAVELER VAULT TAB --- */}
            {activeTab === 'vault' && (
              <div className="space-y-6 animate-fadeIn">
                <h2 className="text-xl font-bold text-gray-900 border-b pb-4">Traveler Vault</h2>
                <p className="text-gray-600 text-sm mb-4">Save details for the people you travel with frequently.</p>
                
                {/* Companions List */}
                <div className="space-y-4 mb-8">
                  {companions.map(comp => (
                    <div key={comp.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 border border-gray-200 rounded-xl bg-gray-50">
                      <div>
                        <p className="font-bold text-gray-900">{comp.name}</p>
                        <p className="text-sm text-gray-500">
                          DOB: {comp.date_of_birth ? comp.date_of_birth.split('T')[0] : ''} 
                          {comp.is_infant_on_lap ? ' (Infant on Lap)' : ''}
                        </p>
                        {comp.description && <p className="text-sm text-gray-600 mt-1 italic">"{comp.description}"</p>}
                      </div>
                      <button onClick={() => handleRemoveCompanion(comp.id)} className="mt-2 sm:mt-0 text-gray-400 hover:text-red-500 transition">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                      </button>
                    </div>
                  ))}
                  {companions.length === 0 && <p className="text-sm text-gray-400 italic">No companions added yet.</p>}
                </div>

                {/* Add New Companion Form */}
                <div className="border border-gray-200 rounded-xl p-6 bg-white shadow-sm">
                  <h3 className="text-md font-semibold text-gray-800 mb-4">Add New Companion</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">Name / Alias *</label>
                      <input 
                        type="text" placeholder="e.g., Wife, Timmy" 
                        value={newCompanion.name} onChange={e => setNewCompanion({...newCompanion, name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-400 focus:outline-none text-sm" 
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">Date of Birth *</label>
                      <input 
                        type="date" 
                        value={newCompanion.date_of_birth} onChange={e => setNewCompanion({...newCompanion, date_of_birth: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-400 focus:outline-none text-sm" 
                      />
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Preferences / Description (Optional)</label>
                    <input 
                      type="text" placeholder="e.g., Loves museums, allergic to nuts" 
                      value={newCompanion.description} onChange={e => setNewCompanion({...newCompanion, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-400 focus:outline-none text-sm" 
                    />
                  </div>

                  {/* Smart Infant Checkbox */}
                  {isInfant(newCompanion.date_of_birth) && (
                    <div className="mb-4 flex items-center gap-2 bg-yellow-50 p-3 rounded-md border border-yellow-100">
                      <input 
                        type="checkbox" id="lap-infant" 
                        checked={newCompanion.is_infant_on_lap} 
                        onChange={e => setNewCompanion({...newCompanion, is_infant_on_lap: e.target.checked})}
                        className="w-4 h-4 text-blue-600 rounded" 
                      />
                      <label htmlFor="lap-infant" className="text-sm text-yellow-800">This traveler is an infant. Will they travel on your lap?</label>
                    </div>
                  )}

                  <button 
                    onClick={handleAddCompanion}
                    disabled={!newCompanion.name || !newCompanion.date_of_birth}
                    className="bg-gray-900 text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800 transition text-sm disabled:opacity-50"
                  >
                    Save Companion
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
