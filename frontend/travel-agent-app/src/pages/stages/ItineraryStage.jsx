import React, { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { fetchWithAuth } from '../../authService'; 
import { API_BASE_URL } from '../../config';
import AttractionsStage from './AttractionsStage';
import LogisticsStage from './LogisticsStage';
import { Loader2 } from 'lucide-react';

export default function ItineraryMaster() {
    const { sessionData } = useOutletContext();
    const session = sessionData?.data || sessionData;
    const sessionId = session?.id;

    const [gameState, setGameState] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchState = useCallback(async () => {
        try {
            const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/state/${sessionId}`, {}, "GET");
            if (res && res.ok) {
                const data = await res.json();
                setGameState(data);
            }
        } catch (err) {
            console.error("Master State Load Error:", err);
        } finally {
            setIsLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        if (sessionId) fetchState();
    }, [sessionId, fetchState]);

    // --- CENTRALIZED STAGE MANAGER ---
    const handleUpdateStage = async (targetStage) => {
        try {
            const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/update-stage`, {
                session_id: sessionId,
                stage: targetStage
            }, "POST");
            
            if (res.ok) {
                // Fetch the new state so the UI flips to the correct component
                await fetchState();
            }
        } catch (err) {
            console.error(`Failed to transition to stage ${targetStage}:`, err);
        }
    };

    if (isLoading || !gameState) {
        return (
            <div className="h-full w-full flex items-center justify-center bg-white">
                <Loader2 className="animate-spin text-blue-600" size={40} />
            </div>
        );
    }

    // --- ROUTING LOGIC ---
    
    // STAGE 1: Logistics & Mobility
    if (gameState.stage === 1) {
        return (
            <LogisticsStage 
                gameState={gameState} 
                session={session} 
                refresh={fetchState}
                onBack={() => handleUpdateStage(0)} // Move back to Attractions
                onNext={() => handleUpdateStage(2)} // Move to Schedule
            />
        );
    }

    // STAGE 2: Final Schedule (Placeholder for next step)
    if (gameState.stage === 2) {
        return (
            <div className="p-6">
                <button
                    onClick={() => handleUpdateStage(1)}
                    className="mb-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
                >
                    Back
                </button>

                <div>Schedule Stage Implementation Coming Soon...</div>
            </div>
        );
    }

    // DEFAULT (STAGE 0): Attractions Picker
    return (
        <AttractionsStage 
            gameState={gameState} 
            session={session} 
            onFinalize={() => handleUpdateStage(1)} // Move to Logistics
        />
    );
}