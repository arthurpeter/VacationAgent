import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext.jsx';
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
    <Toaster
      position="top-center"
      toastOptions={{
        duration: 2000, // auto-dismiss after 2 seconds
        style: {
          background: '#22c55e', // green for success (can change dynamically)
          color: 'white',
          fontWeight: 'bold',
          borderRadius: '0.75rem', // rounded-xl
          padding: '1rem',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        },
      }}
    />
  </StrictMode>,
)
