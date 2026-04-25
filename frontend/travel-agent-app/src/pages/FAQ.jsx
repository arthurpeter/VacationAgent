import React from 'react';
import { Link } from 'react-router-dom';
import PageTransition from '../components/PageTransition';

export default function FAQ() {
  const faqs = [
    {
      question: "[Placeholder Question 1?]",
      answer: "[This is a placeholder answer. It will contain a brief explanation of the feature or policy in question to help the user.]"
    },
    {
      question: "[Placeholder Question 2?]",
      answer: "[This is a placeholder answer. It will contain a brief explanation of the feature or policy in question to help the user.]"
    },
    {
      question: "[Placeholder Question 3?]",
      answer: "[This is a placeholder answer. It will contain a brief explanation of the feature or policy in question to help the user.]"
    }
  ];

  return (
    <PageTransition className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">

        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">How can we help?</h1>
          <p className="text-lg text-gray-600">
            Everything you need to know about planning your next getaway with TuRAG.
          </p>
        </div>

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
    </PageTransition>
  );
}