import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet'; // <-- Import Popup
import L from 'leaflet';
import 'leaflet/dist/leaflet.css'; 

// --- HELPER: Create a premium looking numbered pin ---
const createNumberedPin = (number, color) => {
    return L.divIcon({
        className: 'custom-pin',
        html: `
            <div style="
                background-color: ${color}; 
                width: 28px; 
                height: 28px; 
                border-radius: 50%; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: white; 
                font-weight: 900; 
                font-size: 12px; 
                border: 2px solid white; 
                box-shadow: 0 3px 6px rgba(0,0,0,0.3);
            ">
                ${number}
            </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14], 
        popupAnchor: [0, -14], // <-- Ensures the popup opens ABOVE the pin, not covering it
    });
};

export default function ItineraryMap({ schedule }) {
    const dayColors = ['#2563eb', '#9333ea', '#ea580c', '#16a34a', '#dc2626', '#0891b2'];

    if (!schedule || schedule.length === 0) return null;

    let defaultCenter = [41.9, 12.4]; 
    for (const day of schedule) {
        const firstAttr = day.events.find(e => e.latitude && e.longitude);
        if (firstAttr) {
            defaultCenter = [firstAttr.latitude, firstAttr.longitude];
            break;
        }
    }

    return (
        <div style={{ height: '100%', width: '100%', zIndex: 0 }}>
            <MapContainer 
                center={defaultCenter} 
                zoom={13} 
                style={{ height: '100%', width: '100%' }}
                zoomControl={false} 
            >
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {schedule.map((day, dIdx) => {
                    const color = dayColors[dIdx % dayColors.length];
                    
                    const rawLocations = day.events
                        .filter(evt => evt.latitude && evt.longitude)
                        .map(evt => ({
                            latLng: [evt.latitude, evt.longitude],
                            name: evt.name,
                            id: evt.id,
                            // --- Capture extra data for the popup ---
                            imageUrl: evt.image_url, 
                            startTime: evt.start_time,
                            endTime: evt.end_time,
                            bucket: evt.bucket
                        }));

                    if (rawLocations.length === 0) return null;

                    // Micro-Jitter logic
                    const seenCoords = {};
                    const OFFSET = 0.00015; 

                    const locations = rawLocations.map(loc => {
                        const coordKey = `${loc.latLng[0].toFixed(4)},${loc.latLng[1].toFixed(4)}`;
                        
                        if (seenCoords[coordKey]) {
                            const count = seenCoords[coordKey];
                            seenCoords[coordKey] += 1;
                            return {
                                ...loc,
                                latLng: [loc.latLng[0] - (OFFSET * count), loc.latLng[1] + (OFFSET * count)]
                            };
                        } else {
                            seenCoords[coordKey] = 1;
                            return loc;
                        }
                    });

                    const polylinePositions = locations.map(loc => loc.latLng);

                    return (
                        <React.Fragment key={`day-${dIdx}`}>
                            <Polyline 
                                positions={polylinePositions} 
                                pathOptions={{ color: color, weight: 4, opacity: 0.8, dashArray: '8, 8' }} 
                            />

                            {locations.map((loc, i) => (
                                <Marker 
                                    key={`${loc.id}-${i}`} 
                                    position={loc.latLng}
                                    icon={createNumberedPin(i + 1, color)}
                                >
                                    {/* --- THE POPUP UI --- */}
                                    <Popup className="custom-popup" closeButton={false}>
                                        <div className="flex flex-col w-[180px]">
                                            {/* Show image if we have it */}
                                            {loc.imageUrl && (
                                                <img 
                                                    src={loc.imageUrl} 
                                                    alt={loc.name} 
                                                    className="w-full h-24 object-cover rounded-t-lg mb-2"
                                                />
                                            )}
                                            
                                            <div className={!loc.imageUrl ? "p-2" : "px-2 pb-2"}>
                                                <h3 className="font-bold text-[13px] text-gray-900 leading-tight mb-1">
                                                    {loc.name}
                                                </h3>
                                                
                                                <div className="flex items-center justify-between mt-2">
                                                    <span className="text-[10px] font-bold text-gray-500">
                                                        {loc.startTime} - {loc.endTime}
                                                    </span>
                                                    
                                                    {loc.bucket && loc.bucket !== 'logistics' && (
                                                        <span className="text-[9px] font-bold uppercase text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                                            {loc.bucket}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </Popup>
                                </Marker>
                            ))}
                        </React.Fragment>
                    );
                })}
            </MapContainer>
        </div>
    );
}