import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Home from "./pages/Home";
import CheckEmail from "./pages/CheckEmail";
import VerifyEmail from "./pages/VerifyEmail";
import Navbar from "./components/Navbar";
import VacationLayout from "./layouts/VacationLayout";
import DiscoveryStage from "./pages/stages/DiscoveryStage";
import OptionsStage from "./pages/stages/OptionsStage";
import ItineraryStage from "./pages/stages/ItineraryStage";
import NotFound from './pages/NotFound';
import Footer from "./components/Footer";
import Terms from "./pages/Terms";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import FAQ from "./pages/FAQ";
import Profile from "./pages/Profile";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import ScrollToTop from "./components/ScrollToTop";

import './App.css'

function AppContent() {
  const location = useLocation();

  const isVacationLayout = location.pathname.startsWith('/plan');
  const routeKey = isVacationLayout ? "/plan" : location.pathname;

  return (
    <div className="flex flex-col min-h-screen">
      
      <Navbar />
      
      <main className="flex-grow flex flex-col">
        <AnimatePresence mode="wait">
          <Routes location={location} key={routeKey}>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/check-email" element={<CheckEmail />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/help" element={<FAQ />} />
            <Route path="/profile" element={<Profile />} />

            <Route path="/plan/:id" element={<VacationLayout />}>
              <Route index element={<Navigate to="discovery" replace />} />
              <Route path="discovery" element={<DiscoveryStage />} />
              <Route path="options" element={<OptionsStage />} />
              <Route path="itinerary" element={<ItineraryStage />} />
            </Route>
            
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AnimatePresence>
      </main>

      {!isVacationLayout && <Footer />}
      
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <AppContent />
    </BrowserRouter>
  );
}

export default App;