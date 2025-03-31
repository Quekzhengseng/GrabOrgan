// File: app/doctor/page.js
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
import {
  fetchRecipients,
  fetchLabReports,
  findOrganMatches,
  createOrganOrder,
  createDeliveryRequest,
  requestNewOrgans,
  getPersonalData,
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

  // Handle click on a recipient to view details
  const handleRecipientClick = (recipient) => {
    setSelectedRecipient(recipient);
    setSelectedMatch(null);
    setMatches([]);
    setMatchError(null);
    setRequestSuccess(false);

    if (recipient.recipientId) {
      // Fetch lab reports
      loadLabReports(recipient.recipientId);

      // Automatically find matches for this recipient
      handleFindMatches(recipient.recipientId);
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

  const deliveryInfo = (deliveryData) => {
    if (deliveryData) {
      return <DeliveryMapbox deliveryData={deliveryData} />;
    } else {
      return "Tough";
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

            {/* Delivery Map Section */}
            <div className="mt-6 bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="lg:col-span-2">
                {/* Insert the map component with delivery data */}
                {deliveryInfo("Test")}
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
