import { fetchDeliveries } from "./routeUtils";

// utils/recipientUtils.js

/**
 * Format a date string for display
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString) => {
  if (!dateString) return "Not specified";

  try {
    const options = { year: "numeric", month: "long", day: "numeric" };
    return new Date(dateString).toLocaleDateString(undefined, options);
  } catch (e) {
    return dateString;
  }
};

/**
 * Determine urgency color based on organs needed
 * @param {Array} organsNeeded - Array of needed organs
 * @returns {string} CSS class string for urgency indicator
 */
export const getUrgencyColor = (organsNeeded) => {
  if (!organsNeeded || organsNeeded.length === 0)
    return "bg-gray-100 text-gray-800";

  const criticalOrgans = ["heart", "liver"];
  const hasCriticalOrgan = organsNeeded.some((organ) =>
    criticalOrgans.includes(organ.toLowerCase())
  );

  if (hasCriticalOrgan) {
    return "bg-red-100 text-red-800";
  } else if (organsNeeded.length > 1) {
    return "bg-orange-100 text-orange-800";
  } else {
    return "bg-yellow-100 text-yellow-800";
  }
};

/**
 * Fetches recipients from the API
 * @returns {Promise<Array>} Array of recipient objects
 */
export const fetchRecipients = async () => {
  const response = await fetch("http://localhost:8000/api/v1/recipient");

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();

  if (data.code === 200 && data.data) {
    // Convert the object of recipients into an array
    return Object.values(data.data);
  } else {
    throw new Error("Invalid response format");
  }
};
/**
 * Fetches a recipient from the API
 * @returns {Promise<Object>} a recipient object
 */
export const getPersonalData = async (recipientId, passcode) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/personal/${recipientId}?apikey=${passcode}`
  );

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();

  if (data.Result.Success === true && data.patient) {
    // Convert the object of recipients into an array
    return data.patient;
  } else {
    throw new Error("Invalid response format");
  }
};

/**
 * Fetches lab reports for a specific recipient
 * @param {string} recipientId - ID of the recipient
 * @returns {Promise<Array>} Array of lab report objects
 */
export const fetchLabReports = async (recipientId) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/lab-reports/recipient/${recipientId}`
  );

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();

  if (data.code === 200 && data.data) {
    // Filter lab reports for the selected recipient
    console.log(data.data);
    return data.data || [];
  }

  return [];
};

/**
 * Finds potential organ matches for a recipient
 * @param {string} recipientId - ID of the recipient
 * @returns {Promise<Array>} Array of match objects
 */
