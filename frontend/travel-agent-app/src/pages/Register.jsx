import React, { useState } from "react";
import toast, { Toaster } from 'react-hot-toast';
import { Link, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';

export default function Register() {
  const [form, setForm] = useState({ email: "", password: "", confirm_password: "" });
  
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    
    if (form.password !== form.confirm_password) {
      toast.error("Passwords do not match!");
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (res.ok) {
        toast.success('Registration successful! Please check your email.');
        
        setTimeout(() => {
          navigate("/check-email");
        }, 1500);
      } else {
        const errorData = await res.json();
        toast.error(errorData.detail || "Registration failed. Please try again.");
      }
    } catch (error) {
      toast.error("Network error. Could not reach the server.");
    }
  };

  return (
    <div className="relative flex items-center justify-center min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <Toaster position="top-center" reverseOrder={false} />

      <form onSubmit={handleSubmit} className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-md relative z-0">
        <h2 className="text-3xl font-extrabold mb-8 text-center text-blue-600">Register</h2>

        <input
          name="email"
          type="email"
          placeholder="Email"
          onChange={handleChange}
          required
          className="w-full px-4 py-3 mb-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
        />
        <input
          name="password"
          type="password"
          placeholder="Password"
          onChange={handleChange}
          required
          className="w-full px-4 py-3 mb-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
        />
        <input
          name="confirm_password"
          type="password"
          placeholder="Confirm Password"
          onChange={handleChange}
          required
          className="w-full px-4 py-3 mb-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
        />

        <div className="flex items-start mb-6">
          <div className="flex items-center h-5">
            <input
              id="terms"
              type="checkbox"
              required
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="w-4 h-4 border border-gray-300 rounded bg-gray-50 focus:ring-3 focus:ring-blue-300 cursor-pointer accent-blue-600"
            />
          </div>
          <label htmlFor="terms" className="ml-2 text-sm font-medium text-gray-600 text-left">
            I agree to the{' '}
            <Link to="/terms" className="text-blue-600 hover:underline hover:text-blue-700">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" className="text-blue-600 hover:underline hover:text-blue-700">
              Privacy Policy
            </Link>.
          </label>
        </div>

        <button 
          type="submit" 
          disabled={!agreedToTerms}
          className={`w-full py-3 rounded-xl font-semibold shadow-lg transition-all duration-200 
            ${!agreedToTerms 
              ? 'bg-blue-400 text-white opacity-70 cursor-not-allowed' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
        >
          Sign Up
        </button>

        <p className="mt-6 text-center text-gray-500 text-sm">
          Already have an account? <Link to="/login" className="text-blue-600 hover:underline">Login</Link>
        </p>
      </form>
    </div>
  );
}