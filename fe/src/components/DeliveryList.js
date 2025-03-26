// components/DeliveryList.js
import { Loader2 } from "lucide-react";
import DeliveryCard from "./DeliveryCard";

export default function DeliveryList({
  deliveries,
  loading,
  error,
  onTrackDelivery,
  onDeleteDelivery,
  searchTerm,
  filterStatus,
  setSearchTerm,
  setFilterStatus,
}) {
  return (
    <>
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-green-500" />
          <span className="ml-2 text-gray-600">Loading deliveries...</span>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      ) : deliveries.length === 0 ? (
        <div className="bg-gray-100 p-6 text-center rounded">
          <p className="text-gray-700">
            No delivery orders found matching your criteria.
          </p>
          {(searchTerm || filterStatus !== "All") && (
            <button
              onClick={() => {
                setSearchTerm("");
                setFilterStatus("All");
              }}
              className="mt-2 text-green-600 hover:text-green-800"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {deliveries.map((delivery, index) => (
            <DeliveryCard
              key={delivery.orderID || index}
              delivery={delivery}
              onTrack={onTrackDelivery}
              onDelete={onDeleteDelivery}
            />
          ))}
        </div>
      )}
    </>
  );
}
