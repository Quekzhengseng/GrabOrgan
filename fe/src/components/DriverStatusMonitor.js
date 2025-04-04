// components/DriverStatusMonitor.js
import { useState, useEffect } from "react";
import { Bell, BellOff } from "lucide-react";
import { getSpecificDelivery, getDriver } from "@/utils/routeUtils";

export default function DriverStatusMonitor({ driverId }) {
  const [isPolling, setIsPolling] = useState(true);
  const [statusMessage, setStatusMessage] = useState("");
  const [hasAlert, setHasAlert] = useState(false);

  // Function to poll driver status
  useEffect(() => {
    let intervalId;

    if (isPolling && driverId) {
      // Initial check
      checkDriverStatus();

      // Set up interval to check every minute
      intervalId = setInterval(checkDriverStatus, 10000);
      setStatusMessage(`Monitoring driver ${driverId} status...`);
    } else {
      setStatusMessage("");
    }

    // Cleanup on unmount or when polling is stopped
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isPolling, driverId]);

  // Function to fetch driver data
  const checkDriverStatus = async () => {
    if (!driverId) return;

    try {
      // Use the getDriver utility function instead of direct fetch
      const data = await getDriver(driverId);

      console.log("Driver data retrieved:", data);

      if (data.awaitingAcknowledgement === true) {
        setHasAlert(true);
        // Get the delivery information when acknowledgement is needed
        const deliveryData = await getSpecificDelivery(
          data.currentAssignedDeliveryId
        );
        console.log("Delivery data retrieved:", deliveryData);

        if (deliveryData.pickup == data.stationed_hospital) {
          console.log("same");
          setStatusMessage(
            `Alert: Driver ${driverId} needs to acknowledge delivery #${data.currentAssignedDeliveryId}!`
          );
        } else {
          console.log("different");
          setStatusMessage(
            `Alert: Driver ${driverId} needs to acknowledge delivery #${data.currentAssignedDeliveryId}! 
            <br> Origin Hospital is different. Will need driver to travel to ${deliveryData.pickup}.`
          );
        }
      }
    } catch (error) {
      console.error("Error checking driver status:", error);
      setStatusMessage(`Error: ${error.message}`);
    }
  };

  // Toggle polling on/off
  const togglePolling = () => {
    setIsPolling(!isPolling);
    setHasAlert(false);
  };

  // Acknowledge alert
  const acknowledgeAlert = () => {
    setHasAlert(false);
    setStatusMessage(`Monitoring driver ${driverId} status...`);
    // Insert new utill function to call back select driver to update
  };

  return (
    <div className="mb-6 bg-white rounded-lg shadow p-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Driver Status Monitor
        </label>
        <div
          className={`block w-full p-3 border ${
            hasAlert ? "border-red-500 bg-red-50" : "border-gray-300"
          } rounded-md min-h-12 relative`}
        >
          {statusMessage ? (
            <div className="flex justify-between items-center">
              <span
                className={
                  hasAlert ? "text-red-600 font-medium" : "text-gray-600"
                }
              >
                {statusMessage}
              </span>
              {hasAlert && (
                <button
                  onClick={acknowledgeAlert}
                  className="px-3 py-1 bg-red-600 text-white rounded-md text-sm hover:bg-red-700"
                >
                  Acknowledge
                </button>
              )}
            </div>
          ) : (
            <span className="text-gray-400">Not monitoring driver status</span>
          )}
          <button
            onClick={togglePolling}
            className={`absolute right-3 bottom-3 p-1 rounded-full ${
              isPolling
                ? "bg-green-100 text-green-600"
                : "bg-gray-100 text-gray-600"
            }`}
            title={isPolling ? "Stop monitoring" : "Start monitoring"}
          >
            {isPolling ? (
              <Bell className="h-5 w-5" />
            ) : (
              <BellOff className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
