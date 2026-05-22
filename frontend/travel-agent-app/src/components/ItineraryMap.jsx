import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// --- HELPER: Pure JavaScript Google Encoded Polyline Decoder ---
function decodePolyline(encoded) {
    if (!encoded) return [];
    let points = [];
    let index = 0, len = encoded.length;
    let lat = 0, lng = 0;

    while (index < len) {
        let b, shift = 0, result = 0;
        do {
            b = encoded.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);
        let dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
        lat += dlat;

        shift = 0;
        result = 0;
        do {
            b = encoded.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);
        let dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
        lng += dlng;

        points.push([lat / 1e5, lng / 1e5]);
    }
    return points;
}

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
        "`,
        iconSize: [28, 28],
        iconAnchor: [14, 14], 
        popupAnchor: [0, -14], 
    });
};

// --- HELPER: Dynamic Continuous Dash Pattern Generator ---
// We use lineCap: 'round' to make all dashes soft and pill-shaped.
// By avoiding purely isolated dots, every line stays continuous and easy to track.
const getVerifiedLegDashPattern = (dayIdx, legIdx) => {
    const patterns = [
        '4, 6',             // Sleek, rapid short pill-dashes
        '14, 6',            // Elegant long pill-segments
        '12, 6, 0, 6',      // Premium long dash + circular dot sequence
        '8, 5, 2, 5',       // Dynamic long-short alternating sequence
        '16, 6, 4, 6',      // Broad block + distinct accent dash
        '6, 5, 6, 5'        // Standard medium-spaced layout tracking
    ];
    const targetPatternIndex = (dayIdx + legIdx * 2) % patterns.length;
    return patterns[targetPatternIndex];
};

export default function ItineraryMap({ schedule }) {
    const dayColors = ['#2563eb', '#9333ea', '#ea580c', '#16a34a', '#dc2626', '#0891b2'];
    const ESTIMATED_LINE_COLOR = '#94a3b8';

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
                    
                    const locations = day.events
                        .filter(evt => evt.latitude && evt.longitude)
                        .map(evt => ({
                            latLng: [evt.latitude, evt.longitude],
                            name: evt.name,
                            id: evt.id,
                            imageUrl: evt.image_url, 
                            startTime: evt.start_time,
                            endTime: evt.end_time,
                            bucket: evt.bucket,
                            transitLeg: evt.transit_leg 
                        }));

                    if (locations.length === 0) return null;

                    const seenCoords = {};
                    const OFFSET = 0.00015; 

                    const jitteredLocations = locations.map(loc => {
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

                    return (
                        <React.Fragment key={`day-${dIdx}`}>
                            
                            {/* --- HYBRID PATH RENDERING PIPELINE --- */}
                            {jitteredLocations.map((loc, idx) => {
                                if (idx === 0) return null; 
                                const prevLoc = jitteredLocations[idx - 1];
                                const leg = loc.transitLeg;

                                // CASE 1: Google Verified Street Path -> Fine, stylized continuous pill-dashes
                                if (leg && leg.is_verified && leg.polyline) {
                                    const roadPositions = decodePolyline(leg.polyline);
                                    const dynamicDashPattern = getVerifiedLegDashPattern(dIdx, idx);
                                    
                                    return (
                                        <Polyline 
                                            key={`road-leg-${idx}`}
                                            positions={roadPositions}
                                            pathOptions={{ 
                                                color: color, 
                                                weight: 2,
                                                opacity: 0.4,
                                                lineCap: 'round',
                                                lineJoin: 'round',
                                                dashArray: dynamicDashPattern
                                            }} 
                                        />
                                    );
                                }

                                // CASE 2: Sandbox Fallback/Estimate -> Ultra-fine neutral slate tracking dashes
                                return (
                                    <Polyline 
                                        key={`est-leg-${idx}`}
                                        positions={[prevLoc.latLng, loc.latLng]}
                                        pathOptions={{ 
                                            color: ESTIMATED_LINE_COLOR, 
                                            weight: 1.5,          // Subdued weight for non-synced movements
                                            opacity: 0.5, 
                                            dashArray: '2, 5' 
                                        }} 
                                    />
                                );
                            })}

                            {/* --- MARKER OVERLAYS CANVAS --- */}
                            {jitteredLocations.map((loc, i) => (
                                <Marker 
                                    key={`${loc.id}-${i}`} 
                                    position={loc.latLng}
                                    icon={createNumberedPin(i + 1, color)}
                                >
                                    <Popup className="custom-popup" closeButton={false}>
                                        <div className="flex flex-col w-[180px]">
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