// File: components/DeliveryMapbox.js
"use client";

import React, { useState, useEffect, useRef } from "react";
import { Truck, MapPin, Calendar, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  decodePolyline,
  checkRouteDeviation,
  requestNewRoute,
  calculateEstimatedDeliveryTime,
  addressToCoordinates,
  calculateProgressByDistance,
  trackDelivery,
} from "@/utils/routeUtils";
import next from "next";

const DeliveryMapbox = ({ deliveryId, deliveryData }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const truckMarker = useRef(null);
  const animationInterval = useRef(null);
  const [routePoints, setRoutePoints] = useState([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [currentPointIndex, setCurrentPointIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [basePolyline, setBasePolyline] = useState(
    deliveryData?.polyline || ""
  );
  const [originCoords, setOriginCoords] = useState(null);
  const [destinationCoords, setDestinationCoords] = useState(null);
  const [animationStarted, setAnimationStarted] = useState(false);
  const [animationPaused, setAnimationPaused] = useState(false);
  const [routeDeviation, setRouteDeviation] = useState(false);
  const [reachedDestination, setReachedDestination] = useState(false);
  const [driver, setDriver] = useState({
    name: deliveryData?.driverID || "Driver",
    status: deliveryData?.status || "Ready",
    location: {
      lat: deliveryData?.driverCoord?.lat || 0,
      lng: deliveryData?.driverCoord?.lng || 0,
    },
    progress: 0,
  });

  console.log("Received deliveryId:", deliveryId);
  console.log("Received deliveryData:", deliveryData);

  // Clean up resources when component unmounts
  useEffect(() => {
    return () => {
      if (animationInterval.current) {
        clearInterval(animationInterval.current);
      }
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  // Initialize origin and destination coordinates
  useEffect(() => {
    const initializeCoordinates = async () => {
      try {
        // Always convert addresses to coordinates
        if (deliveryData?.pickup && deliveryData?.destination) {
          const [pickupCoords, destCoords] = await Promise.all([
            addressToCoordinates(deliveryData.pickup),
            addressToCoordinates(deliveryData.destination),
          ]);

          if (pickupCoords && destCoords) {
            setOriginCoords([pickupCoords.lng, pickupCoords.lat]);
            setDestinationCoords([destCoords.lng, destCoords.lat]);
            console.log("Coordinates initialized:", pickupCoords, destCoords);
          } else {
            throw new Error(
              "Failed to geocode pickup or destination addresses"
            );
          }
        } else {
          throw new Error(
            "Missing pickup or destination addresses in delivery data"
          );
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

        const mapboxgl = window.mapboxgl;

        // Clear the container before initializing
        if (mapContainer.current) {
          mapContainer.current.innerHTML = "";
        }

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
        });
      } catch (err) {
        console.error("Error loading Mapbox:", err);
        setError(`Failed to load map: ${err.message}`);
        setLoading(false);
      }
    };

    loadMapbox();
  }, [originCoords, destinationCoords]);

  // First, handle coordinate initialization separately
  useEffect(() => {
    if (!deliveryData?.polyline) return;

    const initializeCoordinates = async () => {
      try {
        // Decode polyline to get route coordinates
        const coords = await decodePolyline(deliveryData.polyline);
        console.log("Coordinates decoded:", coords.length, "points");

        if (coords && coords.length > 0) {
          setRoutePoints(coords);
          setBasePolyline(deliveryData.polyline);
        } else {
          console.error("No valid coordinates decoded from polyline");
        }
      } catch (err) {
        console.error("Error decoding polyline:", err);
        setError(`Failed to decode polyline: ${err.message}`);
      }
    };

    initializeCoordinates();
  }, [deliveryData?.polyline]);

  // Then, process and display the route once coordinates and map are ready
  useEffect(() => {
    if (!mapLoaded || !map.current || routePoints.length === 0) return;

    const setupRoute = async () => {
      try {
        setLoading(true);

        console.log("Setting up route with", routePoints.length, "points");

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
        } else {
          // Update existing source
          map.current.getSource("route").setData({
            type: "Feature",
            properties: {},
            geometry: {
              type: "LineString",
              coordinates: mapboxCoords,
            },
          });
        }

        // Create truck marker if not already created
        if (!truckMarker.current) {
          // Start at origin or driver position if available
          const initialPosition = originCoords;

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
            .setLngLat(initialPosition)
            .addTo(map.current);

          // Start animation automatically
          startDelivery();
        }
      } catch (err) {
        console.error("Error setting up route:", err);
        setError(`Failed to set up route: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    setupRoute();
  }, [mapLoaded, routePoints]);

  // Start the truck animation
  const startDelivery = () => {
    if (animationStarted && !animationPaused) return;

    if (animationPaused) {
      setAnimationPaused(false);
      setDriver((prev) => ({ ...prev, status: "Delivering" }));
    } else {
      setAnimationStarted(true);
      setDriver((prev) => ({ ...prev, status: "Delivering" }));
    }

    // Clear any existing interval
    if (animationInterval.current) {
      clearInterval(animationInterval.current);
    }

    if (routePoints.length === 0) {
      console.warn("No route points available for animation");
      return;
    }

    console.log(`Starting truck animation with ${routePoints.length} points`);

    // Start animation from either the paused index (if resuming) or the current point index
    let index = animationPaused ? 0 : 0;
    console.log("index: " + index);

    animationInterval.current = setInterval(() => {
      if (index >= routePoints.length - 1) {
        clearInterval(animationInterval.current);
        setDriver((prev) => ({ ...prev, status: "Delivered" }));
        setReachedDestination(true);
        return;
      }

      index++;
      setCurrentPointIndex(index);
      const nextPoint = routePoints[index];

      // Check for deviation
      trackDelivery(deliveryId, nextPoint)
        .then((result) => {
          if (result.deviation) {
            console.log("Route deviation detected at position:", nextPoint);
            setRouteDeviation(true);

            // Request new route from current position to destination
            decodePolyline(result.polyline)
              .then((newCoords) => {
                if (newCoords && newCoords.length > 0) {
                  console.log(
                    "New route received with",
                    newCoords.length,
                    "points"
                  );

                  // Create a merged route that keeps all points traveled so far
                  // and adds the new route from the current position
                  const updatedRoute = [...newCoords];

                  // Update route state
                  setRoutePoints(updatedRoute);

                  // Update the polyline displayed on the map
                  if (
                    map.current &&
                    map.current.isStyleLoaded &&
                    map.current.isStyleLoaded()
                  ) {
                    // First check if the map style is loaded
                    try {
                      // Check if the source exists
                      const hasSource =
                        map.current.getStyle() &&
                        map.current.getStyle().sources &&
                        map.current.getStyle().sources.route;

                      if (hasSource) {
                        // Now we can safely update the source
                        map.current.getSource("route").setData({
                          type: "Feature",
                          properties: {},
                          geometry: {
                            type: "LineString",
                            coordinates: [
                              ...[[nextPoint.lng, nextPoint.lat]],
                              ...newCoords.map((coord) => [
                                coord.lng,
                                coord.lat,
                              ]),
                            ],
                          },
                        });
                      } else {
                        console.log(
                          "Route source does not exist, cannot update"
                        );
                      }
                    } catch (err) {
                      console.log("Error updating map source:", err);
                    }
                  } else {
                    console.log("Map is not fully loaded or initialized");
                  }

                  // Update base polyline for future deviation checks
                  // This requires re-encoding the coordinates back to a polyline
                  // You might need to add a utility function for this

                  // Remove deviation indicator after a short delay
                  setTimeout(() => {
                    setRouteDeviation(false);
                  }, 3000);
                }
              })
              .catch((err) => {
                console.error("Error requesting new route:", err);
                // Remove deviation indicator after a short delay even if route update fails
                setTimeout(() => {
                  setRouteDeviation(false);
                }, 3000);
              });
          } else {
            // No deviation - update the map to show only the remaining route
            // This creates the "disappearing" effect as the driver moves
            if (map.current && map.current.getSource("route")) {
              // Get just the portion of the route still ahead
              const remainingRoute = routePoints.slice(index);
              setRoutePoints(remainingRoute);

              // Update the source with just the remaining route points
              map.current.getSource("route").setData({
                type: "Feature",
                properties: {},
                geometry: {
                  type: "LineString",
                  coordinates: remainingRoute.map((coord) => [
                    coord.lng,
                    coord.lat,
                  ]),
                },
              });
            }
          }
        })
        .catch((err) => {
          console.error("Error checking for deviation:", err);
        });

      try {
        // Move truck marker to next point
        if (truckMarker.current && nextPoint) {
          console.log(
            `Moving truck to point ${index}: ${nextPoint.lat}, ${nextPoint.lng}`
          );
          truckMarker.current.setLngLat([nextPoint.lng, nextPoint.lat]);

          // Update driver info with progress based on straight-line distance
          const startPos = routePoints[0];
          const endPos = {
            lat: destinationCoords[1],
            lng: destinationCoords[0],
          };

          const distanceProgress = calculateProgressByDistance(
            nextPoint,
            startPos,
            endPos
          );

          setDriver((prev) => ({
            ...prev,
            location: nextPoint,
            progress: distanceProgress,
          }));
        }
      } catch (err) {
        console.error("Error moving truck:", err);
        clearInterval(animationInterval.current);
      }
    }, 1000);
  };

  const endDelivery = () => {
    console.log("Ending delivery...");
    // Empty function for now, will be implemented later

    // Clear any existing interval
    if (animationInterval.current) {
      clearInterval(animationInterval.current);
    }

    // Update driver status
    setDriver((prev) => ({
      ...prev,
      status: "Completed",
    }));

    // Reset animation states
    setAnimationStarted(false);
    setAnimationPaused(false);
  };

  // Pause the truck animation
  const pauseDelivery = () => {
    if (!animationStarted || animationPaused) return;

    if (animationInterval.current) {
      clearInterval(animationInterval.current);
    }

    setAnimationPaused(true);
    setDriver((prev) => ({ ...prev, status: "Paused" }));
  };

  // Reset the truck animation
  const resetDelivery = () => {
    if (animationInterval.current) {
      clearInterval(animationInterval.current);
    }

    setCurrentPointIndex(0);
    setAnimationStarted(false);
    setAnimationPaused(false);
    setDriver((prev) => ({
      ...prev,
      status: "Ready",
      progress: 0,
    }));

    // Reset truck marker position to start of route
    if (truckMarker.current && routePoints.length > 0) {
      truckMarker.current.setLngLat([routePoints[0].lng, routePoints[0].lat]);
    }
  };

  // Calculate estimated delivery time
  const getEstimatedTime = () => {
    return deliveryData.destination_time;
  };

  return (
    <div className="w-full h-full shadow-md rounded-lg overflow-hidden">
      <Card className="h-full ">
        <CardHeader className="bg-green-600 text-white py-3">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Truck className="w-6 h-6" />
              Live Delivery Tracking
            </div>
            <div className="flex items-center gap-2">
              {reachedDestination ? (
                <button
                  onClick={endDelivery}
                  className="px-3 py-1 bg-white text-red-600 rounded-md hover:bg-gray-100 flex items-center gap-1"
                >
                  End Delivery
                </button>
              ) : !animationStarted || animationPaused ? (
                <button
                  onClick={startDelivery}
                  className="px-3 py-1 bg-white text-green-600 rounded-md hover:bg-gray-100 flex items-center gap-1"
                  disabled={loading || routePoints.length === 0}
                >
                  {animationPaused ? "Resume" : "Start Delivery"}
                </button>
              ) : (
                <button
                  onClick={pauseDelivery}
                  className="px-3 py-1 bg-white text-yellow-600 rounded-md hover:bg-gray-100 flex items-center gap-1"
                >
                  Pause
                </button>
              )}

              <button
                onClick={resetDelivery}
                className="px-3 py-1 bg-white text-gray-600 rounded-md hover:bg-gray-100 flex items-center gap-1"
                disabled={
                  (!animationStarted && currentPointIndex === 0) ||
                  reachedDestination
                }
              >
                Reset
              </button>
            </div>
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

              {/* Route deviation indicator */}
              {routeDeviation && (
                <div className="absolute top-4 right-4 bg-red-100 text-red-800 p-2 rounded-md animate-pulse">
                  <p className="font-medium">Route deviation detected</p>
                  <p className="text-sm">Recalculating route...</p>
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
                    <div className="flex justify-between items-center">
                      <p className="text-sm">Driver: {driver.name}</p>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          driver.status === "Delivered"
                            ? "bg-green-100 text-green-800"
                            : driver.status === "Delivering"
                            ? "bg-blue-100 text-blue-800"
                            : driver.status === "Paused"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {driver.status}
                      </span>
                    </div>

                    <p className="text-sm">
                      Location: {driver.location?.lat?.toFixed(4) || "N/A"},{" "}
                      {driver.location?.lng?.toFixed(4) || "N/A"}
                    </p>
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-green-600 h-2.5 rounded-full transition-all duration-500"
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
                    <div className="flex items-start">
                      <MapPin className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">From:</p>
                        <p className="text-sm">
                          {deliveryData?.pickup || "Pickup Location"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <MapPin className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">To:</p>
                        <p className="text-sm">
                          {deliveryData?.destination || "Destination"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <Calendar className="h-4 w-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">Pickup Time:</p>
                        <p className="text-sm">
                          {deliveryData?.pickup_time || "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start">
                      <Clock className="h-4 w-4 text-purple-600 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-gray-500">
                          Estimated Arrival Time:
                        </p>
                        <p className="text-sm">
                          {routePoints.length > 0
                            ? getEstimatedTime()
                            : "Calculating..."}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-100">
                  <h3 className="font-semibold mb-2 text-green-700">
                    Delivery Instructions
                  </h3>
                  <p className="text-sm">
                    Please deliver the organ package to the transplant team at
                    the emergency entrance. Handle with extreme care.
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
