// components/RecipientProfile.js
import { User } from "lucide-react";
import { formatDate } from "@/utils/recipientUtils";

export default function RecipientProfile({ recipient }) {
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-green-600 text-white p-6">
        <h1 className="text-2xl font-bold">Recipient Profile</h1>
        <p className="mt-2 flex items-center text-green-100">
          <User className="h-4 w-4 mr-2" />
          ID: {recipient.recipientId || "Not assigned"}
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
                {recipient.firstName} {recipient.lastName}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Date of Birth</p>
              <p className="font-medium text-gray-800">
                {formatDate(recipient.dateOfBirth)}
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

        {recipient.nokContact && (
          <div>
            <h2 className="text-xl font-bold mb-4 text-gray-800">
              Emergency Contact
            </h2>
            <div className="space-y-2 text-gray-600">
              <p>
                <span className="font-medium">Name:</span>{" "}
                {recipient.nokContact.firstName} {recipient.nokContact.lastName}
              </p>
              <p>
                <span className="font-medium">Relationship:</span>{" "}
                {recipient.nokContact.relationship}
              </p>
              <p>
                <span className="font-medium">Phone:</span>{" "}
                {recipient.nokContact.phone}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
