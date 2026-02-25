import React from 'react';
import { Link } from 'react-router-dom';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto bg-white p-8 md:p-12 rounded-2xl shadow-sm border border-gray-100">
        
        <h1 className="text-3xl font-extrabold text-gray-900 mb-6">Privacy Policy</h1>
        <p className="text-sm text-gray-500 mb-8">Last updated: February 2026</p>

        <div className="prose prose-blue max-w-none text-gray-600 space-y-6">
          
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">1. Introduction</h2>
            <p>
              Welcome to VacationAgent. We respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, and safeguard your information when you use our AI-powered travel planning application.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">2. Information We Collect</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong>Account Information:</strong> When you register, we collect your email address and authentication credentials.</li>
              <li><strong>Travel Preferences:</strong> We store the information you provide during the AI Discovery chat, including your preferred vibe, budget, travel dates, and home airport.</li>
              <li><strong>Itinerary Data:</strong> We save your generated day-by-day itineraries and saved trips so you can access them later.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">3. How We Use Your Information</h2>
            <p>
              The primary purpose of collecting your data is to provide a highly personalized travel planning experience. We use your preferences to guide our AI agent in suggesting the most relevant flights, accommodations, and activities. We also cache certain search queries to improve app performance and reduce API load times.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">4. Third-Party Services & APIs</h2>
            <p>
              To find the best travel options, your search parameters (such as destination, dates, and budget) are securely transmitted to third-party data providers (like Google Flights and Hotels via SerpAPI). <strong>We do not share your personally identifiable information (PII) with these search providers.</strong> 
            </p>
            <p className="mt-2">
              Please note that we do not process bookings directly. When you click a link to book a flight or hotel, you are navigating to a third-party platform governed by its own privacy policy.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-2">5. Data Security</h2>
            <p>
              We implement industry-standard security measures to protect your account and session data. However, no internet-based service is 100% secure. We encourage you to use a strong password and keep your login credentials confidential.
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