export const findOrganMatches = async (recipientId) => {
  console.log("Searching for matches with recipient number:", recipientId);

  const response = await fetch(
    `http://localhost:8000/api/v1/organ-matches/${recipientId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  // Handle 404 manually
  if (response.status === 404) {
    return []; // Treat as "no matches" instead of an error
  }

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();

  if (data && data.code === 200) {
    console.log(data.data);
    return data.data || [];
  }

  return [];
};

/**
 * Creates an order for an organ transplant
 * @param {Object} selectedMatch - The selected match object
 * @param {Object} selectedRecipient - The selected recipient object
 * @returns {Promise<Object>} Response from the order API
 */
export const createOrganOrder = async (selectedMatch, selectedRecipient) => {
  const orderResponse = await fetch("http://localhost:8000/api/v1/order", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      orderId: `order-${Date.now()}`,
      organType: selectedMatch.OrganId.split("-")[1] || "Unknown",
      transplantDateTime: new Date(Date.now() + 86400000).toISOString(), // Schedule 24 hours from now
      startHospital: "Changi Hospital", // Default values since we don't have this information
      endHospital: "Tan Tock Seng Hospital",
      matchId: selectedMatch.matchId,
      remarks: `Organ transplant request for ${selectedRecipient.firstName} ${selectedRecipient.lastName}`,
    }),
  });

  if (!orderResponse.ok) {
    throw new Error(`Order request failed with status ${orderResponse.status}`);
  }

  return orderResponse.json();
};

/**
 * Creates a delivery request for an organ
 * @returns {Promise<Object>} Response from the delivery API
 */
export const createDeliveryRequest = async () => {
  const deliveryResponse = await fetch("http://localhost:5026/createDelivery", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      startHospital: "Changi Hospital",
      endHospital: "Tan Tock Seng Hospital",
      DoctorId: "doctor-001", // Assuming a default doctor ID
      transplantDateTime: new Date(Date.now() + 86400000).toISOString(),
    }),
  });

  return deliveryResponse.json();
};

/**
 * Requests new organs for a recipient
 * @param {Object} recipient - The recipient object
 * @returns {Promise<Object>} Response from the request-for-organ API
 */
export const requestNewOrgans = async (payload) => {
  console.log(payload);
  const response = await fetch(
    "http://localhost:8000/api/v1/request-for-organ",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        data: {
          recipient: {
            firstName: payload.recipient.firstName,
            lastName: payload.recipient.lastName,
            dateOfBirth: payload.recipient.dateOfBirth,
            nric: payload.recipient.nric,
            email: payload.recipient.email,
            address: payload.recipient.address,
            gender: payload.recipient.gender,
            bloodType: payload.recipient.bloodType,
            organsNeeded: payload.recipient.organsNeeded,
            medicalHistory: payload.recipient.medicalHistory,
            allergies: payload.recipient.allergies,
            nokContact: payload.recipient.nokContact,
          },
          labInfo: {
            // Lab report data
            testType: payload.labInfo.testType,
            dateOfReport: payload.labInfo.dateOfReport, // YYYY-MM-DD formate
            report: {
              name: payload.labInfo.reportName,
              url: payload.labInfo.reportUrl,
            },
            hlaTyping: {},
            comments: payload.labInfo.comments,
          },
        },
      }),
    }
  );
  // console.log(response);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
};

/**
 * Confirm match for a recipient
 * @param {Object} recipientId - The recipient object
 * @returns {Promise<Object>} Response from the confirm-match API
 */
export const initiateMatch = async (recipientId) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/initiate-match/${recipientId}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
};
/**
 * Confirm match for a recipient
 * @param {Object} payload - The recipient object
 * @returns {Promise<Object>} Response from the confirm-match API
 */
export const confirmMatch = async (payload) => {
  const response = await fetch("http://localhost:8000/api/v1/confirm-match", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      organType: payload.organType, // "liver"
      doctorId: payload.doctorId, // "example@gmail.com"
      transplantDateTime: payload.transplantDateTime, // "2025-03-31T05:30:00.000Z" UTC
      startHospital: payload.startHospital, // "CGH"
      endHospital: payload.endHospital, // "TTSH"
      matchId: payload.matchId, // "string ID"
      remarks: payload.remarks, // "To be reviewed"
    }),
  });

  console.log(response);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
};

/**
 * Find all deliveries that match a specific recipient ID
 * @param {string} recipientId - The ID of the recipient to match
 * @returns {Promise<Array>} Array of delivery objects that match the recipient
 */
export const matchDeliveries = async (recipientId) => {
  if (!recipientId) {
    throw new Error("Recipient ID is required");
  }

  try {
    // Step 1: Use the existing findOrganMatches function to get all matches for this recipient
    const matches = await findOrganMatches(recipientId);

    if (!matches || matches.length === 0) {
      return []; // No matches found for this recipient
    }

    // Step 2: Fetch all deliveries using the existing fetchDeliveries function
    const deliveries = await fetchDeliveries();

    // Step 3: Find all deliveries with matchIds that correspond to our matches
    const matchIds = matches.map((match) => match.matchId);

    const matchingDeliveries = deliveries
      .filter(
        (delivery) => delivery.matchId && matchIds.includes(delivery.matchId)
      )
      .map((delivery) => {
        // Find the corresponding match details
        const matchDetails = matches.find(
          (match) => match.matchId === delivery.matchId
        );
        return {
          ...delivery,
          matchDetails,
        };
      });

    return matchingDeliveries;
  } catch (error) {
    console.error("Error in matchDeliveries:", error);
    throw error;
  }
};
