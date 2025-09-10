import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero Section */}
      <header className="flex flex-col items-center justify-center flex-grow text-center p-8">
        <h1 className="text-5xl font-extrabold text-gray-900 mb-4">
          Welcome to <span className="text-blue-600">Travel Agent</span>
        </h1>
        <p className="text-lg text-gray-700 max-w-2xl mb-8">
          Plan your next adventure with the help of AI. From discovering your
          perfect vibe to booking flights, hotels, and building a day-by-day
          itinerary — all in one place.
        </p>
        <Link to="/register">
          <button className="px-6 py-3 text-lg font-semibold text-white bg-blue-600 rounded-2xl shadow-lg hover:bg-blue-700 transition">
            Get Started
          </button>
        </Link>
      </header>

      {/* Flow Preview Section */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-8 max-w-6xl mx-auto">
        <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col items-center text-center hover:shadow-lg transition">
          <span className="text-3xl mb-2">💬</span>
          <h2 className="font-bold text-xl mb-2">Discovery Chat</h2>
          <p className="text-gray-600 text-sm">
            Tell us your vibe, activities, budget, and more in a friendly chat
            format.
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col items-center text-center hover:shadow-lg transition">
          <span className="text-3xl mb-2">✈️🏨</span>
          <h2 className="font-bold text-xl mb-2">Flights & Hotels</h2>
          <p className="text-gray-600 text-sm">
            Review AI-recommended flights and accommodations, all in one place.
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col items-center text-center hover:shadow-lg transition">
          <span className="text-3xl mb-2">🗓️</span>
          <h2 className="font-bold text-xl mb-2">Itinerary</h2>
          <p className="text-gray-600 text-sm">
            Get a personalized day-by-day plan with activities, tickets, and
            maps.
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col items-center text-center hover:shadow-lg transition">
          <span className="text-3xl mb-2">📂</span>
          <h2 className="font-bold text-xl mb-2">Saved Trips</h2>
          <p className="text-gray-600 text-sm">
            Sign up to save trips, revisit past plans, and share with friends.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto p-6 text-center text-gray-500 text-sm">
        © {new Date().getFullYear()} Travel Agent. All rights reserved.
      </footer>
    </div>
  );
}
