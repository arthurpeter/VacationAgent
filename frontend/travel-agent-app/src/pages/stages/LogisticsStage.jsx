import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Car,
  Train,
  Sparkles,
  AlertTriangle,
  Check,
  Loader2,
  ExternalLink,
  Clock,
  Banknote,
  Zap,
} from 'lucide-react';

import PageTransition from '../../components/PageTransition';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';

const paceMarks = [
  {
    label: 'Relaxed',
    description: '2-3 attractions/day with plenty of downtime.',
  },
  {
    label: 'Moderate',
    description: 'Balanced sightseeing and free time.',
  },
  {
    label: 'Fast-Paced',
    description: 'Packed schedule with maximum exploration.',
  },
];

function RecommendationCard({
  title,
  recommendation,
  reasoning,
  icon: Icon,
  color = 'blue',
}) {
  const styles = {
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-100',
      icon: 'bg-blue-600',
      text: 'text-blue-700',
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-100',
      icon: 'bg-purple-600',
      text: 'text-purple-700',
    },
  };

  const s = styles[color];

  return (
    <div className={`${s.bg} ${s.border} border rounded-[2rem] p-6`}>
      <div className="flex items-start gap-4">
        <div
          className={`w-12 h-12 rounded-2xl ${s.icon} text-white flex items-center justify-center shrink-0`}
        >
          <Icon size={22} />
        </div>

        <div>
          <p
            className={`text-[11px] font-black uppercase tracking-widest ${s.text}`}
          >
            AI Recommendation
          </p>

          <h3 className="text-xl font-black text-gray-900 mt-1">
            {recommendation}
          </h3>

          <p className="text-sm text-gray-600 leading-relaxed mt-2">
            {reasoning}
          </p>
        </div>
      </div>
    </div>
  );
}

