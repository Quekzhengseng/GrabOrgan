// components/RecipientCard.js
import { Calendar, User, Heart } from "lucide-react";
import { formatDate, getUrgencyColor } from "@/utils/recipientUtils";

export default function RecipientCard({ recipient, onClick }) {
  return (
    <div
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
      onClick={() => onClick(recipient)}
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
            <span>{recipient.dateOfBirth}</span>
          </div>

          <div className="flex items-center">
            <User className="h-4 w-4 text-green-600 mr-2" />
            <span>{recipient.gender || "Not specified"}</span>
          </div>

          <div className="flex items-center">
            <Heart className="h-4 w-4 text-green-600 mr-2" />
            <span>Blood Type: {recipient.bloodType || "Not specified"}</span>
          </div>
        </div>

        {recipient.organsNeeded && recipient.organsNeeded.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-1">Needed Organs:</p>
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
  );
}
