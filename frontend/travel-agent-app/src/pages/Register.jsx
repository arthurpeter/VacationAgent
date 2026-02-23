import React, { useState } from "react";
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const [form, setForm] = useState({ email: "", password: "", confirm_password: "" });

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    
    // Frontend password validation
    if (form.password !== form.confirm_password) {
      toast.error("Passwords do not match!");
      return;
    }
    
    try {
      const res = await fetch("http://localhost:5000/auth/register", {
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
          className="w-full px-4 py-3 mb-6 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
        />
        <button className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 shadow-lg transition">
          Sign Up
        </button>
        <p className="mt-6 text-center text-gray-500 text-sm">
          Already have an account? <a href="/login" className="text-blue-600 hover:underline">Login</a>
        </p>
      </form>
    </div>
  );
}
