// components/ActivityTimeline.js
import { Activity } from "lucide-react";

export default function ActivityTimeline({ requestSuccess }) {
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-green-600 text-white p-6">
        <h2 className="text-2xl font-bold">Recipient Activity</h2>
      </div>

      <div className="p-6">
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

          <div className="space-y-8">
            <div className="relative pl-10">
              <div className="absolute left-0 top-1 rounded-full bg-green-500 p-2">
                <Activity className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-medium text-gray-800">
                  Added to recipient list
                </p>
                <p className="text-sm text-gray-500">March 20, 2025</p>
              </div>
            </div>

            <div className="relative pl-10">
              <div className="absolute left-0 top-1 rounded-full bg-blue-500 p-2">
                <Activity className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-medium text-gray-800">Lab tests completed</p>
                <p className="text-sm text-gray-500">March 21, 2025</p>
              </div>
            </div>

            <div className="relative pl-10">
              <div className="absolute left-0 top-1 rounded-full bg-yellow-500 p-2">
                <Activity className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-medium text-gray-800">
                  Added to donor match queue
                </p>
                <p className="text-sm text-gray-500">March 22, 2025</p>
              </div>
            </div>

            {requestSuccess && (
              <div className="relative pl-10">
                <div className="absolute left-0 top-1 rounded-full bg-red-500 p-2">
                  <Activity className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-800">
                    Organ transplant requested
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date().toLocaleDateString()}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
