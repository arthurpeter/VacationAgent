import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-100 mt-auto">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
        
        {/* Brand / Copyright */}
        <div className="flex flex-col items-center md:items-start text-sm text-gray-500">
          <span className="font-semibold text-gray-900 mb-1">VacationAgent</span>
          <p>&copy; {currentYear} All rights reserved.</p>
        </div>

        {/* Links & Contact */}
        <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-6 text-sm font-medium text-gray-500">
          <Link to="/terms" className="hover:text-blue-600 transition">
            Terms of Service
          </Link>
          <Link to="/privacy" className="hover:text-blue-600 transition">
            Privacy Policy
          </Link>
          
          {/* A visual divider for larger screens */}
          <span className="text-gray-300 hidden md:inline">|</span>
          
          {/* Displaying the email directly as requested */}
          <span>
            Need help? Email us at <a href="mailto:contact.turag@gmail.com" className="text-blue-600 hover:underline">contact.turag@gmail.com</a>
          </span>
        </div>
        
      </div>
    </footer>
  );
}