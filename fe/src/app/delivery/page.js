// File: app/doctor/page.js
"use client";

import { useState, useEffect } from "react";
import {
  Loader2,
  Calendar,
  User,
  Heart,
  ArrowLeft,
  BadgeAlert,
  Activity,
} from "lucide-react";
import Link from "next/link";

export default function RecipientsDashboard() {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [labReports, setLabReports] = useState([]);
  const [loadingLabReports, setLoadingLabReports] = useState(false);

  // Match and request organ states
  const [matches, setMatches] = useState([]);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState(null);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [requestLoading, setRequestLoading] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState(false);

  useEffect(() => {
    async function fetchRecipients() {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:5013/recipient");

        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.code === 200 && data.data) {
          // Convert the object of recipients into an array
          const recipientsArray = Object.values(data.data);
          setRecipients(recipientsArray);
        } else {
          throw new Error("Invalid response format");
        }
      } catch (err) {
        console.error("Error fetching recipients:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchRecipients();
  }, []);

  // Function to fetch lab reports for a specific recipient
  const fetchLabReports = async (recipientId) => {
    try {
      setLoadingLabReports(true);
      const response = await fetch("http://localhost:5007/lab-reports");

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();

      if (data.code === 200 && data.data) {
        // Filter lab reports for the selected recipient
        const filteredReports = data.data.filter(
          (report) =>
            report.patientId === recipientId ||
            report.recipientId === recipientId
        );
        setLabReports(filteredReports);
      } else {
        setLabReports([]);
      }
    } catch (err) {
      console.error("Error fetching lab reports:", err);
      setLabReports([]);
    } finally {
      setLoadingLabReports(false);
    }
  };

  // Handle click on a recipient to view details
  const handleRecipientClick = (recipient) => {
    setSelectedRecipient(recipient);
    setSelectedMatch(null);
    setMatches([]);
    setMatchError(null);
    setRequestSuccess(false);
    if (recipient.recipientId) {
      fetchLabReports(recipient.recipientId);
    }
  };

  // Go back to recipient list
  const handleBackClick = () => {
    setSelectedRecipient(null);
    setLabReports([]);
    setMatches([]);
    setSelectedMatch(null);
    setRequestSuccess(false);
  };

  // Find potential organ matches for a recipient
  const handleFindMatches = async (recipientId) => {
    if (!recipientId) return;

    setMatchLoading(true);
    setMatchError(null);
    setSelectedMatch(null);

    try {
      // The match API is actually exposed through RabbitMQ, not a direct endpoint
      // We need to use the request_for_organ endpoint with the match.request routing key
      const response = await fetch("http://localhost:5021/request_for_organ", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          recipientId,
          // Include other required fields for the request_for_organ API
          firstName: selectedRecipient.firstName,
          lastName: selectedRecipient.lastName,
          dateOfBirth: selectedRecipient.dateOfBirth,
          gender: selectedRecipient.gender,
          bloodType: selectedRecipient.bloodType,
          organsNeeded: selectedRecipient.organsNeeded,
          nokContact: selectedRecipient.nokContact || {},
          // Empty fields for lab report data
          reportName: "",
          testType: "",
          dateOfReport: new Date().toISOString(),
          results: {},
        }),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();

      // Since this is a message queue-based system, we won't get immediate match results
      // Instead, we'll simulate it with some sample data for the UI
      // In a real implementation, you'd use websockets or polling to get the actual matches

      // Simulate match response after a delay
      setTimeout(() => {
        const simulatedMatches = generateSimulatedMatches(selectedRecipient);
        setMatches(simulatedMatches);
        setMatchLoading(false);
      }, 2000);
    } catch (err) {
      console.error("Error finding matches:", err);
      setMatchError(err.message);
      setMatches([]);
      setMatchLoading(false);
    }
  };

  // Generate simulated match data based on recipient
  const generateSimulatedMatches = (recipient) => {
    const organsNeeded = recipient.organsNeeded || ["heart"];
    const matchCount = Math.floor(Math.random() * 3) + 1; // 1-3 matches

    return Array.from({ length: matchCount }, (_, i) => {
      const organType = organsNeeded[i % organsNeeded.length];
      const donorId = `donor-${Math.floor(Math.random() * 10000)}`;

      return {
        matchId: `${donorId}-${organType}-${recipient.recipientId}`,
        OrganId: `${donorId}-${organType}`,
        donorId: donorId,
        recipientId: recipient.recipientId,
        numOfHLA: Math.floor(Math.random() * 3) + 4, // 4-6 HLA match
        Test_DateTime: new Date().toISOString(),
        donor_details: {
          first_name: ["John", "Jane", "Michael", "Sarah", "David"][
            Math.floor(Math.random() * 5)
          ],
          last_name: ["Smith", "Johnson", "Williams", "Brown", "Jones"][
            Math.floor(Math.random() * 5)
          ],
          gender: Math.random() > 0.5 ? "Male" : "Female",
          blood_type: ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"][
            Math.floor(Math.random() * 8)
          ],
        },
        recipient_details: {
          first_name: recipient.firstName,
          last_name: recipient.lastName,
          gender: recipient.gender,
          blood_type: recipient.bloodType,
        },
      };
    });
  };

  // Handle requesting an organ based on selected match
  const handleRequestOrgan = async () => {
    if (!selectedMatch || !selectedRecipient) return;

    setRequestLoading(true);

    try {
      // Call the request organ API with the match data
      const response = await fetch("http://localhost:5021/request_for_organ", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          recipientId: selectedRecipient.recipientId,
          matchId: selectedMatch.matchId,
          organId: selectedMatch.OrganId,
          // Include required recipient data
          firstName: selectedRecipient.firstName,
          lastName: selectedRecipient.lastName,
          dateOfBirth: selectedRecipient.dateOfBirth,
          gender: selectedRecipient.gender,
          bloodType: selectedRecipient.bloodType,
          organsNeeded: selectedRecipient.organsNeeded,
          nokContact: selectedRecipient.nokContact || {},
          // Include lab report data that might be required
          reportName: `Transplant Request for ${
            selectedMatch.OrganId.split("-")[1] || "Organ"
          }`,
          testType: "Transplant Request",
          dateOfReport: new Date().toISOString(),
          results: {
            hlaMatch: `${selectedMatch.numOfHLA}/6`,
            bloodTypeCompatibility: "Compatible",
            status: "Requested",
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      console.log("Organ request response:", data);

      // Show success message
      setRequestSuccess(true);
    } catch (err) {
      console.error("Error requesting organ:", err);
      alert(`Failed to request organ: ${err.message}`);
    } finally {
      setRequestLoading(false);
    }
  };

  // Function to format date for display
  const formatDate = (dateString) => {
    if (!dateString) return "Not specified";

    try {
      const options = { year: "numeric", month: "long", day: "numeric" };
      return new Date(dateString).toLocaleDateString(undefined, options);
    } catch (e) {
      return dateString;
    }
  };

  // Function to determine urgency color based on organs needed
  const getUrgencyColor = (organsNeeded) => {
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

  // Render recipient detail view
  if (selectedRecipient) {
    return (
      <div className="container mx-auto px-4 py-8">
        <button
          onClick={handleBackClick}
          className="flex items-center text-green-600 hover:text-green-800 mb-6 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to all recipients
        </button>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Recipient Information Panel */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="bg-green-600 text-white p-6">
                <h1 className="text-2xl font-bold">Recipient Profile</h1>
                <p className="mt-2 flex items-center text-green-100">
                  <User className="h-4 w-4 mr-2" />
                  ID: {selectedRecipient.recipientId || "Not assigned"}
                </p>
              </div>

              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-xl font-bold mb-4 text-gray-800">
                    Personal Information
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-gray-500">Full Name</p>
                      <p className="font-medium text-gray-800">
                        {selectedRecipient.firstName}{" "}
                        {selectedRecipient.lastName}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500">Date of Birth</p>
                      <p className="font-medium text-gray-800">
                        {formatDate(selectedRecipient.dateOfBirth)}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500">Gender</p>
                      <p className="font-medium text-gray-800">
                        {selectedRecipient.gender}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500">Blood Type</p>
                      <p className="font-medium text-gray-800">
                        {selectedRecipient.bloodType}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h2 className="text-xl font-bold mb-4 text-gray-800">
                    Medical Information
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-gray-500">Organs Needed</p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {selectedRecipient.organsNeeded &&
                        selectedRecipient.organsNeeded.length > 0 ? (
                          selectedRecipient.organsNeeded.map((organ, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs"
                            >
                              {organ}
                            </span>
                          ))
                        ) : (
                          <p className="text-gray-600">None specified</p>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500">Allergies</p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {selectedRecipient.allergies &&
                        selectedRecipient.allergies.length > 0 ? (
                          selectedRecipient.allergies.map((allergy, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs"
                            >
                              {allergy}
                            </span>
                          ))
                        ) : (
                          <p className="text-gray-600">No known allergies</p>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500">Medical History</p>
                      {selectedRecipient.medicalHistory &&
                      selectedRecipient.medicalHistory.length > 0 ? (
                        <ul className="mt-1 list-disc pl-5 text-gray-600">
                          {selectedRecipient.medicalHistory.map(
                            (item, index) => (
                              <li key={index}>
                                {typeof item === "object" ? (
                                  <div className="py-1">
                                    <p className="font-medium">
                                      {item.description ||
                                        item.condition ||
                                        "Medical condition"}
                                    </p>
                                    {item.dateDiagnosed && (
                                      <p className="text-xs text-gray-500">
                                        Diagnosed:{" "}
                                        {formatDate(item.dateDiagnosed)}
                                      </p>
                                    )}
                                    {item.treatment && (
                                      <p className="text-xs">
                                        Treatment: {item.treatment}
                                      </p>
                                    )}
                                  </div>
                                ) : (
                                  item
                                )}
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        <p className="text-gray-600">
                          No medical history available
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {selectedRecipient.nokContact && (
                  <div>
                    <h2 className="text-xl font-bold mb-4 text-gray-800">
                      Emergency Contact
                    </h2>
                    <div className="space-y-2 text-gray-600">
                      <p>
                        <span className="font-medium">Name:</span>{" "}
                        {selectedRecipient.nokContact.firstName}{" "}
                        {selectedRecipient.nokContact.lastName}
                      </p>
                      <p>
                        <span className="font-medium">Relationship:</span>{" "}
                        {selectedRecipient.nokContact.relationship}
                      </p>
                      <p>
                        <span className="font-medium">Phone:</span>{" "}
                        {selectedRecipient.nokContact.phone}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Lab Reports Section */}
          <div className="md:col-span-2">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="bg-green-600 text-white p-6">
                <h2 className="text-2xl font-bold">Lab Reports</h2>
              </div>

              <div className="p-6">
                {loadingLabReports ? (
                  <div className="flex justify-center items-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-green-500" />
                    <span className="ml-2 text-gray-600">
                      Loading lab reports...
                    </span>
                  </div>
                ) : labReports.length === 0 ? (
                  <div className="bg-gray-100 p-6 text-center rounded">
                    <p className="text-gray-700">
                      No lab reports found for this recipient.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {labReports.map((report, index) => (
                      <div
                        key={report.uuid || index}
                        className="border rounded-lg overflow-hidden"
                      >
                        <div className="bg-gray-50 px-4 py-3 border-b">
                          <h3 className="font-bold text-lg text-gray-800">
                            {report.reportName}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {formatDate(report.dateOfReport)}
                          </p>
                        </div>

                        <div className="p-4">
                          <div className="mb-4">
                            <p className="font-medium text-gray-700">
                              Test Type:
                            </p>
                            <p className="text-gray-600">
                              {report.testType || "Not specified"}
                            </p>
                          </div>

                          {report.results && (
                            <div>
                              <p className="font-medium text-gray-700 mb-2">
                                Results:
                              </p>
                              <div className="bg-gray-50 rounded-lg p-4">
                                {Object.entries(report.results).map(
                                  ([key, value]) => (
                                    <div
                                      key={key}
                                      className="grid grid-cols-2 mb-2 pb-2 border-b border-gray-200 last:border-0"
                                    >
                                      <span className="text-sm font-medium text-gray-500 capitalize">
                                        {key}
                                      </span>
                                      <span className="text-gray-800">
                                        {typeof value === "object"
                                          ? JSON.stringify(value)
                                          : value}
                                      </span>
                                    </div>
                                  )
                                )}
                              </div>
                            </div>
                          )}

                          {report.comments && (
                            <div className="mt-4">
                              <p className="font-medium text-gray-700">
                                Comments:
                              </p>
                              <p className="text-gray-600">{report.comments}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Activity Timeline */}
            {/* Match/Organ Section */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden mt-6">
              <div className="bg-green-600 text-white p-6 flex justify-between items-center">
                <h2 className="text-2xl font-bold">Organ Matches</h2>
                <button
                  onClick={() =>
                    handleFindMatches(selectedRecipient.recipientId)
                  }
                  className="px-4 py-2 bg-white text-green-600 rounded-md hover:bg-gray-100 transition-colors"
                >
                  Find Matches
                </button>
              </div>

              <div className="p-6">
                {matchLoading ? (
                  <div className="flex justify-center items-center h-48">
                    <Loader2 className="h-8 w-8 animate-spin text-green-500" />
                    <span className="ml-2 text-gray-600">
                      Finding potential matches...
                    </span>
                  </div>
                ) : matchError ? (
                  <div className="bg-red-100 p-4 rounded-md text-red-700">
                    <p className="font-bold">Error finding matches</p>
                    <p>{matchError}</p>
                  </div>
                ) : matches.length === 0 ? (
                  <div className="bg-gray-100 p-6 text-center rounded">
                    <p className="text-gray-700">
                      No potential organ matches found. Click "Find Matches" to
                      search for compatible donors.
                    </p>
                  </div>
                ) : (
                  <div>
                    {requestSuccess && (
                      <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                        <p className="font-bold">Success!</p>
                        <p>
                          Organ transplant has been requested successfully. The
                          medical team will be notified.
                        </p>
                      </div>
                    )}

                    <p className="text-gray-700 mb-4">
                      Select a match to request organ transplant:
                    </p>
                    <div className="grid gap-4 md:grid-cols-2">
                      {matches.map((match) => (
                        <div
                          key={match.matchId}
                          className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                            selectedMatch &&
                            selectedMatch.matchId === match.matchId
                              ? "border-green-500 bg-green-50"
                              : "border-gray-200 hover:border-green-300"
                          }`}
                          onClick={() => setSelectedMatch(match)}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-medium text-gray-800">
                              {match.OrganId.split("-")[1] || "Organ"}
                            </span>
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                              {match.numOfHLA}/6 HLA Match
                            </span>
                          </div>

                          <div className="text-sm space-y-1 text-gray-600">
                            <p>
                              Donor ID:{" "}
                              {match.donorId?.substring(0, 8) || "Unknown"}
                            </p>
                            <p>
                              Donor:{" "}
                              {match.donor_details?.first_name || "Unknown"}{" "}
                              {match.donor_details?.last_name || ""}
                              {match.donor_details?.gender &&
                                ` (${match.donor_details.gender})`}
                            </p>
                            <p>
                              Blood Type:{" "}
                              {match.donor_details?.blood_type || "Unknown"}
                            </p>
                            <p className="text-xs text-gray-500">
                              Match Date: {formatDate(match.Test_DateTime)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>

                    {selectedMatch && (
                      <div className="mt-6 flex justify-end">
                        <button
                          onClick={handleRequestOrgan}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center"
                          disabled={requestLoading}
                        >
                          {requestLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Processing Request...
                            </>
                          ) : (
                            "Request Organ Transplant"
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Activity Timeline */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden mt-6">
              <div className="bg-green-600 text-white p-6">
                <h2 className="text-2xl font-bold">Recipient Activity</h2>
              </div>

              <div className="p-6">
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                  <div className="space-y-8">
                    <div className="relative pl-10">
                      <div className="absolute left-0 top-1 rounded-full bg-green-500 p-2">
                        <Activity className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">
                          Added to recipient list
                        </p>
                        <p className="text-sm text-gray-500">March 20, 2025</p>
                      </div>
                    </div>

                    <div className="relative pl-10">
                      <div className="absolute left-0 top-1 rounded-full bg-blue-500 p-2">
                        <Activity className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">
                          Lab tests completed
                        </p>
                        <p className="text-sm text-gray-500">March 21, 2025</p>
                      </div>
                    </div>

                    <div className="relative pl-10">
                      <div className="absolute left-0 top-1 rounded-full bg-yellow-500 p-2">
                        <Activity className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">
                          Added to donor match queue
                        </p>
                        <p className="text-sm text-gray-500">March 22, 2025</p>
                      </div>
                    </div>

                    {requestSuccess && (
                      <div className="relative pl-10">
                        <div className="absolute left-0 top-1 rounded-full bg-red-500 p-2">
                          <Activity className="h-4 w-4 text-white" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-800">
                            Organ transplant requested
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date().toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render the card list view (default)
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Organ Recipients</h1>
        <Link
          href="/"
          className="px-4 py-2 bg-gray-100 rounded-md text-gray-600 hover:bg-gray-200 transition-colors"
        >
          Logout
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-green-500" />
          <span className="ml-2 text-gray-600">Loading recipients...</span>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      ) : recipients.length === 0 ? (
        <div className="bg-gray-100 p-6 text-center rounded">
          <p className="text-gray-700">No recipients found.</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {recipients.map((recipient, index) => (
            <div
              key={recipient.recipientId || index}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
              onClick={() => handleRecipientClick(recipient)}
            >
              <div className="p-5">
                <div className="flex justify-between items-start mb-3">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getUrgencyColor(
                      recipient.organsNeeded
                    )}`}
                  >
                    {recipient.organsNeeded && recipient.organsNeeded.length > 0
                      ? `Needs ${recipient.organsNeeded.length} organ${
                          recipient.organsNeeded.length > 1 ? "s" : ""
                        }`
                      : "No organs listed"}
                  </span>
                  <span className="text-xs text-gray-500">
                    ID: {recipient.recipientId?.substring(0, 8) || "N/A"}
                  </span>
                </div>

                <h3 className="font-bold text-gray-800 mb-3">
                  {recipient.firstName} {recipient.lastName}
                </h3>

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 text-green-600 mr-2" />
                    <span>{formatDate(recipient.dateOfBirth)}</span>
                  </div>

                  <div className="flex items-center">
                    <User className="h-4 w-4 text-green-600 mr-2" />
                    <span>{recipient.gender || "Not specified"}</span>
                  </div>

                  <div className="flex items-center">
                    <Heart className="h-4 w-4 text-green-600 mr-2" />
                    <span>
                      Blood Type: {recipient.bloodType || "Not specified"}
                    </span>
                  </div>
                </div>

                {recipient.organsNeeded &&
                  recipient.organsNeeded.length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs text-gray-500 mb-1">
                        Needed Organs:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {recipient.organsNeeded.map((organ, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs"
                          >
                            {organ}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </div>

              <div className="border-t px-5 py-3 bg-gray-50 flex justify-end items-center">
                <span className="text-green-600 text-sm font-medium flex items-center">
                  View details →
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
