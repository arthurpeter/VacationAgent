import { useState } from 'react';
import { useLocation } from 'react-router-dom';

export default function CheckEmail() {
  const location = useLocation();
  const email = location.state?.email || "";
  const [status, setStatus] = useState("");

  const handleResend = async () => {
    setStatus("Sending...");
    try {
      const response = await fetch('http://localhost:5000/auth/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (response.ok) {
        setStatus("Verification email resent! Please check your inbox.");
      } else {
        setStatus("Failed to resend. Please try again later.");
      }
    } catch (error) {
      setStatus("Network error. Please try again.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
        <h2 className="text-2xl font-bold mb-4 text-blue-600">Check Your Email</h2>
        <p className="mb-6 text-gray-600">
          We've sent a confirmation link to <strong>{email}</strong>. 
          Please click the link to verify your account and log in.
        </p>
        
        <button 
          onClick={handleResend}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
        >
          Resend Email
        </button>
        
        {status && <p className="mt-4 text-sm text-gray-700">{status}</p>}
      </div>
    </div>
  );
}