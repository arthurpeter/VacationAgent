import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';

export default function NewVacationModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  
  const [userProfile, setUserProfile] = useState(null);
  const [isFetchingProfile, setIsFetchingProfile] = useState(false);

  const [usePreferences, setUsePreferences] = useState(false);
  
  const [selectedCompanions, setSelectedCompanions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const fetchProfile = async () => {
        setIsFetchingProfile(true);
        try {
          const res = await fetchWithAuth(`${API_BASE_URL}/users/me`, {}, "GET");
          if (res && res.ok) {
            const data = await res.json();
            setUserProfile(data);
            
            if ((data.home_airports && data.home_airports.length > 0) || data.currency_preference) {
                setUsePreferences(true);
            }
          }
        } catch (error) {
          console.error("Failed to fetch user profile:", error);
        } finally {
          setIsFetchingProfile(false);
        }
      };
      fetchProfile();
    } else {
      setUserProfile(null);
      setUsePreferences(false);
      setSelectedCompanions([]);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const hasAirports = userProfile?.home_airports && userProfile.home_airports.length > 0;
  const hasCurrency = !!userProfile?.currency_preference;
  const hasCompanions = userProfile?.companions && userProfile.companions.length > 0;

  const handleCompanionToggle = (companionId) => {
    setSelectedCompanions(prev => 
      prev.includes(companionId) 
        ? prev.filter(id => id !== companionId)
        : [...prev, companionId]
    );
  };

  const calculateTravelers = () => {
    let adults = 1;
    let children = 0;
    let infants_in_seat = 0;
    let infants_on_lap = 0;
    let children_ages = [];

    selectedCompanions.forEach(compId => {
      const comp = userProfile.companions.find(c => c.id === compId);
      if (!comp || !comp.date_of_birth) return;

      const birthYear = new Date(comp.date_of_birth).getFullYear();
      const currentYear = new Date().getFullYear();
      const age = currentYear - birthYear;

      if (age >= 12) {
        adults += 1;
      } else if (age >= 2) {
        children += 1;
        children_ages.push(age);
      } else {
        if (comp.is_infant_on_lap) infants_on_lap += 1;
        else infants_in_seat += 1;
        children_ages.push(age);
      }
    });

    return { 
      adults, 
      children, 
      infants_in_seat, 
      infants_on_lap, 
      children_ages: children_ages.join(',') 
    };
  };

  const handleCreateSession = async () => {
    setIsLoading(true);
    try {
      const createRes = await fetchWithAuth(`${API_BASE_URL}/session/create`, {}, "POST");
      if (!createRes) {
        setIsLoading(false);
        return; 
      }
      if (!createRes.ok) throw new Error("Failed to create session");

      const createData = await createRes.json();
      const sessionId = createData.session_id;

      let patchData = {};
      
      if (usePreferences) {
        if (hasAirports) {
            patchData.departure = userProfile.home_airports.join(',');
        }
        if (hasCurrency) {
            patchData.currency = userProfile.currency_preference;
        }
      }
      
      const travelers = calculateTravelers();
      patchData = { ...patchData, ...travelers, companion_ids: selectedCompanions };

      if (Object.keys(patchData).length > 0) {
        await fetchWithAuth(`${API_BASE_URL}/session/${sessionId}/details`, patchData, "PATCH");
      }

      navigate(`/plan/${sessionId}/discovery`); 
      
    } catch (error) {
      console.error("Error creating session:", error);
      alert("Something went wrong starting your session.");
    } finally {
      setIsLoading(false);
      onClose(); 
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl transform transition-all">
        <h2 className="text-2xl font-extrabold text-gray-900 mb-2">Start a New Vacation</h2>
        
        {isFetchingProfile ? (
          <div className="py-8 flex justify-center items-center">
             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {(!hasAirports && !hasCurrency && !hasCompanions) ? (
              <p className="mb-8 text-gray-500">
                Ready to plan your next trip? Let's get started.
              </p>
            ) : (
              <div className="mb-6 mt-4">
                
                {(hasAirports || hasCurrency) && (
                  <label className="flex items-start space-x-3 mb-4 cursor-pointer group bg-blue-50 p-4 rounded-xl border border-blue-100">
                    <input 
                      type="checkbox" 
                      checked={usePreferences} 
                      onChange={(e) => setUsePreferences(e.target.checked)}
                      className="mt-1 w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                    />
                    <div className="text-gray-700 group-hover:text-gray-900 transition flex flex-col">
                      <span className="font-semibold text-gray-900 mb-1">Apply my saved preferences</span>
                      <ul className="text-sm space-y-1">
                        {hasAirports && (
                            <li><span className="text-gray-500">Airports:</span> <span className="font-medium">{userProfile.home_airports.join(', ')}</span></li>
                        )}
                        {hasCurrency && (
                            <li><span className="text-gray-500">Currency:</span> <span className="font-medium">{userProfile.currency_preference}</span></li>
                        )}
                      </ul>
                    </div>
                  </label>
                )}

                {hasCompanions && (
                  <div className="mt-6 border-t pt-4">
                    <p className="text-sm font-semibold text-gray-800 mb-3">Who is traveling with you?</p>
                    {userProfile.companions.map(companion => (
                      <label key={companion.id} className="flex items-center space-x-3 mb-2 cursor-pointer group hover:bg-gray-50 p-2 rounded-lg transition">
                        <input 
                          type="checkbox" 
                          checked={selectedCompanions.includes(companion.id)} 
                          onChange={() => handleCompanionToggle(companion.id)}
                          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                        />
                        <span className="text-gray-700 group-hover:text-gray-900 transition text-sm font-medium">
                          {companion.name} 
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        <div className="flex justify-end space-x-4 mt-6">
          <button 
            onClick={onClose}
            disabled={isLoading}
            className="px-5 py-2.5 text-gray-600 font-medium hover:bg-gray-100 rounded-xl transition"
          >
            Cancel
          </button>
          <button 
            onClick={handleCreateSession}
            disabled={isLoading || isFetchingProfile}
            className="px-5 py-2.5 bg-blue-600 text-white font-bold rounded-xl shadow-md hover:bg-blue-700 disabled:opacity-50 transition transform hover:-translate-y-0.5"
          >
            {isLoading ? 'Setting up...' : 'Start Planning'}
          </button>
        </div>
      </div>
    </div>
  );
}