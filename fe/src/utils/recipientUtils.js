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
    `http://localhost:8000/api/v1/personal/${recipientId}`
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
    `http://localhost:8000/api/v1/lab-reports/${recipientId}`
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
  // Extract just the number portion from the recipient ID
  // Then convert to a number to remove leading zeros

  console.log("Searching for matches with recipient number:", recipientId);

  // Use the endpoint to get matches by recipient ID number
  const response = await fetch(
    `http://localhost:5008/matches/recipient/${recipientId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

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
 * @returns {Promise<Object>} Response from the request_for_organ API
 */
export const requestNewOrgans = async (recipient) => {
  const response = await fetch(
    "http://localhost:8000/api/v1/request-for-organ",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        recipient: {
          recipientId: recipient.recipientId,
          firstName: recipient.firstName,
          lastName: recipient.lastName,
          dateOfBirth: recipient.dateOfBirth,
          nric: recipient.nric,
          email: recipient.email,
          address: recipient.address,
          gender: recipient.gender,
          bloodType: recipient.bloodType,
          organsNeeded: recipient.organsNeeded,
          nokContact: recipient.nokContact || {},
        },
        labInfo: {
          // Lab report data
          testType: "Tissue",
          reportName: "Transplant Eligibility",
          testType: "Organ Request",
          dateOfReport: new Date().toISOString().split("T")[0], // YYYY-MM-DD formate
          report: {
            name: "Tissue Lab Test Report",
            url: "https://www.parkwaylabs.com.sg/docs/parkwaylablibraries/test-catalogues/pls-tissue-forms.pdf?sfvrsn=1418faf5_1",
          },
          hlaTyping: {},
          comments: "To be reviewed",
          uuid: recipient.recipientId,
        },
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
};

// {
//   "data": {
//     "recipient": {
//       "firstName": "Isaiah",
//       "lastName": "Jackson",
//       "dateOfBirth": "1990-05-20",
//     "nric": "S1234567Z",
//       "email": "isaiahloo@gmail.com",
//       "address": "31 Victoria Street",
//       "bloodType": "O+",
//       "gender": "Male",
//       "organsNeeded": [
//         "kidney",
//         "liver"
//       ],
//       "medicalHistory": [
//         {
//           "condition": "Hypertension",
//           "dateDiagnosed": "2015-03-15",
//           "description": "Mild high blood pressure managed with lifestyle changes",
//           "treatment": "Diet and exercise"
//         }
//       ],
//       "allergies": [
//         "penicillin"
//       ],
//       "nokContact": {
//         "firstName": "Bob",
//         "lastName": "Smith",
//         "phone": "98765432",
//         "relationship": "Spouse"
//       }
//     },
//     "labInfo": {
//         "testType": "Tissue",
//         "dateOfReport": "2023-12-01",
//         "report": {
//             "name": "Tissue Lab Test Report",
//             "url": "https://www.parkwaylabs.com.sg/docs/parkwaylablibraries/test-catalogues/pls-tissue-forms.pdf?sfvrsn=1418faf5_1"
//         },
//         "hlaTyping":  {
//         },
//         "comments": "To be reviewed"
//     }
//   }
// }
