"use client";

import React, { useState, useEffect, useRef } from "react";
import { Clock, MapPin, Calendar, Heart } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  decodePolyline,
  getSpecificDelivery,
  addressToCoordinates,
  calculateProgressByDistance,
} from "@/utils/routeUtils";

const DoctorDeliveryTracker = ({ deliveryId }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const truckMarker = useRef(null);
  const pollingInterval = useRef(null);

  const [deliveryData, setDeliveryData] = useState(null);
  const [routePoints, setRoutePoints] = useState([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [originCoords, setOriginCoords] = useState(null);
  const [destinationCoords, setDestinationCoords] = useState(null);
  const [driverLocation, setDriverLocation] = useState(null);
  const [progress, setProgress] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [estimatedArrival, setEstimatedArrival] = useState(null);
  const [organType, setOrganType] = useState("Organ");

  // Clean up resources when component unmounts
  useEffect(() => {
    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  // Start polling for delivery data
  useEffect(() => {
    if (!deliveryId) return;

    // Initial fetch
    fetchDeliveryData();

    // Set up polling every 30 seconds
    pollingInterval.current = setInterval(fetchDeliveryData, 30000);

    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, [deliveryId]);

  // Fetch delivery data
  const fetchDeliveryData = async () => {
    if (!deliveryId) return;

    try {
      console.log("Fetching delivery data for ID:", deliveryId);
      const data = await getSpecificDelivery(deliveryId);
      console.log("Received delivery data:", data);

      setDeliveryData(data);
      setOrganType(data.organType || "Organ");
      setEstimatedArrival(data.destination_time || "N/A");
      setLastUpdated(new Date().toLocaleTimeString());

      // Update driver location if available
      if (data.driverCoord) {
        setDriverLocation(data.driverCoord);
      }

      // Decode polyline if it exists and we don't have route points yet
      if (data.polyline && routePoints.length === 0) {
        const coords = await decodePolyline(data.polyline);
        if (coords && coords.length > 0) {
          setRoutePoints(coords);
        }
      }
    } catch (err) {
      console.error("Error fetching delivery data:", err);
      setError(`Failed to fetch delivery data: ${err.message}`);
    }
  };

  // Initialize origin and destination coordinates when delivery data is loaded
  useEffect(() => {
    if (!deliveryData?.pickup || !deliveryData?.destination) return;

    const initializeCoordinates = async () => {
      try {
        // Always convert addresses to coordinates
        const [pickupCoords, destCoords] = await Promise.all([
          addressToCoordinates(deliveryData.pickup),
          addressToCoordinates(deliveryData.destination),
        ]);

        if (pickupCoords && destCoords) {
          setOriginCoords([pickupCoords.lng, pickupCoords.lat]);
          setDestinationCoords([destCoords.lng, destCoords.lat]);
          console.log("Coordinates initialized:", pickupCoords, destCoords);
        } else {
          throw new Error("Failed to geocode pickup or destination addresses");
        }
      } catch (err) {
        console.error("Error initializing coordinates:", err);
        setError(`Failed to initialize coordinates: ${err.message}`);
      }
    };

    initializeCoordinates();
  }, [deliveryData?.pickup, deliveryData?.destination]);

  // Initialize Mapbox map when coordinates are ready
  useEffect(() => {
    if (
      !mapContainer.current ||
      !originCoords ||
      !destinationCoords ||
      map.current
    )
      return;

    const loadMapbox = async () => {
      try {
        setLoading(true);

        // Load Mapbox script dynamically
        if (!window.mapboxgl) {
          await new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src =
              "https://cdnjs.cloudflare.com/ajax/libs/mapbox-gl/2.15.0/mapbox-gl.js";
            script.async = true;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);

            const cssLink = document.createElement("link");
            cssLink.href =
              "https://cdnjs.cloudflare.com/ajax/libs/mapbox-gl/2.15.0/mapbox-gl.css";
            cssLink.rel = "stylesheet";
            document.head.appendChild(cssLink);
          });
        }

        // Clear the container before initializing
        if (mapContainer.current) {
          mapContainer.current.innerHTML = "";
        }

        const mapboxgl = window.mapboxgl;

        mapboxgl.accessToken =
          "pk.eyJ1IjoicXVla2t5eiIsImEiOiJjbTdzemJqcTEwdG9mMmxvaWw4b2Y3YWZiIn0.pX3y1okQlBpQM0lPHYoMjg";

        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: "mapbox://styles/mapbox/streets-v12",
          zoom: 12,
          center: originCoords,
        });

        map.current.on("load", () => {
          setMapLoaded(true);
          setLoading(false);
        });
      } catch (err) {
        console.error("Error loading Mapbox:", err);
        setError(`Failed to load map: ${err.message}`);
        setLoading(false);
      }
    };

    loadMapbox();
  }, [originCoords, destinationCoords]);

  // Setup route and markers when map is loaded and route points are available
  useEffect(() => {
    if (
      !mapLoaded ||
      !map.current ||
      routePoints.length === 0 ||
      !originCoords ||
      !destinationCoords
    )
      return;

    const setupRoute = async () => {
      try {
        // Convert to mapbox format ([lng, lat]) for map display
        const mapboxCoords = routePoints.map((coord) => [coord.lng, coord.lat]);

        // Add origin and destination markers
        new window.mapboxgl.Marker({ color: "#00bb00" })
          .setLngLat(originCoords)
          .addTo(map.current);

        new window.mapboxgl.Marker({ color: "#ff0000" })
          .setLngLat(destinationCoords)
          .addTo(map.current);

        // Add route to map
        if (!map.current.getSource("route")) {
          map.current.addSource("route", {
            type: "geojson",
            data: {
              type: "Feature",
              properties: {},
              geometry: {
                type: "LineString",
                coordinates: mapboxCoords,
              },
            },
          });

          map.current.addLayer({
            id: "route",
            type: "line",
            source: "route",
            layout: {
              "line-join": "round",
              "line-cap": "round",
            },
            paint: {
              "line-color": "#3887be",
              "line-width": 5,
              "line-opacity": 0.75,
            },
          });
        }

        // Fit map to show the entire route
        const bounds = new window.mapboxgl.LngLatBounds();
        mapboxCoords.forEach((coord) => bounds.extend(coord));
        map.current.fitBounds(bounds, { padding: 50 });
      } catch (err) {
        console.error("Error setting up route:", err);
        setError(`Failed to set up route: ${err.message}`);
      }
    };

    setupRoute();
  }, [mapLoaded, routePoints, originCoords, destinationCoords]);

  // Update truck marker when driver location changes
  useEffect(() => {
    if (!mapLoaded || !map.current || !driverLocation) return;

    try {
      // Create or update truck marker
      if (!truckMarker.current) {
        const el = document.createElement("div");
        el.className = "truck-marker";
        el.innerHTML = `
          <div style="background-color: #3b82f6; padding: 8px; border-radius: 9999px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
          </div>
        `;

        truckMarker.current = new window.mapboxgl.Marker({
          element: el,
          anchor: "bottom",
        })
          .setLngLat([driverLocation.lng, driverLocation.lat])
          .addTo(map.current);

        // Center the map on the driver's location
        map.current.flyTo({
          center: [driverLocation.lng, driverLocation.lat],
          zoom: 14,
          speed: 1.5,
        });
      } else {
        truckMarker.current.setLngLat([driverLocation.lng, driverLocation.lat]);
      }

      // Calculate progress if we have all the necessary data
      if (routePoints.length > 0 && originCoords && destinationCoords) {
        const startPos = { lat: originCoords[1], lng: originCoords[0] };
        const endPos = { lat: destinationCoords[1], lng: destinationCoords[0] };

        const currentProgress = calculateProgressByDistance(
          driverLocation,
          startPos,
          endPos
        );

        setProgress(currentProgress);
      }
    } catch (err) {
      console.error("Error updating truck marker:", err);
    }
  }, [driverLocation, mapLoaded, routePoints, originCoords, destinationCoords]);

  // Format date/time for display
  const formatTime = (timeString) => {
    if (!timeString) return "N/A";

    // Handle format like "20250315 11:45:00 AM"
    try {
      const year = timeString.substring(0, 4);
      const month = timeString.substring(4, 6);
      const day = timeString.substring(6, 8);
      const time = timeString.substring(9);

      return `${day}/${month}/${year} ${time}`;
    } catch (err) {
      return timeString;
    }
  };

  return (
    <div className="w-full shadow-md rounded-lg overflow-hidden">
      <Card className="h-full">
        <CardHeader className="bg-blue-600 text-white py-3">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Heart className="w-6 h-6" />
              {organType} Delivery Tracker
            </div>
            <div className="text-sm">Last updated: {lastUpdated || "N/A"}</div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-0">
            {/* Mapbox container */}
            <div className="col-span-2 h-[28rem] relative ml-4">
              <div ref={mapContainer} className="w-full h-full" />

              {/* Loading overlay */}
              {loading && (
                <div className="absolute inset-0 bg-gray-100 bg-opacity-70 flex items-center justify-center">
                  <div className="text-lg font-semibold">
                    Loading tracker...
                  </div>
                </div>
              )}

              {/* Error message */}
              {error && (
                <div className="absolute bottom-4 left-4 right-4 bg-red-100 text-red-800 p-2 rounded-md">
                  {error}
                </div>
              )}
            </div>

            {/* Status panel */}
            <div className="p-4 border-l border-gray-200">
              <div className="space-y-4">
                <div className="bg-white p-4 rounded-lg border border-gray-100">
                  <h3 className="font-semibold mb-2 text-blue-700">
                    Delivery Status
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <p className="text-sm">
                        Status: {deliveryData?.status || "Unknown"}
                      </p>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          deliveryData?.status === "Delivered"
                            ? "bg-green-100 text-green-800"
                            : deliveryData?.status === "In Transit"
                            ? "bg-blue-100 text-blue-800"
                            : deliveryData?.status === "Assigned"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {deliveryData?.status || "Unknown"}
                      </span>
                    </div>

                    <p className="text-sm">
                      Order ID: {deliveryData?.orderID || "N/A"}
                    </p>

                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-right mt-1 text-gray-500">
                        {progress}% of journey complete
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-100">
                  <h3 className="font-semibold mb-2 text-blue-700">
                    {organType} Information
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-start">
                      <MapPin className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">Source:</p>
                        <p className="text-sm">
                          {deliveryData?.pickup || "Source Hospital"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <MapPin className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">Destination:</p>
                        <p className="text-sm">
                          {deliveryData?.destination || "Destination Hospital"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <Calendar className="h-4 w-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">Pickup Time:</p>
                        <p className="text-sm">
                          {formatTime(deliveryData?.pickup_time) || "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <Clock className="h-4 w-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">
                          Estimated Arrival:
                        </p>
                        <p className="text-sm">
                          {formatTime(estimatedArrival) || "Calculating..."}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DoctorDeliveryTracker;
