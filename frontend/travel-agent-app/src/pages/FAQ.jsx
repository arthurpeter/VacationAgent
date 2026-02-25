import React from 'react';
import { Link } from 'react-router-dom';

export default function FAQ() {
  const faqs = [
    {
      question: "How does the AI plan my trip?",
      answer: "Our AI travel agent acts as your personal concierge. You chat with it about your vibe, budget, and dates. Once it understands what you're looking for, it scans thousands of flights and hotels to build a personalized day-by-day itinerary."
    },
    {
      question: "Why did the price of my flight or hotel change?",
      answer: "We use live data to give you the best recommendations. However, airline and hotel prices fluctuate constantly based on availability. The price you see in your final itinerary is a highly accurate estimate, but the final cost is determined by the booking provider when you click 'View Offer'."
    },
    {
      question: "Can I edit the itinerary the AI made for me?",
      answer: "Absolutely! The AI provides a baseline, but you are in full control. On the itinerary screen, you can drag and drop activities, swap out hotels, or add your own custom plans to any given day."
    },
    {
      question: "How do I share my trip with friends?",
      answer: "Once you are happy with your itinerary, look for the 'Export' button. You can generate a beautifully formatted PDF, download it to your calendar, or share a read-only web link directly with your travel buddies."
    },
    {
      question: "Are my passport and payment details safe?",
      answer: "We do not process payments or store sensitive booking data directly. When you are ready to book, we hand you off securely to trusted providers (like airlines or official hotel booking systems) to complete your transaction safely."
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">How can we help?</h1>
          <p className="text-lg text-gray-600">
            Everything you need to know about planning your next getaway with VacationAgent.
          </p>
        </div>

        {/* FAQ List */}
        <div className="space-y-6">
          {faqs.map((faq, index) => (
            <div key={index} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <h3 className="text-xl font-bold text-gray-900 mb-3 flex items-start gap-3">
                <span className="text-blue-500 text-2xl leading-none">Q.</span>
                {faq.question}
              </h3>
              <div className="text-gray-600 leading-relaxed ml-8">
                <span className="font-semibold text-gray-400 mr-2">A.</span>
                {faq.answer}
              </div>
            </div>
          ))}
        </div>

        {/* Still need help? */}
        <div className="mt-12 bg-blue-600 rounded-2xl p-8 text-center text-white shadow-lg">
          <h2 className="text-2xl font-bold mb-4">Still have questions?</h2>
          <p className="text-blue-100 mb-6 max-w-lg mx-auto">
            If you hit a snag or the AI is acting a little jet-lagged, let us know! We are constantly improving our systems.
          </p>
          <button className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors shadow-sm">
            Contact Support
          </button>
        </div>

        <div className="mt-8 text-center">
          <Link to="/" className="text-blue-600 hover:underline font-medium">
            &larr; Back to Dashboard
          </Link>
        </div>

      </div>
    </div>
  );
}