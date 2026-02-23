import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const [status, setStatus] = useState("Verifying your email...");

  useEffect(() => {
    if (!token) {
      setStatus("Invalid verification link.");
      return;
    }

    const verify = async () => {
      try {
        const response = await fetch(`http://localhost:5000/auth/verify-email?token=${token}`, {
          method: 'POST',
        });
        
        const data = await response.json();

        if (response.ok) {
          setStatus("Email verified! Redirecting to login...");
          
          setTimeout(() => navigate('/login'), 1200);
        } else {
          setStatus(data.detail || "Verification failed. The link may have expired.");
        }
      } catch (error) {
        setStatus("Network error during verification.");
      }
    };

    verify();
  }, [token, navigate]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
        <h2 className="text-2xl font-bold mb-4">Email Verification</h2>
        <p className="text-gray-700">{status}</p>
        
        {status.includes("failed") || status.includes("Invalid") ? (
          <button 
            onClick={() => navigate('/login')}
            className="mt-6 text-blue-600 hover:underline"
          >
            Go to Login
          </button>
        ) : null}
      </div>
    </div>
  );
}