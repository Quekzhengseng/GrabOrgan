// File: components/DeliveryMapbox.js
"use client";

import React, { useState, useEffect, useRef } from "react";
import { Package, Truck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const DeliveryMapbox = ({ deliveryData }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const truckMarker = useRef(null);
  const [routePoints, setRoutePoints] = useState([]);
  const [currentPointIndex, setCurrentPointIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [driver, setDriver] = useState({
    name: deliveryData?.driverID || "John Doe",
    status: deliveryData?.status || "Delivering",
    location: { lat: 1.3402, lng: 103.9496 },
    progress: 0,
  });

  // Define fixed origin and destination coordinates
  const origin = [103.9848883, 1.3551344]; // [lng, lat] format
  const destination = [103.846336, 1.32316]; // [lng, lat] format

  // Hardcoded sample polyline for testing
  const SAMPLE_POLYLINE =
    "evdG}smyRPg@dB}AtBlCl@n@qAhAMZ_@|@Qn@E~@@d@M~CEf@K\\Ub@uBbBITAPBRlAbB@TnCfDzQlUhAtAv@fAd@~@Xz@XvAJ~@DvAEhB}@dZc@nPBlHL~DP`CZlCj@xDvAdGxAvEbGdPrGtPnBzFnBpFnCnHjDjJvFpLhAvCf@pBtCrOrBxJr@jFbIdr@Fv@~@hHzAxJ~@lG`@`EPbDD\\F~IHzAVlB`@bBbDtKvDxLR|@VtBJdCEjDK`DMz@w@tBQZG\\qCnDi@b@aG~Do@h@iQvLqAdAkAdA{@z@eDnEy@~A_A~Bw@fCWhAuAfHa@|A{@~B{BdG[pAShBEjA@z@NnA`@pBbBlGDZfBzHVhBFlBU`IU`GEdCs@~PO|CHX@b@KfG@nC@LJ~HDz@JtGX`@^L^@bNOz@dFzDa@nDR~CRjD^tCLzCoAxAgASgBg@_Cw@sBe@wAqBsBkCsAcASi@KJq@f@cA";

  // Initialize Mapbox map
  useEffect(() => {
    if (mapContainer.current) {
      const script = document.createElement("script");
      script.src =
        "https://cdnjs.cloudflare.com/ajax/libs/mapbox-gl/2.15.0/mapbox-gl.js";
      script.async = true;

      script.onload = () => {
        const mapboxgl = window.mapboxgl;
        mapboxgl.accessToken =
          "pk.eyJ1IjoicXVla2t5eiIsImEiOiJjbTdzemJqcTEwdG9mMmxvaWw4b2Y3YWZiIn0.pX3y1okQlBpQM0lPHYoMjg";

        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: "mapbox://styles/mapbox/streets-v12",
          zoom: 12,
          center: origin, // Center on origin
        });

        map.current.on("load", () => {
          initializeMap();
        });
      };

      document.head.appendChild(script);

      // Add CSS for Mapbox
      const cssLink = document.createElement("link");
      cssLink.href =
        "https://cdnjs.cloudflare.com/ajax/libs/mapbox-gl/2.15.0/mapbox-gl.css";
      cssLink.rel = "stylesheet";
      document.head.appendChild(cssLink);

      return () => {
        if (map.current) {
          map.current.remove();
        }
        if (document.head.contains(script)) {
          document.head.removeChild(script);
        }
        if (document.head.contains(cssLink)) {
          document.head.removeChild(cssLink);
        }
      };
    }
  }, []);

  // Initialize the map with markers and route
  const initializeMap = async () => {
    try {
      setLoading(true);

      // Add origin and destination markers
      if (window.mapboxgl) {
        // Origin marker (green)
        new window.mapboxgl.Marker({ color: "#00bb00" })
          .setLngLat(origin)
          .addTo(map.current);

        // Destination marker (red)
        new window.mapboxgl.Marker({ color: "#ff0000" })
          .setLngLat(destination)
          .addTo(map.current);
      }

      // Set bounds to show both markers
      const bounds = new window.mapboxgl.LngLatBounds()
        .extend(origin)
        .extend(destination);

      map.current.fitBounds(bounds, { padding: 100 });

      // Decode the polyline and add the route
      try {
        const response = await fetch("http://localhost:5006/decode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            polyline: deliveryData?.polyline || SAMPLE_POLYLINE,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to decode polyline");
        }

        const data = await response.json();

        if (data.coordinates && data.coordinates.length > 0) {
          // Convert coordinates to the format Mapbox expects: [lng, lat]
          const coordinates = data.coordinates
            .map((coord) => {
              // Handle different possible formats
              if (Array.isArray(coord)) {
                // Convert array format to object
                const obj = {};
                coord.forEach((pair) => {
                  if (Array.isArray(pair) && pair.length === 2) {
                    obj[pair[0]] = pair[1];
                  }
                });
                return [obj.lng, obj.lat];
              } else if (coord && typeof coord === "object") {
                // Object format with lng/lat properties
                return [coord.lng, coord.lat];
              }
              return null;
            })
            .filter((coord) => coord !== null);

          setRoutePoints(coordinates);

          // Add the route line to the map
          map.current.addSource("route", {
            type: "geojson",
            data: {
              type: "Feature",
              properties: {},
              geometry: {
                type: "LineString",
                coordinates: coordinates,
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

          // Create and add truck marker
          if (coordinates.length > 0) {
            const el = document.createElement("div");
            el.className = "flex items-center justify-center";
            el.innerHTML = `
              <div class="bg-blue-500 p-2 rounded-full">
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
              .setLngLat(coordinates[0])
              .addTo(map.current);

            // Start animating the truck
            startTruckAnimation(coordinates);
          }
        }
      } catch (err) {
        console.error("Error loading route:", err);
        setError(`Failed to load route: ${err.message}`);
      }
    } catch (err) {
      setError(`Map initialization error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Animate the truck along the route
  const startTruckAnimation = (coordinates) => {
    if (!coordinates || coordinates.length < 2 || !truckMarker.current) return;

    let i = 0;
    const timer = setInterval(() => {
      if (i >= coordinates.length - 1) {
        clearInterval(timer);
        return;
      }

      i++;
      const coord = coordinates[i];

      try {
        // Update truck position
        truckMarker.current.setLngLat(coord);

        // Update driver info
        setDriver((prev) => ({
          ...prev,
          location: {
            lng: coord[0],
            lat: coord[1],
          },
          progress: Math.floor((i / (coordinates.length - 1)) * 100),
        }));

        // Update current point index for any components that need it
        setCurrentPointIndex(i);
      } catch (err) {
        console.error("Error moving truck:", err);
      }
    }, 1000);
  };

  return (
    <div className="w-full h-full shadow-md rounded-lg overflow-hidden">
      <Card className="h-full">
        <CardHeader className="bg-green-600 text-white">
          <CardTitle className="flex items-center gap-2">
            <Truck className="w-6 h-6" />
            Live Delivery Tracking
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-0">
            {/* Mapbox container */}
            <div className="col-span-2 h-[28rem] relative">
              <div ref={mapContainer} className="w-full h-full" />

              {/* Loading overlay */}
              {loading && (
                <div className="absolute inset-0 bg-gray-100 bg-opacity-70 flex items-center justify-center">
                  <div className="text-lg font-semibold">Loading route...</div>
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
                  <h3 className="font-semibold mb-2 text-green-700">
                    Driver Status
                  </h3>
                  <div className="space-y-2">
                    <p className="text-sm">Driver: {driver.name}</p>
                    <p className="text-sm">Status: {driver.status}</p>
                    <p className="text-sm">
                      Location: {driver.location.lat.toFixed(4)},{" "}
                      {driver.location.lng.toFixed(4)}
                    </p>
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-green-600 h-2.5 rounded-full"
                          style={{ width: `${driver.progress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-right mt-1 text-gray-500">
                        {driver.progress}% complete
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-100">
                  <h3 className="font-semibold mb-2 text-green-700">
                    Route Information
                  </h3>
                  <div className="space-y-2">
                    <p className="text-sm">
                      From: {deliveryData?.pickup || "Changi Hospital"}
                    </p>
                    <p className="text-sm">
                      To:{" "}
                      {deliveryData?.destination || "Tan Tock Seng Hospital"}
                    </p>
                    <p className="text-sm">
                      Total Points: {routePoints.length}
                    </p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-100">
                  <h3 className="font-semibold mb-2 text-green-700">
                    Delivery Instructions
                  </h3>
                  <p className="text-sm">
                    Please deliver the organ package to the transplant team at
                    the emergency entrance.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DeliveryMapbox;
