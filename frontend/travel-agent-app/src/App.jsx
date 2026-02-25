import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
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

import './App.css'

// function App() {
//   return (
//     <BrowserRouter>
//       <Navbar />
//       <Routes>
//         <Route path="/" element={<Home />} />
//         <Route path="/login" element={<Login />} />
//         <Route path="/register" element={<Register />} />
//         <Route path="/check-email" element={<CheckEmail />} />
//         <Route path="/verify-email" element={<VerifyEmail />} />
//         <Route path="/plan/:id" element={<VacationLayout />}>
//           <Route index element={<Navigate to="discovery" replace />} />
//           <Route path="discovery" element={<DiscoveryStage />} />
//           <Route path="options" element={<OptionsStage />} />
//           <Route path="itinerary" element={<ItineraryStage />} />
//         </Route>
//         <Route path="*" element={<NotFound />} />
//       </Routes>
//     </BrowserRouter>
//   );
// }

// export default App

function AppContent() {
  const location = useLocation();

  // 3. Check if the current route is part of the VacationLayout
  // Since all your planning routes start with "/plan", we can just check that
  const isVacationLayout = location.pathname.startsWith('/plan');

  return (
    // 4. Flex column with min-h-screen ensures the footer is pushed to the bottom
    <div className="flex flex-col min-h-screen">
      
      <Navbar />
      
      {/* flex-grow allows the main content to expand and push the footer down */}
      <main className="flex-grow flex flex-col">
        <Routes>
          {/* Main Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/check-email" element={<CheckEmail />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          
          {/* New Static Routes */}
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/help" element={<FAQ />} />

          {/* Vacation Layout Routes */}
          <Route path="/plan/:id" element={<VacationLayout />}>
            <Route index element={<Navigate to="discovery" replace />} />
            <Route path="discovery" element={<DiscoveryStage />} />
            <Route path="options" element={<OptionsStage />} />
            <Route path="itinerary" element={<ItineraryStage />} />
          </Route>
          
          {/* 404 Route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      {/* 5. Conditionally render the Footer ONLY if not in the VacationLayout */}
      {!isVacationLayout && <Footer />}
      
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
