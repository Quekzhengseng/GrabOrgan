import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { formatDate } from "@/utils/recipientUtils";
import TransplantDateTimePicker from "./TransplantDateTime";
import { confirmMatch, initiateMatch } from "@/utils/recipientUtils";

export default function OrganMatches({
  matches,
  loading,
  error,
  onRefresh,
  selectedMatch,
  onSelectMatch,
  requestLoading,
  requestSuccess,
  recipientId,
}) {
  // Dialog state
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmedMatch, setConfirmedMatch] = useState(null);
  const [transplantDateTime, setTransplantDateTime] = useState("");
  const [selectedStartHospital, setSelectedStartHospital] = useState("");
  const [selectedEndHospital, setSelectedEndHospital] = useState("");
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const email = sessionStorage.getItem("userEmail");
    setUserEmail(email);
  }, []);

  const handleOpenConfirmDialog = (match) => {
    setConfirmedMatch(match);
    setShowConfirmDialog(true);
  };

  const handleCloseConfirmDialog = () => {
    setShowConfirmDialog(false);
    setConfirmedMatch(null);
  };

  // Trigger your confirmMatch endpoint with the relevant fields
  const handleConfirmMatch = () => {
    if (!confirmedMatch) return;
    const utcDateTime = new Date(transplantDateTime).toISOString();

    // Build the body fields you want to send
    const payload = {
      organType:
        confirmedMatch.organType ?? confirmedMatch.organId?.split("-")[0],
      doctorId: userEmail,
      transplantDateTime: utcDateTime,
      startHospital: selectedStartHospital,
      endHospital: selectedEndHospital,
      matchId: confirmedMatch.matchId,
      remarks: confirmedMatch.remarks ?? "",
    };

    console.log(payload);
    confirmMatch(payload);

    // Close the dialog
    setShowConfirmDialog(false);
    setConfirmedMatch(null);
  };

  const handleInitiateMatch = () =>{
    if (!recipientId) return;
    initiateMatch(recipientId)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-green-600 text-white p-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold">Organ Matches</h2>
        <div className="flex gap-2">
          {matches.length === 0 && !loading && (
            <button
              onClick={handleInitiateMatch}
              className="px-4 py-2 bg-white text-orange-600 rounded-md hover:bg-gray-100 transition-colors flex items-center"
              disabled={requestLoading}
            >
              {requestLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Requesting...
                </>
              ) : (
                "Find Matches"
              )}
            </button>
          )}
          <button
            onClick={() => onRefresh(recipientId)}
            className="px-4 py-2 bg-white text-green-600 rounded-md hover:bg-gray-100 transition-colors flex items-center"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Finding Matches...
              </>
            ) : (
              "Refresh Matches"
            )}
          </button>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-green-500" />
            <span className="ml-2 text-gray-600">
              Finding potential matches...
            </span>
          </div>
        ) : error ? (
          <div className="bg-red-100 p-4 rounded-md text-red-700">
            <p className="font-bold">Error finding matches</p>
            <p>{error}</p>
          </div>
        ) : matches.length === 0 ? (
          <div className="bg-gray-100 p-6 text-center rounded">
            <p className="text-gray-700">
              No potential organ matches found. Click "Find Matches" to search
              for compatible donors.
            </p>
          </div>
        ) : (
          <div>
            {requestSuccess && (
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                <p className="font-bold">Success!</p>
                <p>
                  Organ transplant has been requested successfully. The medical
                  team will be notified.
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
                    selectedMatch && selectedMatch.matchId === match.matchId
                      ? "border-green-500 bg-green-50"
                      : "border-gray-200 hover:border-green-300"
                  }`}
                  onClick={() => onSelectMatch(match)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium text-gray-800">
                      {match.organId.split("-")[0] || "Organ"}
                    </span>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                      {match.numOfHLA}/6 HLA Match
                    </span>
                  </div>

                  <div className="text-sm space-y-1 text-gray-600">
                    <p>
                      Donor ID: {match.donorId?.substring(0, 8) || "Unknown"}
                    </p>
                    {/* <p>
                      Donor: {match.donor_details?.first_name || "Unknown"}{" "}
                      {match.donor_details?.last_name || ""}
                      {match.donor_details?.gender &&
                        ` (${match.donor_details.gender})`}
                    </p>
                    <p>
                      Blood Type: {match.donor_details?.blood_type || "Unknown"}
                    </p> */}
                    <p className="text-xs text-gray-500">
                      Match Date: {formatDate(match.testDateTime)}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {selectedMatch && (
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => handleOpenConfirmDialog(selectedMatch)}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center"
                  disabled={requestLoading}
                >
                  {requestLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing Request...
                    </>
                  ) : (
                    "Confirm Match"
                  )}
                </button>
              </div>
            )}
            {/* --- DIALOG / MODAL START --- */}
            {showConfirmDialog && confirmedMatch && (
              <div className="fixed inset-0 flex items-center justify-center z-50">
                {/* Overlay */}
                <div
                  className="absolute inset-0 backdrop-blur-sm bg-white/300"
                  onClick={handleCloseConfirmDialog}
                />

                {/* Modal box */}
                <div className="relative bg-white p-6 rounded-md shadow-md w-full max-w-lg">
                  <h2 className="text-xl font-bold mb-4">
                    Confirm Match Details
                  </h2>

                  <form
                    onSubmit={(e) => e.preventDefault()}
                    className="space-y-4"
                  >
                    {/* Example of read-only fields */}
                    <div>
                      <label className="block text-sm font-semibold mb-1">
                        Organ Type
                      </label>
                      <input
                        type="text"
                        readOnly
                        value={
                          confirmedMatch.organType ??
                          confirmedMatch.organId?.split("-")[0] ??
                          ""
                        }
                        className="w-full border border-gray-300 bg-gray-100 text-gray-500 rounded p-2 cursor-not-allowed"
                      />
                    </div>

                    <TransplantDateTimePicker
                      initialDateTime={
                        confirmedMatch.transplantDateTime ??
                        confirmedMatch.testDateTime
                      }
                      onChange={(value) => setTransplantDateTime(value)}
                    />

                    <div>
                      <div className="mt-4">
                        <label className="block text-sm font-semibold mb-1">
                          Start Hospital
                        </label>
                        <select
                          className="w-full border rounded p-2"
                          value={selectedStartHospital}
                          onChange={(e) =>
                            setSelectedStartHospital(e.target.value)
                          }
                        >
                          <option value="">Select Hospital</option>
                          {[
                            "CGH",
                            "SGH",
                            "TTSH",
                            "SKGH",
                            "NUH",
                            "KTPH",
                            "NTFGH",
                          ].map((hospital) => (
                            <option key={hospital} value={hospital}>
                              {hospital}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div>
                      <div className="mt-4">
                        <label className="block text-sm font-semibold mb-1">
                          End Hospital
                        </label>
                        <select
                          className="w-full border rounded p-2"
                          value={selectedEndHospital}
                          onChange={(e) =>
                            setSelectedEndHospital(e.target.value)
                          }
                        >
                          <option value="">Select Hospital</option>
                          {[
                            "CGH",
                            "SGH",
                            "TTSH",
                            "SKGH",
                            "NUH",
                            "KTPH",
                            "NTFGH",
                          ].map((hospital) => (
                            <option key={hospital} value={hospital}>
                              {hospital}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Example of an editable remarks field */}
                    <div>
                      <label className="block text-sm font-semibold mb-1">
                        Remarks
                      </label>
                      <textarea
                        className="w-full border rounded p-2"
                        placeholder="Any notes or remarks?"
                        onChange={(e) =>
                          setConfirmedMatch((prev) => ({
                            ...prev,
                            remarks: e.target.value,
                          }))
                        }
                        value={confirmedMatch.remarks ?? ""}
                      />
                    </div>
                  </form>

                  {/* Buttons */}
                  <div className="mt-6 flex justify-end gap-2">
                    <button
                      onClick={handleCloseConfirmDialog}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmMatch}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Confirm
                    </button>
                  </div>
                </div>
              </div>
            )}
            {/* --- DIALOG / MODAL END --- */}
          </div>
        )}
      </div>
    </div>
  );
}
