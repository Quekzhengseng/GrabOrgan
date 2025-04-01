import { useState } from "react";
import { Eye, EyeOff, User } from "lucide-react";
import { formatDate } from "@/utils/recipientUtils";

export default function RecipientProfile({ recipient, getPersonalData }) {
  // State to track whether the unmasked data is displayed
  const [isEyeActive, setIsEyeActive] = useState(false);
  // State for displaying the passcode modal
  const [showPasscodeModal, setShowPasscodeModal] = useState(false);
  // State for the passcode input value
  const [passcode, setPasscode] = useState("");
  // Data to display (masked by default; already provided via `recipient`)
  const [displayRecipient, setDisplayRecipient] = useState(recipient);

  // Close the modal and reset the passcode field
  const handleCloseModal = () => {
    setShowPasscodeModal(false);
    setPasscode("");
  };
  const handleToggleEye = async () => {
    if (isEyeActive) {
      // If already unmasked, revert to masked view
      setIsEyeActive(false);
      setDisplayRecipient(recipient); // back to masked version
    } else {
      // Show modal to enter passcode before unmasking
      setShowPasscodeModal(true);
    }
  };
  const handlePasscodeSubmit = async (e) => {
    e.preventDefault();
    const updatedData = await getPersonalData(recipient.recipientId, passcode);
    if (updatedData) {
      setDisplayRecipient(updatedData); // update display to unmasked
      setIsEyeActive(true);
    }
    handleCloseModal();
  };

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-green-600 text-white p-6">
        <h1 className="text-2xl font-bold">Recipient Profile</h1>
        <p className="mt-2 flex items-center text-green-100">
          <User className="h-4 w-4 mr-2" />
          ID: {recipient.recipientId || "Not assigned"}
        </p>
      </div>

      <div className="p-6">
        {/* PERSONAL INFORMATION */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">
              Personal Information
            </h2>
            <button
              onClick={handleToggleEye}
              className="text-gray-500 hover:text-gray-700"
              aria-label="Enter Passcode"
            >
              {isEyeActive ? (
                <Eye className="h-5 w-5" />
              ) : (
                <EyeOff className="h-5 w-5" />
              )}
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Full Name</p>
              <p className="font-medium text-gray-800">
                {displayRecipient.firstName} {displayRecipient.lastName}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Date of Birth</p>
              <p className="font-medium text-gray-800">
                {displayRecipient.dateOfBirth}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="font-medium text-gray-800">
                {displayRecipient.email}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">NRIC</p>
              <p className="font-medium text-gray-800">
                {displayRecipient.nric}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Address</p>
              <p className="font-medium text-gray-800">
                {displayRecipient.address}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Gender</p>
              <p className="font-medium text-gray-800">{recipient.gender}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Blood Type</p>
              <p className="font-medium text-gray-800">{recipient.bloodType}</p>
            </div>
          </div>
        </div>

        {/* MEDICAL INFORMATION (unchanged) */}
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4 text-gray-800">
            Medical Information
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Organs Needed</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {recipient.organsNeeded && recipient.organsNeeded.length > 0 ? (
                  recipient.organsNeeded.map((organ, index) => (
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
                {recipient.allergies && recipient.allergies.length > 0 ? (
                  recipient.allergies.map((allergy, index) => (
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
              {recipient.medicalHistory &&
              recipient.medicalHistory.length > 0 ? (
                <ul className="mt-1 list-disc pl-5 text-gray-600">
                  {recipient.medicalHistory.map((item, index) => (
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
                              Diagnosed: {formatDate(item.dateDiagnosed)}
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
                  ))}
                </ul>
              ) : (
                <p className="text-gray-600">No medical history available</p>
              )}
            </div>
          </div>
        </div>

        {/* EMERGENCY CONTACT (unchanged) */}
        {displayRecipient.nokContact && (
          <div>
            <h2 className="text-xl font-bold mb-4 text-gray-800">
              Emergency Contact
            </h2>
            <div className="space-y-2 text-gray-600">
              <p>
                <span className="font-medium">Name:</span>{" "}
                {displayRecipient.nokContact.firstName}{" "}
                {displayRecipient.nokContact.lastName}
              </p>
              <p>
                <span className="font-medium">Relationship:</span>{" "}
                {displayRecipient.nokContact.relationship}
              </p>
              <p>
                <span className="font-medium">Phone:</span>{" "}
                {displayRecipient.nokContact.phone}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Passcode Modal */}
      {showPasscodeModal && (
        <div className="fixed inset-0 flex items-center justify-center backdrop-blur-sm bg-white/30 z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-sm w-full">
            <h3 className="text-lg font-bold mb-4">Enter Passcode</h3>
            <form onSubmit={handlePasscodeSubmit}>
              <input
                type="password"
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                placeholder="Enter passcode"
                className="w-full border border-gray-300 rounded px-3 py-2 mb-4"
              />
              <div className="flex justify-end">
                
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="mr-4 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
