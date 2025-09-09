import React, { useState } from "react";

export default function Register() {
  const [form, setForm] = useState({ email: "", username: "", password: "", first_name: "", last_name: "" });

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    // Replace with your backend URL
    const res = await fetch("http://localhost:5000/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    // Handle response...
    if (res.ok) {
        // Registration successful, now log the user in
        const loginRes = await fetch("http://localhost:5000/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: form.username, password: form.password }),
        });
        if (loginRes.ok) {
            const response = await loginRes.json();
            setTokens(response.access_token, response.refresh_token);
            window.location.href = "/";
        } else {
            alert("There was an error logging in after registration.");
            // redirect to login page or handle as needed
            window.location.href = "/login";
        }
    } else {
        // Handle registration error (e.g., show a message)
        alert("Registration failed. Please try again.");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Register</h2>
        <input className="input mb-2" name="email" type="email" placeholder="Email" onChange={handleChange} required />
        <input className="input mb-2" name="username" type="text" placeholder="Username" onChange={handleChange} required />
        <input className="input mb-2" name="first_name" type="text" placeholder="First Name" onChange={handleChange} required />
        <input className="input mb-2" name="last_name" type="text" placeholder="Last Name" onChange={handleChange} required />
        <input className="input mb-4" name="password" type="password" placeholder="Password" onChange={handleChange} required />
        <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Sign Up</button>
      </form>
    </div>
  );
}