// File: app/delivery/page.js
"use client";

import { useState, useEffect } from "react";
import {
  Loader2,
  Truck,
  ArrowLeft,
  Package,
  MapPin,
  Calendar,
  Clock,
  ChevronRight,
  Search,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import DeliveryMapbox from "@/components/DeliveryMapbox"; // Import the map component from components directory

export default function DeliveryOrdersPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [filteredDeliveries, setFilteredDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("Assigned");
  const router = useRouter();
  const searchParams = useSearchParams();

  // Check if we have an orderId in the URL to display details
  const orderIdParam = searchParams?.get("orderId");

  useEffect(() => {
    async function fetchDeliveries() {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:5002/deliveryinfo");

        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.code === 200 && data.data) {
          // Convert the object of deliveries into an array
          const deliveryArray = Object.values(data.data);
          setDeliveries(deliveryArray);
          setFilteredDeliveries(deliveryArray);

          // If we have an orderId in the URL, find and select that delivery
          if (orderIdParam) {
            const selectedDelivery = deliveryArray.find(
              (delivery) => delivery.orderID === orderIdParam
            );
            if (selectedDelivery) {
              setSelectedDelivery(selectedDelivery);
            }
          }
        } else {
          throw new Error("Invalid response format");
        }
      } catch (err) {
        console.error("Error fetching deliveries:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDeliveries();
  }, [orderIdParam]);

  // Apply filters when search term or filter status changes
  useEffect(() => {
    if (!deliveries.length) return;

    let filtered = [...deliveries];

    // Filter by status
    if (filterStatus !== "All") {
      filtered = filtered.filter(
        (delivery) => delivery.status === filterStatus
      );
    }

    // Filter by search term
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (delivery) =>
          delivery.orderID?.toLowerCase().includes(searchLower) ||
          delivery.pickup?.toLowerCase().includes(searchLower) ||
          delivery.destination?.toLowerCase().includes(searchLower) ||
          delivery.driverID?.toLowerCase().includes(searchLower)
      );
    }

    setFilteredDeliveries(filtered);
  }, [searchTerm, filterStatus, deliveries]);

  // Helper function to get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case "Awaiting pickup":
        return "bg-yellow-100 text-yellow-800";
      case "In progress":
        return "bg-blue-100 text-blue-800";
      case "Completed":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";

    // Parse the date format "YYYYMMDD HH:MM:SS AM/PM"
    const [datePart, timePart, ampm] = dateString.split(" ");

    // Format YYYYMMDD to YYYY-MM-DD
    const year = datePart.substring(0, 4);
    const month = datePart.substring(4, 6);
    const day = datePart.substring(6, 8);

    return `${year}-${month}-${day} ${timePart} ${ampm}`;
  };

  // Handle track delivery button click
  const handleTrackDelivery = (delivery, e) => {
    e.stopPropagation(); // Prevent triggering the card click
    setSelectedDelivery(delivery);
    // Update URL with orderId but without refreshing the page
    router.push(`/delivery?orderId=${delivery.orderID}`, { scroll: false });
  };

  // Go back to delivery list
  const handleBackClick = () => {
    setSelectedDelivery(null);
    router.push("/delivery", { scroll: false });
  };

  const handleDeliveryDelete = async (delivery, e) => {
    e.stopPropagation(); // Prevent triggering the card click
    try {
      console.log(delivery.orderID);
      const response = await fetch(
        `http://localhost:5002/deliveryinfo/${delivery.orderID}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status: "Deleted" }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update delivery status");
      }

      alert("Delivery deleted successfully!");
      // Remove the deleted delivery from the list
      const updatedDeliveries = deliveries.filter(
        (d) => d.orderID !== delivery.orderID
      );
      setDeliveries(updatedDeliveries);
      setFilteredDeliveries(updatedDeliveries);
    } catch (error) {
      console.error("Error deleting delivery:", error);
      alert("Error deleting delivery.");
    }
  };

  // Get unique statuses for the filter dropdown
  const getStatusOptions = () => {
    if (!deliveries.length) return ["All"];
    const statuses = deliveries.map((delivery) => delivery.status);
    return ["All", ...new Set(statuses)];
  };

  // Clear search field
  const clearSearch = () => {
    setSearchTerm("");
  };

  // Render map view when a delivery is selected
  if (selectedDelivery) {
    return (
      <div className="container mx-auto px-4 py-6">
        <button
          onClick={handleBackClick}
          className="flex items-center text-green-600 hover:text-green-800 mb-6 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to all deliveries
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4 text-gray-800">
                Delivery Details
              </h2>

              <div className="space-y-4">
                <div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      selectedDelivery.status
                    )}`}
                  >
                    {selectedDelivery.status}
                  </span>
                </div>

                <div className="flex items-start">
                  <Package className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Order ID</p>
                    <p className="text-gray-600">{selectedDelivery.orderID}</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <MapPin className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Pickup Location</p>
                    <p className="text-gray-600">{selectedDelivery.pickup}</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <Calendar className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Pickup Time</p>
                    <p className="text-gray-600">
                      {formatDate(selectedDelivery.pickup_time)}
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <MapPin className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Destination</p>
                    <p className="text-gray-600">
                      {selectedDelivery.destination}
                    </p>
                  </div>
                </div>

                {selectedDelivery.destination_time && (
                  <div className="flex items-start">
                    <Clock className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900">
                        Destination Time
                      </p>
                      <p className="text-gray-600">
                        {formatDate(selectedDelivery.destination_time)}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-start">
                  <Truck className="h-5 w-5 text-green-600 mr-3 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Driver ID</p>
                    <p className="text-gray-600">
                      {selectedDelivery.driverID || "Not assigned"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            {/* Insert the map component with delivery data */}
            <DeliveryMapbox deliveryData={selectedDelivery} />
          </div>
        </div>
      </div>
    );
  }

  // Render the list of deliveries (default view)
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Delivery Orders</h1>
        <Link
          href="/"
          className="px-4 py-2 bg-gray-100 rounded-md text-gray-600 hover:bg-gray-200 transition-colors"
        >
          Logout
        </Link>
      </div>

      {/* Search and Filter Section */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search Box */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Box
            </label>
            <input
              type="text"
              placeholder="Search by order ID, location, driver..."
              className="block w-full pl-10 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                onClick={clearSearch}
                className="absolute  inset-y-0 right-0 pr-3 flex items-center"
              >
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600 relative top-[-10px]" />
              </button>
            )}
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Status
            </label>
            <select
              className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              {getStatusOptions().map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          {/* Results Summary */}
          <div className="flex items-end">
            <p className="text-gray-600">
              Showing {filteredDeliveries.length} of {deliveries.length}{" "}
              deliveries
            </p>
          </div>
        </div>
      </div>

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
      ) : filteredDeliveries.length === 0 ? (
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
          {filteredDeliveries.map((delivery, index) => (
            <div
              key={delivery.orderID || index}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
              onClick={(e) => handleTrackDelivery(delivery, e)}
            >
              <div className="p-5">
                <div className="flex justify-between items-start mb-3">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      delivery.status
                    )}`}
                  >
                    {delivery.status}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatDate(delivery.pickup_time).split(" ")[0]}
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
                <div onClick={(e) => handleDeliveryDelete(delivery, e)}>
                  <span className="text-red-600 text-sm font-medium flex items-center">
                    Delete Delivery
                  </span>
                </div>
                <div onClick={(e) => handleTrackDelivery(delivery, e)}>
                  <span className="text-green-600 text-sm font-medium flex items-center">
                    Track delivery <ChevronRight className="h-4 w-4 ml-1" />
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
