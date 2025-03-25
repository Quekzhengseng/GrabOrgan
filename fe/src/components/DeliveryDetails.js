// components/DeliveryDetails.js
import { Package, MapPin, Calendar, Clock, Truck } from "lucide-react";
import { formatDeliveryDate, getDeliveryStatusColor } from "@/utils/routeUtils";

export default function DeliveryDetails({ delivery }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Delivery Details</h2>

      <div className="space-y-4">
        <div>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDeliveryStatusColor(
              delivery.status
            )}`}
          >
            {delivery.status}
          </span>
        </div>

        <div className="flex items-start">
          <Package className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
          <div>
            <p className="font-medium text-gray-900">Order ID</p>
            <p className="text-gray-600">{delivery.orderID}</p>
          </div>
        </div>

        <div className="flex items-start">
          <MapPin className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
          <div>
            <p className="font-medium text-gray-900">Pickup Location</p>
            <p className="text-gray-600">{delivery.pickup}</p>
          </div>
        </div>

        <div className="flex items-start">
          <Calendar className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
          <div>
            <p className="font-medium text-gray-900">Pickup Time</p>
            <p className="text-gray-600">
              {formatDeliveryDate(delivery.pickup_time)}
            </p>
          </div>
        </div>

        <div className="flex items-start">
          <MapPin className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
          <div>
            <p className="font-medium text-gray-900">Destination</p>
            <p className="text-gray-600">{delivery.destination}</p>
          </div>
        </div>

        {delivery.destination_time && (
          <div className="flex items-start">
            <Clock className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
            <div>
              <p className="font-medium text-gray-900">Destination Time</p>
              <p className="text-gray-600">
                {formatDeliveryDate(delivery.destination_time)}
              </p>
            </div>
          </div>
        )}

        <div className="flex items-start">
          <Truck className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
          <div>
            <p className="font-medium text-gray-900">Driver ID</p>
            <p className="text-gray-600">
              {delivery.driverID || "Not assigned"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
