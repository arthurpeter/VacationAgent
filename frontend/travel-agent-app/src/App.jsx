import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Navbar from "./components/Navbar";
import VacationLayout from "./layouts/VacationLayout";
import DiscoveryStage from "./pages/stages/DiscoveryStage";
import OptionsStage from "./pages/stages/OptionsStage";
import ItineraryStage from "./pages/stages/ItineraryStage";
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/plan/:id" element={<VacationLayout />}>
          <Route index element={<Navigate to="discovery" replace />} />
          <Route path="discovery" element={<DiscoveryStage />} />
          <Route path="options" element={<OptionsStage />} />
          <Route path="itinerary" element={<ItineraryStage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App
