// File: app/page.js
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function LoginPage() {
  const router = useRouter();
  const [userType, setUserType] = useState("doctor");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    // Simulate login process
    setTimeout(() => {
      setIsLoading(false);

      // Redirect based on user type (for demo purposes)
      if (userType === "doctor") {
        router.push("/doctor");
      } else {
        router.push(`/delivery?id=${email}`);
      }
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center">
      <div className="max-w-md w-full mx-auto">
        <div className="text-center mb-6">
          {/* Logo placeholder - replace with your actual logo */}
          <div className="flex justify-center mb-2">
            <div className="relative w-16 h-16 bg-green-600 rounded-full flex items-center justify-center">
              <span className="text-white text-2xl font-bold">GO</span>
            </div>
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900">GrabOrgan</h1>
          <p className="text-green-600 font-medium">
            Efficient organ delivery system
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg px-8 py-10 mb-4">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-center text-gray-800 mb-5">
              Login to your account
            </h2>

            {/* User type toggle */}
            <div className="flex justify-center mb-6">
              <div className="bg-gray-100 p-1 rounded-lg flex w-full max-w-xs">
                <button
                  onClick={() => setUserType("doctor")}
                  className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
                    userType === "doctor"
                      ? "bg-green-600 text-white"
                      : "text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Doctor
                </button>
                <button
                  onClick={() => setUserType("driver")}
                  className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
                    userType === "driver"
                      ? "bg-green-600 text-white"
                      : "text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Driver
                </button>
              </div>
            </div>

            {/* Login form */}
            <form onSubmit={handleLogin}>
              <div className="mb-4">
                <label
                  className="block text-gray-700 text-sm font-medium mb-2"
                  htmlFor="email"
                >
                  Login ID
                </label>
                <input
                  id="email"
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="1234"
                />
              </div>

              <div className="mb-6">
                <label
                  className="block text-gray-700 text-sm font-medium mb-2"
                  htmlFor="password"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Logging in...
                  </span>
                ) : (
                  `Login as ${userType === "doctor" ? "Doctor" : "Driver"}`
                )}
              </button>
            </form>
          </div>

          <div className="flex items-center justify-between">
            <a href="#" className="text-sm text-green-600 hover:text-green-800">
              Forgot password?
            </a>
            <a href="#" className="text-sm text-green-600 hover:text-green-800">
              Create account
            </a>
          </div>
        </div>

        <p className="text-center text-sm text-gray-600">
          GrabOrgan &copy; {new Date().getFullYear()} - Saving lives through
          efficient delivery
        </p>
      </div>
    </div>
  );
}
