// File: utils/routeUtils.js

/**
 * Converts an address string to geographic coordinates
 * @param {string} address - The address to geocode
 * @returns {Promise<Object|null>} Coordinates as {lat, lng} or null on failure
 */
export const addressToCoordinates = async (address) => {
  try {
    const response = await fetch(
      "https://zsq.outsystemscloud.com/Location/rest/Location/PlaceToCoord",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          long_name: address,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.status !== "OK" && data.ErrorMessage) {
      throw new Error(data.ErrorMessage);
    }

    return {
      lat: data.latitude,
      lng: data.longitude,
    };
  } catch (error) {
    console.error("Error converting address to coordinates:", error);
    return null;
  }
};

/**
 * Decodes a polyline string into an array of coordinates.
 * @param {string} polyline - The encoded polyline string
 * @returns {Promise<Array>} Array of coordinates in {lat, lng} format
 */
export const decodePolyline = async (polyline) => {
  try {
    const response = await fetch("http://localhost:5006/decode", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ polyline }),
    });

    if (!response.ok) {
      throw new Error(`Decode API error: ${response.status}`);
    }

    const data = await response.json();
    return data.coordinates || [];
  } catch (error) {
    console.error("Error decoding polyline:", error);
    return [];
  }
};

/**
 * Calculates the distance between two points using the Haversine formula
 * @param {Object} point1 - First point as {lat, lng}
 * @param {Object} point2 - Second point as {lat, lng}
 * @returns {number} Distance in kilometers
 */
export const calculateDistance = (point1, point2) => {
  const toRad = (value) => (value * Math.PI) / 180;
  const R = 6371; // Earth's radius in km
  const dLat = toRad(point2.lat - point1.lat);
  const dLon = toRad(point2.lng - point1.lng);
  const lat1 = toRad(point1.lat);
  const lat2 = toRad(point2.lat);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // Return distance in kilometers
};

/**
 * Checks if a driver has deviated from route using the backend API
 * @param {string} polyline - The encoded polyline string of the route
 * @param {Object} driverCoord - Current driver position as {lat, lng}
 * @returns {Promise<boolean>} Whether the driver has deviated
 */
export const checkRouteDeviation = async (polyline, driverCoord) => {
  try {
    const response = await fetch("http://localhost:5006/deviate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        polyline,
        driverCoord,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      deviated: data.data.deviate,
    };
  } catch (error) {
    console.error("Error checking deviation:", error);
    return { deviated: false, distance: 0, closestPointIndex: 0 };
  }
};

/**
 * Request a new route from the backend API
 * @param {Array} currentPosition - Current position as {lat, lng}
 * @param {Array} destinationPoint - Destination as {lat, lng}
 * @param {Object} deliveryData - Delivery data object
 * @returns {Promise<Array|null>} New coordinates or null on failure
 */
export const requestNewRoute = async (currentPosition, destinationPoint) => {
  try {
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
                latitude: destinationPoint.lat,
                longitude: destinationPoint.lng,
              },
            },
          },
          origin: {
            location: {
              latLng: {
                latitude: currentPosition.lat,
                longitude: currentPosition.lng,
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

    if (!data?.Route?.[0]?.Polyline?.encodedPolyline) {
      throw new Error("No polyline in response");
    }

    const polyline = data.Route[0].Polyline.encodedPolyline;

    // Decode the polyline
    const coordinates = await decodePolyline(polyline);
    return coordinates;
  } catch (error) {
    console.error("Error fetching new route:", error);
    return null;
  }
};

/**
 * Calculate progress based on straight-line distance
 * @param {Object} currentPos - Current position as {lat, lng}
 * @param {Object} startPos - Start position as {lat, lng}
 * @param {Object} endPos - End position as {lat, lng}
 * @returns {number} Progress percentage (0-100)
 */
export const calculateProgressByDistance = (currentPos, startPos, endPos) => {
  // Calculate total straight-line distance from start to end
  const totalDistance = Math.sqrt(
    Math.pow(endPos.lng - startPos.lng, 2) +
      Math.pow(endPos.lat - startPos.lat, 2)
  );

  // Calculate distance already traveled (straight line from start to current)
  const distanceTraveled = Math.sqrt(
    Math.pow(currentPos.lng - startPos.lng, 2) +
      Math.pow(currentPos.lat - startPos.lat, 2)
  );

  // Calculate progress percentage
  return Math.min(Math.floor((distanceTraveled / totalDistance) * 100), 100);
};

/**
 * Format a date string in the format "YYYYMMDD HH:MM:SS AM/PM"
 * @param {string} dateString - The date string to format
 * @returns {string} Formatted date string
 */
export const formatDeliveryDate = (dateString) => {
  if (!dateString) return "N/A";

  // Parse the date format "YYYYMMDD HH:MM:SS AM/PM"
  const [datePart, timePart, ampm] = dateString.split(" ");

  // Format YYYYMMDD to YYYY-MM-DD
  const year = datePart.substring(0, 4);
  const month = datePart.substring(4, 6);
  const day = datePart.substring(6, 8);

  return `${year}-${month}-${day} ${timePart} ${ampm}`;
};

/**
 * Get the color class for a delivery status badge
 * @param {string} status - The delivery status
 * @returns {string} CSS class string for the status badge
 */
export const getDeliveryStatusColor = (status) => {
  switch (status) {
    case "Awaiting pickup":
      return "bg-yellow-100 text-yellow-800";
    case "In progress":
      return "bg-blue-100 text-blue-800";
    case "Completed":
      return "bg-green-100 text-green-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

/**
 * Fetch all delivery information
 * @returns {Promise<Array>} Array of delivery objects
 */
export const fetchDeliveries = async () => {
  const response = await fetch("http://localhost:5002/deliveryinfo");

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();

  if (data.code === 200 && data.data) {
    // Convert the object of deliveries into an array
    return Object.values(data.data);
  } else {
    throw new Error("Invalid response format");
  }
};

/**
 * Delete a delivery
 * @param {string} deliveryId - The delivery ID to delete
 * @returns {Promise<boolean>} Success status
 */
export const deleteDelivery = async (deliveryId) => {
  const response = await fetch(
    `http://localhost:5002/deliveryinfo/${deliveryId}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: "Deleted" }),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to delete delivery");
  }

  return true;
};
