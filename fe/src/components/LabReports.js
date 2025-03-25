// components/LabReports.js
import { Loader2 } from "lucide-react";
import { formatDate } from "@/utils/recipientUtils";

export default function LabReports({ labReports, loading }) {
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-green-600 text-white p-6">
        <h2 className="text-2xl font-bold">Lab Reports</h2>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-green-500" />
            <span className="ml-2 text-gray-600">Loading lab reports...</span>
          </div>
        ) : labReports.length === 0 ? (
          <div className="bg-gray-100 p-6 text-center rounded">
            <p className="text-gray-700">
              No lab reports found for this recipient.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {labReports.map((report, index) => (
              <div
                key={report.uuid || index}
                className="border rounded-lg overflow-hidden"
              >
                <div className="bg-gray-50 px-4 py-3 border-b">
                  <h3 className="font-bold text-lg text-gray-800">
                    {report.reportName}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {formatDate(report.dateOfReport)}
                  </p>
                </div>

                <div className="p-4">
                  <div className="mb-4">
                    <p className="font-medium text-gray-700">Test Type:</p>
                    <p className="text-gray-600">
                      {report.testType || "Not specified"}
                    </p>
                  </div>

                  {report.results && (
                    <div>
                      <p className="font-medium text-gray-700 mb-2">Results:</p>
                      <div className="bg-gray-50 rounded-lg p-4">
                        {Object.entries(report.results).map(([key, value]) => (
                          <div
                            key={key}
                            className="grid grid-cols-2 mb-2 pb-2 border-b border-gray-200 last:border-0"
                          >
                            <span className="text-sm font-medium text-gray-500 capitalize">
                              {key}
                            </span>
                            <span className="text-gray-800">
                              {typeof value === "object"
                                ? JSON.stringify(value)
                                : value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {report.comments && (
                    <div className="mt-4">
                      <p className="font-medium text-gray-700">Comments:</p>
                      <p className="text-gray-600">{report.comments}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
