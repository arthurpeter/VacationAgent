import React, { useState } from "react";
import { setTokens } from "../authService";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    // Replace with your backend URL
    const res = await fetch("http://localhost:5000/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    // Handle response...
    if (res.ok) {
      const response = await res.json();
      setTokens(response.access_token, response.refresh_token);
      window.location.href = "/";
    } else {
      // Handle login error (e.g., show a message)
      alert("Login failed. Please check your credentials.");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>
        <input className="input mb-4" name="username" type="text" placeholder="Username" onChange={handleChange} required />
        <input className="input mb-6" name="password" type="password" placeholder="Password" onChange={handleChange} required />
        <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Sign In</button>
      </form>
    </div>
  );
}