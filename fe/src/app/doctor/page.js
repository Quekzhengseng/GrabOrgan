"use client";

import { useState, useEffect } from "react";
import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import DeliveryMapbox from "@/components/DeliveryMapbox";
import RecipientCard from "@/components/RecipientCard";
import RecipientProfile from "@/components/RecipientProfile";
import LabReports from "@/components/LabReports";
import OrganMatches from "@/components/OrganMatches";
import ActivityTimeline from "@/components/ActivityTimeline";
import DoctorDeliveryTracker from "@/components/DoctorDeliveryTracker";
import {
  fetchRecipients,
  fetchLabReports,
  findOrganMatches,
  createOrganOrder,
  createDeliveryRequest,
  requestNewOrgans,
  getPersonalData,
  matchDeliveries,
} from "@/utils/recipientUtils";

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

  // Delivery tracking states
  const [matchedDeliveries, setMatchedDeliveries] = useState([]);
  const [deliveriesLoading, setDeliveriesLoading] = useState(false);
  const [deliveriesError, setDeliveriesError] = useState(null);

  useEffect(() => {
    async function loadRecipients() {
      try {
        setLoading(true);
        const recipientsData = await fetchRecipients();
        console.log(recipientsData);
        setRecipients(recipientsData);
      } catch (err) {
        console.error("Error fetching recipients:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadRecipients();
  }, []);

  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const email = sessionStorage.getItem("userEmail");
    setUserEmail(email);
  }, []);
  // console.log("Doctor Page:",userEmail);

  // Handle loading lab reports for a recipient
  const loadLabReports = async (recipientId) => {
    try {
      setLoadingLabReports(true);
      const reports = await fetchLabReports(recipientId);
      setLabReports(reports);
    } catch (err) {
      console.error("Error fetching lab reports:", err);
      setLabReports([]);
    } finally {
      setLoadingLabReports(false);
    }
  };

  // Handle fetching delivery information for a recipient
  const loadDeliveries = async (recipientId) => {
    if (!recipientId) return;

    setDeliveriesLoading(true);
    setDeliveriesError(null);

    try {
      const deliveries = await matchDeliveries(recipientId);
      console.log("Matched deliveries:", deliveries);
      setMatchedDeliveries(deliveries || []);
    } catch (err) {
      console.error("Error finding delivery matches:", err);
      setDeliveriesError(err.message);
      setMatchedDeliveries([]);
    } finally {
      setDeliveriesLoading(false);
    }
  };

  // Handle click on a recipient to view details
  const handleRecipientClick = (recipient) => {
    setSelectedRecipient(recipient);
    setSelectedMatch(null);
    setMatches([]);
    setMatchError(null);
    setRequestSuccess(false);
    setMatchedDeliveries([]);
    setDeliveriesError(null);

    if (recipient.recipientId) {
      // Fetch lab reports
      loadLabReports(recipient.recipientId);

      // Automatically find matches for this recipient
      handleFindMatches(recipient.recipientId);

      // Find matching deliveries
      loadDeliveries(recipient.recipientId);
    }
  };

  // Go back to recipient list
  const handleBackClick = () => {
    setSelectedRecipient(null);
    setLabReports([]);
    setMatches([]);
    setSelectedMatch(null);
    setRequestSuccess(false);
    setMatchedDeliveries([]);
  };

  // Find potential organ matches for a recipient
  const handleFindMatches = async (recipientId) => {
    if (!recipientId) return;

    setMatchLoading(true);
    setMatchError(null);
    setSelectedMatch(null);

    try {
      const matchesData = await findOrganMatches(recipientId);
      setMatches(matchesData);

      if (matchesData.length === 0) {
        console.log("No matches found for this recipient");
      }
    } catch (err) {
      console.error("Error finding matches:", err);
      setMatchError(err.message);
      setMatches([]);
    } finally {
      setMatchLoading(false);
    }
  };

  // Handle requesting an organ based on selected match
  const handleRequestOrgan = async () => {
    if (!selectedMatch || !selectedRecipient) return;

    setRequestLoading(true);

    try {
      // Create order for the selected match
      await createOrganOrder(selectedMatch, selectedRecipient);

      // Now request organ delivery
      await createDeliveryRequest();

      // Show success message
      setRequestSuccess(true);

      // Refresh delivery info after request
      setTimeout(() => {
        loadDeliveries(selectedRecipient.recipientId);
      }, 2000);
    } catch (err) {
      console.error("Error requesting organ:", err);
      alert(`Failed to request organ: ${err.message}`);
    } finally {
      setRequestLoading(false);
    }
  };

  // Handle requesting new organs (when no matches found)
  const handleRequestNewOrgans = async () => {
    if (!selectedRecipient) return;

    setRequestLoading(true);

    try {
      // Call the request_for_organ API to initiate a new organ search
      const data = await requestNewOrgans(selectedRecipient);
      console.log("Request for new organs response:", data);

      // Show success message
      alert(
        "Request for new organs submitted successfully. The system will search for potential matches."
      );

      // Check for matches again after a short delay
      setTimeout(() => {
        handleFindMatches(selectedRecipient.recipientId);
      }, 3000);
    } catch (err) {
      console.error("Error requesting new organs:", err);
      alert(`Failed to request new organs: ${err.message}`);
    } finally {
      setRequestLoading(false);
    }
  };

  // Render delivery trackers section
  const renderDeliveryTrackers = () => {
    if (deliveriesLoading) {
      return (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-green-500" />
          <span className="ml-2 text-gray-600">
            Loading delivery information...
          </span>
        </div>
      );
    }

    if (deliveriesError) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-600">
          <p>Error loading delivery information: {deliveriesError}</p>
        </div>
      );
    }

    if (matchedDeliveries.length === 0) {
      return (
        <div className="bg-gray-50 rounded-md p-6 text-center">
          <p className="text-gray-500">
            No active deliveries found for this recipient.
          </p>
          {requestSuccess && (
            <p className="text-green-600 mt-2">
              A new organ has been requested. Delivery information will appear
              here when available.
            </p>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="border-b pb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Active Organ Deliveries
          </h3>
          <p className="text-sm text-gray-500">
            {matchedDeliveries.length} deliveries in progress
          </p>
        </div>

        {matchedDeliveries.map((delivery, index) => (
          <div
            key={delivery.orderID}
            className="bg-white rounded-lg shadow-md overflow-hidden"
          >
            <div className="bg-gray-50 px-4 py-3 border-b">
              <div className="flex justify-between items-center">
                <h4 className="font-medium text-gray-900">
                  Delivery #{index + 1}: {delivery.organType} Organ
                </h4>
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                    delivery.status === "In Progress"
                      ? "bg-green-100 text-green-800"
                      : delivery.status === "Assigned"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {delivery.status}
                </span>
              </div>
            </div>

            <div className="p-4">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs text-gray-500">Pickup Location</p>
                  <p className="text-sm font-medium">{delivery.pickup}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(
                      delivery.pickup_time.replace(" ", "T")
                    ).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Destination</p>
                  <p className="text-sm font-medium">{delivery.destination}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(
                      delivery.destination_time.replace(" ", "T")
                    ).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Map for this delivery */}
              <DoctorDeliveryTracker deliveryId={delivery.orderID} />

              {/* Match details if available */}
              {delivery.matchDetails && (
                <div className="mt-4 bg-blue-50 p-3 rounded-md">
                  <p className="text-xs text-blue-500 font-medium">
                    MATCH DETAILS
                  </p>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <p className="text-xs text-gray-700">
                      HLA Compatibility: {delivery.matchDetails.numOfHLA}/6
                    </p>
                    <p className="text-xs text-gray-700">
                      Match ID: {delivery.matchDetails.matchId.substring(0, 8)}
                      ...
                    </p>
                    <p className="text-xs text-gray-700">
                      Donor ID: {delivery.matchDetails.donorId.substring(0, 8)}
                      ...
                    </p>
                    <p className="text-xs text-gray-700">
                      Test Date:{" "}
                      {new Date(
                        delivery.matchDetails.testDateTime
                      ).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
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
            <RecipientProfile
              recipient={selectedRecipient}
              getPersonalData={getPersonalData}
            />
          </div>

          {/* Right Panel (Lab Reports, Matches, Timeline) */}
          <div className="md:col-span-2">
            {/* Lab Reports */}
            <LabReports labReports={labReports} loading={loadingLabReports} />

            {/* Organ Matches */}
            <div className="mt-6">
              <OrganMatches
                matches={matches}
                loading={matchLoading}
                error={matchError}
                onRefresh={handleFindMatches}
                onRequestNewOrgans={handleRequestNewOrgans}
                selectedMatch={selectedMatch}
                onSelectMatch={setSelectedMatch}
                onRequestOrgan={handleRequestOrgan}
                requestLoading={requestLoading}
                requestSuccess={requestSuccess}
                recipientId={selectedRecipient.recipientId}
              />
            </div>

            {/* Activity Timeline */}
            <div className="mt-6">
              <ActivityTimeline requestSuccess={requestSuccess} />
            </div>

            {/* Delivery Tracking Section */}
            <div className="mt-6 bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="p-4">{renderDeliveryTrackers()}</div>
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
        <div className="inline-flex justify-content-center">
          <h1 className="text-2xl font-bold text-gray-800 ">
            Organ Recipients
          </h1>
          <Link
            href="/doctor/create"
            className="mx-4  px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Create New
          </Link>
        </div>
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
            <RecipientCard
              key={recipient.recipientId || index}
              recipient={recipient}
              onClick={handleRecipientClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}
