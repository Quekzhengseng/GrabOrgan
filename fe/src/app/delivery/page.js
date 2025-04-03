// File: app/delivery/page.js
"use client";

import { useState, useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import DeliveryMapbox from "@/components/DeliveryMapbox";
import DeliveryDetails from "@/components/DeliveryDetails";
import SearchAndFilter from "@/components/SearchAndFilter";
import DeliveryList from "@/components/DeliveryList";
import DriverStatusMonitor from "@/components/DriverStatusMonitor";
import { fetchDeliveries, deleteDelivery } from "@/utils/routeUtils";

export default function DeliveryOrdersPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [filteredDeliveries, setFilteredDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("All");
  const [id, setId] = useState(null);
  const router = useRouter();
  const searchParams = useSearchParams();

  // Check if we have an orderId in the URL to display details
  const orderIdParam = searchParams?.get("orderId");
  const driverId = searchParams?.get("id");

  // Set the driver ID from URL parameters
  useEffect(() => {
    if (driverId) {
      setId(driverId);
      console.log("Driver ID set from URL:", driverId);
    }
  }, [driverId]);

  useEffect(() => {
    async function loadDeliveries() {
      try {
        setLoading(true);
        const allDeliveryData = await fetchDeliveries();

        let deliveryData = [];

        for (let i = 0; i < allDeliveryData.length; i++) {
          if (
            (allDeliveryData[i].driverId == id &&
              allDeliveryData[i].status == "Assigned") ||
            allDeliveryData[i].status == "In Progress"
          ) {
            deliveryData.push(allDeliveryData[i]);
          }
        }

        setDeliveries(deliveryData);
        setFilteredDeliveries(deliveryData);

        // If we have an orderId in the URL, find and select that delivery
        if (orderIdParam) {
          const selectedDelivery = deliveryData.find(
            (delivery) => delivery.orderID === orderIdParam
          );
          if (selectedDelivery) {
            setSelectedDelivery(selectedDelivery);
          }
        }
      } catch (err) {
        console.error("Error fetching deliveries:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadDeliveries();
  }, [id, orderIdParam]);

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

  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const email = sessionStorage.getItem("userEmail");
    setUserEmail(email);
  }, []);
  // console.log("Driver Page:", userEmail);

  // Handle track delivery button click
  const handleTrackDelivery = (delivery) => {
    setSelectedDelivery(delivery);
    // Update URL with both driverId and orderId without refreshing the page
    router.push(`/delivery?id=${id}&orderId=${delivery.orderID}`, {
      scroll: false,
    });
  };

  // Go back to delivery list
  const handleBackClick = () => {
    setSelectedDelivery(null);
    router.push("/delivery", { scroll: false });
  };

  const handleDeliveryDelete = async (delivery) => {
    try {
      await deleteDelivery(delivery.orderID);
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
            <DeliveryDetails delivery={selectedDelivery} />
          </div>

          <div className="lg:col-span-2">
            {/* Insert the map component with delivery data */}
            <DeliveryMapbox
              deliveryId={orderIdParam}
              deliveryData={selectedDelivery}
            />
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

      {/* Driver Status Monitor */}
      <DriverStatusMonitor driverId={driverId} />

      {/* Search and Filter Section */}
      <SearchAndFilter
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
        statusOptions={getStatusOptions()}
        totalCount={deliveries.length}
        filteredCount={filteredDeliveries.length}
      />

      {/* Delivery List */}
      <DeliveryList
        deliveries={filteredDeliveries}
        loading={loading}
        error={error}
        onTrackDelivery={handleTrackDelivery}
        onDeleteDelivery={handleDeliveryDelete}
        searchTerm={searchTerm}
        filterStatus={filterStatus}
        setSearchTerm={setSearchTerm}
        setFilterStatus={setFilterStatus}
      />
    </div>
  );
}
