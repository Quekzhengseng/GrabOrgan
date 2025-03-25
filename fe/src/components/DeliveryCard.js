// components/DeliveryCard.js
import { MapPin, Truck, ChevronRight } from "lucide-react";
import { formatDeliveryDate, getDeliveryStatusColor } from "@/utils/routeUtils";

export default function DeliveryCard({ delivery, onTrack, onDelete }) {
  // Handle track delivery button click
  const handleTrackDelivery = (e) => {
    e.stopPropagation(); // Prevent triggering the card click
    onTrack(delivery);
  };

  // Handle delete delivery button click
  const handleDeleteDelivery = (e) => {
    e.stopPropagation(); // Prevent triggering the card click
    onDelete(delivery);
  };

  return (
    <div
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
      onClick={handleTrackDelivery}
    >
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDeliveryStatusColor(
              delivery.status
            )}`}
          >
            {delivery.status}
          </span>
          <span className="text-xs text-gray-500">
            {formatDeliveryDate(delivery.pickup_time).split(" ")[0]}
          </span>
        </div>

        <h3 className="font-bold text-gray-800 mb-3 truncate">
          Order ID: {delivery.orderID}
        </h3>

        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center">
            <MapPin className="h-4 w-4 text-green-600 mr-2" />
            <span className="truncate">From: {delivery.pickup}</span>
          </div>

          <div className="flex items-center">
            <MapPin className="h-4 w-4 text-green-600 mr-2" />
            <span className="truncate">To: {delivery.destination}</span>
          </div>

          {delivery.driverID && (
            <div className="flex items-center">
              <Truck className="h-4 w-4 text-green-600 mr-2" />
              <span>Driver: {delivery.driverID}</span>
            </div>
          )}
        </div>
      </div>

      <div className="border-t px-5 py-3 bg-gray-50 flex justify-between items-center">
        <div onClick={handleDeleteDelivery}>
          <span className="text-red-600 text-sm font-medium flex items-center">
            Delete Delivery
          </span>
        </div>
        <div onClick={handleTrackDelivery}>
          <span className="text-green-600 text-sm font-medium flex items-center">
            Track delivery <ChevronRight className="h-4 w-4 ml-1" />
          </span>
        </div>
      </div>
    </div>
  );
}