function TransportCard({
  active,
  onClick,
  title,
  description,
  icon: Icon,
}) {
  return (
    <button
      onClick={onClick}
      className={`relative text-left p-6 rounded-[2rem] border-2 transition-all ${
        active
          ? 'border-blue-600 bg-blue-50 shadow-lg'
          : 'border-gray-200 bg-white hover:border-blue-200'
      }`}
    >
      {active && (
        <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center">
          <Check size={14} strokeWidth={4} />
        </div>
      )}

      <div
        className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
          active
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-500'
        }`}
      >
        <Icon size={28} />
      </div>

      <h3 className="mt-5 text-lg font-black text-gray-900">{title}</h3>

      <p className="mt-2 text-sm text-gray-500 leading-relaxed">
        {description}
      </p>
    </button>
  );
}

export default function LogisticsStage({
  gameState,
  session,
  refresh,
  onBack,
  onNext,
}) {
  const [paceValue, setPaceValue] = useState(50);

  const [selectedTransport, setSelectedTransport] =
    useState('public_transport');

  const [loadingTransportInfo, setLoadingTransportInfo] = useState(false);

  const [offerData, setOfferData] = useState(null);

  const [loadingRecommendations, setLoadingRecommendations] =
    useState(false);

  const mobilityRecommendation =
    gameState.mobility_recommendation;

  const paceRecommendation =
    gameState.pace_recommendation;

  const recommendedTransport = useMemo(() => {
    if (!mobilityRecommendation) return null;

    return mobilityRecommendation.should_rent_car
      ? 'rental_car'
      : 'public_transport';
  }, [mobilityRecommendation]);

  const selectedPace = useMemo(() => {
    if (paceValue <= 33) return 'Relaxed';
    if (paceValue <= 66) return 'Moderate';
    return 'Fast-Paced';
  }, [paceValue]);

  const isGoingAgainstRecommendation =
    recommendedTransport &&
    selectedTransport !== recommendedTransport;

  useEffect(() => {
    const loadRecommendations = async () => {
      setLoadingRecommendations(true);

      try {
        await Promise.all([
          fetchWithAuth(
            `${API_BASE_URL}/itinerary/logistics/transport`,
            {
              session_id: session.id,
              action: 'mobility_recommendation',
            },
            'POST'
          ),

          fetchWithAuth(
            `${API_BASE_URL}/itinerary/logistics/transport`,
            {
              session_id: session.id,
              action: 'pace_recommendation',
            },
            'POST'
          ),
        ]);

        refresh();
      } catch (e) {
        console.error(e);
      } finally {
        setLoadingRecommendations(false);
      }
    };

    if (
      !gameState.mobility_recommendation ||
      !gameState.pace_recommendation
    ) {
      loadRecommendations();
    }
  }, []);

  const fetchTransportInfo = async (type) => {
    setLoadingTransportInfo(true);

    try {
      const action =
        type === 'rental_car'
          ? 'search_rental_car_offers'
          : 'search_public_transport_offers';

      const res = await fetchWithAuth(
        `${API_BASE_URL}/itinerary/logistics/transport`,
        {
          session_id: session.id,
          action,
        },
        'POST'
      );

      if (res.ok) {
        const data = await res.json();

        const transportData =
          data.mobility_config.strategies[type];

        setOfferData({
          type,
          ...transportData,
        });

        refresh();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingTransportInfo(false);
    }
  };

  const saveMobility = async (transportType) => {
    try {
      const config = {
        preference_mode: 'smart_optimization',
        strategies: {
          public_transport: {
            enabled: transportType === 'public_transport',
          },
          rental_car: {
            enabled: transportType === 'rental_car',
          },
        },
      };

      await fetchWithAuth(
        `${API_BASE_URL}/itinerary/update-mobility`,
        {
          session_id: session.id,
          config,
        },
        'POST'
      );
    } catch (e) {
      console.error(e);
    }
  };

  const savePace = async (pace) => {
    try {
      await fetchWithAuth(
        `${API_BASE_URL}/itinerary/logistics/pace`,
        {
          session_id: session.id,
          pace,
        },
        'POST'
      );
    } catch (e) {
      console.error(e);
    }
  };

  const handleTransportSelect = async (type) => {
    setSelectedTransport(type);

    await saveMobility(type);

    await fetchTransportInfo(type);
  };

  const handleContinue = async () => {
    await savePace(selectedPace);
    onNext();
  };

  return (
    <PageTransition className="w-full h-full bg-gray-50 overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">

        {/* HEADER */}

        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-500 hover:text-blue-600 font-bold"
          >
            <ArrowLeft size={18} />
            Back
          </button>

          <button
            onClick={handleContinue}
            className="bg-gray-900 hover:bg-blue-600 text-white px-8 py-4 rounded-2xl font-black flex items-center gap-2 transition-all shadow-lg"
          >
            Generate Itinerary
            <ArrowRight size={18} />
          </button>
        </div>

        {/* TITLE */}

        <div className="mb-10">
          <h1 className="text-5xl font-black text-gray-900 tracking-tight">
            Travel Style
          </h1>

          <p className="text-lg text-gray-500 mt-3">
            Configure how you want to experience your trip.
          </p>
        </div>

        {/* RECOMMENDATIONS */}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          {loadingRecommendations ? (
            <div className="col-span-2 bg-white rounded-[2rem] p-12 border border-gray-200 flex items-center justify-center gap-3">
              <Loader2 className="animate-spin text-blue-600" />
              <span className="font-bold text-gray-600">
                AI analyzing your trip...
              </span>
            </div>
          ) : (
            <>
              {mobilityRecommendation && (
                <RecommendationCard
                  title="Mobility"
                  recommendation={
                    mobilityRecommendation.recommendation
                  }
                  reasoning={mobilityRecommendation.reasoning}
                  icon={Train}
                  color="blue"
                />
              )}

              {paceRecommendation && (
                <RecommendationCard
                  title="Pace"
                  recommendation={
                    paceRecommendation.recommendation
                  }
                  reasoning={paceRecommendation.reasoning}
                  icon={Zap}
                  color="purple"
                />
              )}
            </>
          )}
        </div>

        {/* WARNING */}

        {isGoingAgainstRecommendation && (
          <div className="mb-10 bg-amber-50 border border-amber-200 rounded-[2rem] p-5 flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500 text-white flex items-center justify-center shrink-0">
              <AlertTriangle size={22} />
            </div>

            <div>
              <h3 className="font-black text-amber-800">
                You're going against the AI recommendation
              </h3>

              <p className="text-sm text-amber-700 mt-1 leading-relaxed">
                The AI recommended{' '}
                {recommendedTransport === 'rental_car'
                  ? 'a rental car'
                  : 'public transport'}
                , but your itinerary can still be generated with your
                selected option.
              </p>
            </div>
          </div>
        )}

        {/* PACE */}

        <div className="bg-white border border-gray-200 rounded-[3rem] p-10 mb-10">
          <h2 className="text-3xl font-black text-gray-900">
            Trip Pace
          </h2>

          <p className="text-gray-500 mt-2">
            Control how packed your itinerary should feel.
          </p>

          <div className="mt-10">
            <input
              type="range"
              min="0"
              max="100"
              value={paceValue}
              onChange={(e) =>
                setPaceValue(Number(e.target.value))
              }
              className="w-full h-3 rounded-full accent-blue-600 cursor-pointer"
            />

            <div className="grid grid-cols-3 gap-4 mt-8">
              {paceMarks.map((pace) => (
                <div
                  key={pace.label}
                  className={`rounded-2xl border p-5 transition-all ${
                    selectedPace === pace.label
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200'
                  }`}
                >
                  <h3 className="font-black text-gray-900">
                    {pace.label}
                  </h3>

                  <p className="text-sm text-gray-500 mt-2">
                    {pace.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* TRANSPORT */}

        <div className="bg-white border border-gray-200 rounded-[3rem] p-10">
          <h2 className="text-3xl font-black text-gray-900">
            Getting Around
          </h2>

          <p className="text-gray-500 mt-2">
            Choose your preferred transportation style.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-10">
            <TransportCard
              active={selectedTransport === 'public_transport'}
              onClick={() =>
                handleTransportSelect('public_transport')
              }
              title="Public Transport"
              description="Best for cities, museums and central sightseeing."
              icon={Train}
            />

            <TransportCard
              active={selectedTransport === 'rental_car'}
              onClick={() =>
                handleTransportSelect('rental_car')
              }
              title="Rental Car"
              description="Best for road trips, nature and remote attractions."
              icon={Car}
            />
          </div>

          {/* DYNAMIC OFFER PANEL */}

          {(loadingTransportInfo || offerData) && (
            <div className="mt-8 bg-gray-50 border border-gray-200 rounded-[2rem] p-8">
              {loadingTransportInfo ? (
                <div className="flex items-center gap-3">
                  <Loader2 className="animate-spin text-blue-600" />

                  <span className="font-bold text-gray-600">
                    Fetching official travel information...
                  </span>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between flex-wrap gap-6">
                    <div>
                      <p className="text-[11px] uppercase tracking-widest font-black text-blue-600">
                        Official Information
                      </p>

                      <h3 className="text-2xl font-black text-gray-900 mt-2">
                        {offerData.type === 'rental_car'
                          ? 'Rental Car Estimate'
                          : 'Transit Pass'}
                      </h3>
                    </div>

                    <div className="bg-white rounded-2xl border border-gray-200 px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Banknote className="text-green-600" />

                        <div>
                          <p className="text-xs text-gray-500 font-bold">
                            Estimated Price
                          </p>

                          <p className="text-2xl font-black text-gray-900">
                            {offerData.currency || 'EUR'}{' '}
                            {offerData.daily_price_est ||
                              offerData.pass_price_est}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {offerData.ztl_warning && (
                    <div className="mt-6 bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
                      <AlertTriangle
                        size={18}
                        className="text-amber-600 shrink-0 mt-0.5"
                      />

                      <p className="text-sm text-amber-700">
                        Restricted traffic zones (ZTL) detected in
                        this destination.
                      </p>
                    </div>
                  )}

                  <div className="mt-6 flex items-center gap-6 flex-wrap">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock size={16} />

                      <span className="font-medium text-sm">
                        {offerData.operating_hours?.open || '05:00'} -{' '}
                        {offerData.operating_hours?.close || '23:00'}
                      </span>
                    </div>

                    {offerData.official_link && (
                      <a
                        href={offerData.official_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 bg-gray-900 hover:bg-blue-600 text-white px-5 py-3 rounded-xl font-bold transition-all"
                      >
                        Official Website
                        <ExternalLink size={16} />
                      </a>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  );
}