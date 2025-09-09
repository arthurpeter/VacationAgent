import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="flex gap-4 p-4 bg-gray-100 shadow">
      <Link to="/" className="font-bold text-blue-600 hover:underline">Home</Link>
      <Link to="/login" className="text-blue-600 hover:underline">Login</Link>
      <Link to="/register" className="text-green-600 hover:underline">Register</Link>
      {/* Add more links as needed */}
    </nav>
  );
}