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
  const [fakeRoutePoints, setfakeRoutePoints] = useState([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [currentPointIndex, setCurrentPointIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [basepolyline, setPolyline] = useState(null);
  const [driverCoord, setDriverCoord] = usestate(null);
  const [driver, setDriver] = useState({
    name: deliveryData?.driverID || "John Doe",
    status: deliveryData?.status || "Delivering",
    location: { lat: 1.3402, lng: 103.9496 },
    progress: 0,
  });

  // Define origin and destination coordinates
  // In a real app, you would get these from the deliveryData
  // But for now we'll use the ones from your original code
  const origin = { lat: 1.3551344, lng: 103.9848883 };
  const destination = { lat: 1.32316, lng: 103.846336 };

  // Get deviation from GeoAlgo API
  const getDeviation = async (polyline, drivercoord) => {
    try {
      const response = await fetch("http://localhost:5006/deviate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          polyline: polyline,
          driverCoord: drivercoord,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      console.log("Deviation Response:", data.data.deviate);

      return data.data.deviate;
    } catch (err) {
      console.log("Error is " + err);
      return false;
    }
  };

  // Get route from OutSystems API on localhost
  const fetchRoute = async (newcoord) => {
    if (newcoord == null) {
      setLoading(true);
    }
    setError(null);

    let startlat;
    let startlng;

    if (newcoord == null) {
      startlat = origin.lat;
      startlng = origin.lng;
    } else {
      startlat = newcoord.lat;
      startlng = newcoord.lng;
    }

    try {
      // Call your OutSystems API
      const response = await fetch(
        "https://zsq.outsystemscloud.com/Location/rest/Location/route",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            routingPreference: "TRAFFIC_AWARE",
            travelMode: "DRIVE",
            computeAlternativeRoutes: false,
            destination: {
              location: {
                latLng: {
                  latitude: destination.lat,
                  longitude: destination.lng,
                },
              },
            },
            origin: {
              location: {
                latLng: {
                  latitude: startlat,
                  longitude: startlng,
                },
              },
            },
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      // For the demo, if we can't access the real API, use a hardcoded polyline
      if (!data || !data.Route || !data.Route[0] || !data.Route[0].Polyline) {
        console.log("Using fallback polyline data");
        return "evdG}smyRPg@dB}AtBlCl@n@qAhAMZ_@|@Qn@E~@@d@M~CEf@K\\Ub@uBbBITAPBRlAbB@TnCfDzQlUhAtAv@fAd@~@Xz@XvAJ~@DvAEhB}@dZc@nPBlHL~DP`CZlCj@xDvAdGxAvEbGdPrGtPnBzFnBpFnCnHjDjJvFpLhAvCf@pBtCrOrBxJr@jFbIdr@Fv@~@hHzAxJ~@lG`@`EPbDD\\F~IHzAVlB`@bBbDtKvDxLR|@VtBJdCEjDK`DMz@w@tBQZG\\qCnDi@b@aG~Do@h@iQvLqAdAkAdA{@z@eDnEy@~A_A~Bw@fCWhAuAfHa@|A{@~B{BdG[pAShBEjA@z@NnA`@pBbBlGDZfBzHVhBFlBU`IU`GEdCs@~PO|CHX@b@KfG@nC@LJ~HDz@JtGX`@^L^@bNOz@dFzDa@nDR~CRjD^tCLzCoAxAgASgBg@_Cw@sBe@wAqBsBkCsAcASi@KJq@f@cA";
      }

      return data.Route[0].Polyline.encodedPolyline;
    } catch (err) {
      console.error("Error fetching route:", err);
      setError(err.message);

      // Return a fallback polyline for demo purposes
      return "evdG}smyRPg@dB}AtBlCl@n@qAhAMZ_@|@Qn@E~@@d@M~CEf@K\\Ub@uBbBITAPBRlAbB@TnCfDzQlUhAtAv@fAd@~@Xz@XvAJ~@DvAEhB}@dZc@nPBlHL~DP`CZlCj@xDvAdGxAvEbGdPrGtPnBzFnBpFnCnHjDjJvFpLhAvCf@pBtCrOrBxJr@jFbIdr@Fv@~@hHzAxJ~@lG`@`EPbDD\\F~IHzAVlB`@bBbDtKvDxLR|@VtBJdCEjDK`DMz@w@tBQZG\\qCnDi@b@aG~Do@h@iQvLqAdAkAdA{@z@eDnEy@~A_A~Bw@fCWhAuAfHa@|A{@~B{BdG[pAShBEjA@z@NnA`@pBbBlGDZfBzHVhBFlBU`IU`GEdCs@~PO|CHX@b@KfG@nC@LJ~HDz@JtGX`@^L^@bNOz@dFzDa@nDR~CRjD^tCLzCoAxAgASgBg@_Cw@sBe@wAqBsBkCsAcASi@KJq@f@cA";
    } finally {
      setLoading(false);
    }
  };

  // Polyline decoder service
  const fetchPolylineCoordinates = async (polyline) => {
    try {
      const response = await fetch("http://localhost:5006/decode", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          polyline: polyline,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      if (data && data.coordinates && data.coordinates.length > 0) {
        return data.coordinates;
      } else {
        throw new Error("No coordinates found in API response");
      }
    } catch (err) {
      console.error("Error decoding polyline:", err);

      // For demo/fallback, return some fake coordinates
      // This simulates what your API would return
      return [
        // this should return a error
      ];
    }
  };

  // Function to update or create route on map
  const updateRouteOnMap = (decodedPoints) => {
    if (!map.current) return;
    console.log("Updating route with points:", decodedPoints.length);

    // Check if the source already exists
    if (map.current.getSource("route")) {
      console.log("Source exists, updating data");
      // Update existing source with new data
      map.current.getSource("route").setData({
        type: "Feature",
        properties: {},
        geometry: {
          type: "LineString",
          coordinates: decodedPoints.map((point) => [point.lng, point.lat]),
        },
      });
    } else {
      // Source doesn't exist, so create it and add layer
      map.current.addSource("route", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: {
            type: "LineString",
            coordinates: decodedPoints.map((point) => [point.lng, point.lat]),
          },
        },
      });

      // Add line layer
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
  };

  // Initialize Mapbox map
  useEffect(() => {
    console.log({ deliveryData });
    const script = document.createElement("script");
    script.src =
      "https://cdnjs.cloudflare.com/ajax/libs/mapbox-gl/2.15.0/mapbox-gl.js";
    script.async = true;

    script.onload = () => {
      const mapboxgl = window.mapboxgl;
      mapboxgl.accessToken =
        "pk.eyJ1IjoicXVla2t5eiIsImEiOiJjbTdzemJqcTEwdG9mMmxvaWw4b2Y3YWZiIn0.pX3y1okQlBpQM0lPHYoMjg";

      if (!map.current && mapContainer.current) {
        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: "mapbox://styles/mapbox/streets-v12",
          zoom: 12,
          center: [origin.lng, origin.lat], // Center initially on origin
        });

        map.current.on("load", () => {
          setMapLoaded(true);
        });
      }
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
  }, []);

  // Fetch and process route once map is loaded
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Get the route polyline from the API and draw on map
    const getRouteAndDraw = async () => {
      // Use polyline from the delivery data if available, or fetch a new one
      const encodedPolyline = deliveryData?.polyline || (await fetchRoute());
      setPolyline(encodedPolyline);

      // Then decode it
      let decodedPoints;
      try {
        decodedPoints = await fetchPolylineCoordinates(encodedPolyline);
      } catch (err) {
        setError(err);
        console.log("Error: " + error);
      }

      if (!decodedPoints || decodedPoints.length === 0) {
        console.error("No points decoded from polyline");
        return;
      }

      // For the demo, use the same fake route from your original code
      let fakedecodedPoints;
      try {
        const fakePolyline =
          "evdG}smyRPg@dB}AtBlCl@n@qAhAMZ_@|@Qn@E~@@d@M~CEf@K\\Ub@uBbBITAPBRlAbB@TnCfDzQlUhAtAv@fAd@~@Xz@XvAJ~@DvAEhB}@dZc@nPBlHL~DP`CZlCj@xDvAdGxAvEbGdPrGtPnBzFnBpFnCnHjDjJvFpLhAvCf@pBtCrOrBxJr@jFbIdr@Fv@~@hHzAxJ~@lG`@`EPbDD\\F~IHzAVlB`@bBbDtKvDxLR|@VtBJdCEjDK`DMz@w@tBQZG\\qCnDi@b@aG~Do@h@iQvLqAdAkAdA{@z@eDnEy@~A_A~Bw@fCWhAuAfHa@|A{@~B{BdG[pAShBEjA@z@NnA`@pBbBlGDZfBzHVhBFlBU`IU`GEdCs@~PO|CHX@b@KfG@nC@LJ~HDz@JtGX`@^L^@bNOz@dFzDa@nDR~CRjD^tCLzCoAxAgASgBg@_Cw@sBe@wAqBsBkCsAcASi@KJq@f@cA";
        fakedecodedPoints = await fetchPolylineCoordinates(fakePolyline);
      } catch (err) {
        console.log("Error with fake route: " + err);
        fakedecodedPoints = decodedPoints; // Fallback to the real route
      }

      // Set ref for the decoded points to be used
      setRoutePoints(decodedPoints);
      // setfakeRoutePoints(fakedecodedPoints || decodedPoints);

      // Update driver's initial location to first point in route
      setDriver((prev) => ({
        ...prev,
        location: decodedPoints[0],
      }));

      updateRouteOnMap(decodedPoints);

      // Fit map to the route bounds
      if (decodedPoints.length > 1) {
        const bounds = new window.mapboxgl.LngLatBounds();
        decodedPoints.forEach((point) => {
          bounds.extend([point.lng, point.lat]);
        });
        map.current.fitBounds(bounds, { padding: 50 });
      }

      // Add markers for origin (green) and destination (red)
      new window.mapboxgl.Marker({ color: "#00bb00" })
        .setLngLat([origin.lng, origin.lat])
        .addTo(map.current);

      new window.mapboxgl.Marker({ color: "#ff0000" })
        .setLngLat([destination.lng, destination.lat])
        .addTo(map.current);

      // Create truck marker for the driver
      const el = document.createElement("div");
      el.className = "flex items-center justify-center";
      el.innerHTML =
        '<div class="bg-blue-500 p-2 rounded-full">' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
        '<rect x="1" y="3" width="15" height="13" />' +
        '<polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />' +
        '<circle cx="5.5" cy="18.5" r="2.5" />' +
        '<circle cx="18.5" cy="18.5" r="2.5" />' +
        "</svg></div>";

      truckMarker.current = new window.mapboxgl.Marker({
        element: el,
        anchor: "bottom",
      })
        .setLngLat([decodedPoints[0].lng, decodedPoints[0].lat])
        .addTo(map.current);
    };

    getRouteAndDraw();
  }, [mapLoaded, deliveryData]);

  // Move truck along the route
  useEffect(() => {
    if (!mapLoaded || fakeRoutePoints.length === 0 || !truckMarker.current)
      return;

    const interval = setInterval(() => {
      setCurrentPointIndex((prevIndex) => {
        if (prevIndex >= fakeRoutePoints.length - 1) {
          clearInterval(interval);
          return prevIndex;
        }

        const nextIndex = prevIndex + 1;
        const nextPoint = fakeRoutePoints[nextIndex];

        // Move the truck marker
        if (truckMarker.current) {
          truckMarker.current.setLngLat([nextPoint.lng, nextPoint.lat]);
        }

        // Update driver info with new location and progress
        setDriver((prev) => ({
          ...prev,
          location: nextPoint,
          progress: Math.floor(
            (nextIndex / (fakeRoutePoints.length - 1)) * 100
          ),
        }));

        return nextIndex;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [mapLoaded, fakeRoutePoints]);

  // Separate effect for route updating
  useEffect(() => {
    if (!mapLoaded || currentPointIndex === 0) return;

    const currentPoint = fakeRoutePoints[currentPointIndex];
    const newcoord = {
      lat: currentPoint.lat,
      lng: currentPoint.lng,
    };

    // First check for deviation using current polyline and position
    getDeviation(basepolyline, newcoord)
      .then((isDeviated) => {
        if (isDeviated) {
          console.log("Deviation detected, fetching new route");
          // Only fetch new route if deviation is detected
          return fetchRoute(newcoord).then((newPolyline) => {
            if (!newPolyline) {
              console.log("Failed to get new polyline");
              return null;
            }

            // Update the base polyline with the new one
            setPolyline(newPolyline);

            // Decode the new polyline
            return fetchPolylineCoordinates(newPolyline);
          });
        } else {
          console.log("No deviation detected, using existing route");
          return null;
        }
      })
      .then((decodedPoints) => {
        // Only update the route if we have new decoded points
        if (decodedPoints && Array.isArray(decodedPoints)) {
          updateRouteOnMap(decodedPoints);
          setRoutePoints(decodedPoints);
          console.log("Route updated with new path");
        }
      })
      .catch((err) => {
        console.error("Error in deviation/routing process:", err);
      });
  }, [currentPointIndex, mapLoaded, fakeRoutePoints, basepolyline]);

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
                  Error: {error}. Using fallback route.
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
