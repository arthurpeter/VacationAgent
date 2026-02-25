import React from 'react';
import { Link } from 'react-router-dom';

export default function Terms() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto bg-white p-8 md:p-12 rounded-2xl shadow-sm border border-gray-100">
        
        <h1 className="text-3xl font-extrabold text-gray-900 mb-6">Terms of Service & Privacy Policy</h1>
        <p className="text-sm text-gray-500 mb-8">Last updated: October 2023</p>

        <div className="prose prose-blue max-w-none text-gray-600 space-y-6">
          
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">1. Acceptance of Terms</h2>
            <p>
              By accessing and using VacationAgent ("we", "our", or "us"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our application.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">2. AI-Generated Itineraries & Pricing</h2>
            <p>
              VacationAgent utilizes artificial intelligence and third-party APIs (such as search engine aggregators) to recommend flights, accommodations, and activities. 
              <strong> Please note:</strong> The prices and availability displayed during the planning process are estimates based on live and cached data. We do not guarantee the final price or availability of any travel service. Final prices are determined by the respective booking providers.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">3. Booking and Third-Party Links</h2>
            <p>
              We are a travel planning tool, not a travel agency. We do not directly process bookings or payments for flights, hotels, or activities. When you click to view or book an offer, you will be redirected to third-party affiliate partners or providers. We are not responsible for the terms, conditions, or privacy policies of those third-party sites.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">4. Privacy & Data Collection</h2>
            <p>
              To provide a personalized experience, we store user session data, saved trips, and travel preferences in our database. We will never sell your personal data. By creating an account, you consent to the storage of this data to improve your AI recommendations. 
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">5. User Conduct</h2>
            <p>
              You agree to use the AI chat interfaces responsibly and not to attempt to bypass, exploit, or inject malicious prompts into the agent infrastructure.
            </p>
          </section>

        </div>

        <div className="mt-12 pt-8 border-t border-gray-100 text-center">
          <Link 
            to="/" 
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            I Understand, Return to App
          </Link>
        </div>

      </div>
    </div>
  );
}