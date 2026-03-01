import React, { useState } from "react";
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import { API_BASE_URL } from '../config';

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const auth = useAuth();
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", 
        body: JSON.stringify(form),
      });

      if (res.ok) {
        toast.success("Login successful!");
        const response = await res.json();
        
        setTimeout(() => {
          auth.login(response.access_token);
          navigate('/');
        }, 1200); 
      } else {
        const errorData = await res.json();
        toast.error(errorData.detail || "Login failed. Please check your credentials.");
      }
    } catch (err) {
      toast.error("Network error. Could not reach the server.");
    }
  };

  return (
    <div className="relative flex items-center justify-center min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <Toaster position="top-center" reverseOrder={false} />
      <form onSubmit={handleSubmit} className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-md">
        <h2 className="text-3xl font-extrabold mb-8 text-center text-blue-600">Login</h2>
        <input
          name="email"
          type="email"
          placeholder="Email"
          onChange={handleChange}
          required
          className="w-full px-4 py-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
        />
        <input
          name="password"
          type="password"
          placeholder="Password"
          onChange={handleChange}
          required
          className="w-full px-4 py-3 mb-6 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
        />
        <button className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 shadow-lg transition">
          Sign In
        </button>
        <div className="mt-6 flex flex-col items-center space-y-3 text-sm">
          <Link 
            to="/forgot-password" 
            className="text-blue-600 font-medium hover:text-blue-800 hover:underline transition"
          >
            Forgot your password?
          </Link>
          
          <p className="text-gray-500">
            Don't have an account?{' '}
            <Link 
              to="/register" 
              className="text-blue-600 font-medium hover:text-blue-800 hover:underline transition"
            >
              Register
            </Link>
          </p>
        </div>
      </form>
    </div>
  );
}
