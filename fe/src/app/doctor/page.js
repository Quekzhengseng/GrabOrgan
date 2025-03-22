// File: app/doctor/page.js
"use client";

import { useState, useEffect } from "react";
import {
  Loader2,
  Calendar,
  FileText,
  ArrowLeft,
  ExternalLink,
  Filter,
  X,
} from "lucide-react";
import Link from "next/link";

export default function LabReportsDashboard() {
  const [labReports, setLabReports] = useState([]);
  const [filteredReports, setFilteredReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [testTypes, setTestTypes] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState("");
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  useEffect(() => {
    async function fetchLabReports() {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:5007/lab-reports");

        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.code === 200 && data.data) {
          setLabReports(data.data);
          setFilteredReports(data.data);

          // Extract unique test types for filter
          const uniqueTestTypes = [
            ...new Set(
              data.data.map((report) => report.testType).filter((type) => type)
            ),
          ];
          setTestTypes(uniqueTestTypes);
        } else {
          throw new Error("Invalid response format");
        }
      } catch (err) {
        console.error("Error fetching lab reports:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchLabReports();
  }, []);

  // Apply filter when selectedFilter changes
  useEffect(() => {
    if (selectedFilter === "") {
      setFilteredReports(labReports);
    } else {
      const filtered = labReports.filter(
        (report) => report.testType === selectedFilter
      );
      setFilteredReports(filtered);
    }
  }, [selectedFilter, labReports]);

  // Function to handle filter selection
  const handleFilterChange = (testType) => {
    setSelectedFilter(testType);
    setShowFilterMenu(false);
  };

  // Function to clear filter
  const clearFilter = () => {
    setSelectedFilter("");
  };

  // Function to determine status color based on results
  const getStatusColor = (results) => {
    if (!results) return "bg-gray-100";

    if (
      results.crossMatch === "Incompatible" ||
      results.antibodyScreen === "Positive"
    ) {
      return "bg-red-50 border-red-200";
    }

    if (results.comments && results.comments.includes("review")) {
      return "bg-yellow-50 border-yellow-200";
    }

    return "bg-green-50 border-green-200";
  };

  // Function to format date
  const formatDate = (dateString) => {
    if (!dateString) return "No date";

    const options = { year: "numeric", month: "short", day: "numeric" };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Render detail view when a report is selected
  if (selectedReport) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <button
          onClick={() => setSelectedReport(null)}
          className="flex items-center text-green-600 hover:text-green-800 mb-6 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to all reports
        </button>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-green-600 text-white p-6">
            <h1 className="text-2xl font-bold">{selectedReport.reportName}</h1>
            <div className="flex items-center mt-2 text-green-100">
              <Calendar className="h-4 w-4 mr-2" />
              <span>{formatDate(selectedReport.dateOfReport)}</span>
            </div>
          </div>

          <div className="p-6">
            <div className="grid gap-6 md:grid-cols-2 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-800 mb-2">Test Type</h3>
                <p>{selectedReport.testType || "Not specified"}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-800 mb-2">
                  Date of Report
                </h3>
                <p>{formatDate(selectedReport.dateOfReport)}</p>
              </div>
            </div>

            <div className="mb-6">
              <h2 className="text-xl font-bold mb-4 text-gray-800">
                Test Results
              </h2>
              <div className="bg-gray-50 rounded-lg p-4">
                {selectedReport.results ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {Object.entries(selectedReport.results).map(
                      ([key, value]) => (
                        <div key={key} className="border-b pb-2">
                          <h3 className="text-sm font-medium text-gray-500 capitalize">
                            {key}
                          </h3>
                          <p
                            className={`font-medium ${
                              key === "crossMatch" && value === "Incompatible"
                                ? "text-red-600"
                                : key === "antibodyScreen" &&
                                  value === "Positive"
                                ? "text-yellow-600"
                                : "text-gray-800"
                            }`}
                          >
                            {value}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500">No results available</p>
                )}
              </div>
            </div>

            {selectedReport.reportUrl && (
              <div className="mt-6">
                <a
                  href={selectedReport.reportUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Full Report PDF
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Render the card list view (default)
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Lab Reports</h1>
        <div className="flex items-center gap-2">
          {/* Filter dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowFilterMenu(!showFilterMenu)}
              className="flex items-center px-3 py-2 bg-green-100 text-green-800 rounded-md hover:bg-green-200 transition-colors"
            >
              <Filter className="h-4 w-4 mr-1" />
              {selectedFilter ? `Type: ${selectedFilter}` : "Filter by Type"}
            </button>

            {showFilterMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                <ul className="py-1">
                  <li>
                    <button
                      onClick={() => handleFilterChange("")}
                      className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                    >
                      All Types
                    </button>
                  </li>
                  {testTypes.map((type, index) => (
                    <li key={index}>
                      <button
                        onClick={() => handleFilterChange(type)}
                        className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                      >
                        {type}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Clear filter button - only show when filter is active */}
          {selectedFilter && (
            <button
              onClick={clearFilter}
              className="flex items-center px-2 py-2 text-gray-500 hover:text-gray-700"
              title="Clear filter"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          <Link
            href="/"
            className="px-4 py-2 bg-gray-100 rounded-md text-gray-600 hover:bg-gray-200 transition-colors"
          >
            Logout
          </Link>
        </div>
      </div>

      {/* Filter indicator */}
      {selectedFilter && (
        <div className="mb-4 flex items-center">
          <span className="text-sm text-gray-500">
            Filtered by test type:{" "}
            <span className="font-medium text-green-700">{selectedFilter}</span>
          </span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-green-500" />
          <span className="ml-2 text-gray-600">Loading reports...</span>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="bg-gray-100 p-6 text-center rounded">
          <p className="text-gray-700">
            {selectedFilter
              ? `No lab reports found with test type "${selectedFilter}".`
              : "No lab reports found."}
          </p>
          {selectedFilter && (
            <button
              onClick={clearFilter}
              className="mt-2 text-green-600 hover:text-green-800"
            >
              Clear filter
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredReports.map((report) => (
            <div
              key={report.uuid}
              className={`border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow cursor-pointer ${getStatusColor(
                report.results
              )}`}
              onClick={() => setSelectedReport(report)}
            >
              <div className="p-5">
                <div className="flex items-center mb-2">
                  <FileText className="h-5 w-5 text-green-600 mr-2" />
                  <h2 className="font-bold text-gray-800 truncate">
                    {report.reportName}
                  </h2>
                </div>

                <div className="flex items-center mb-4 text-sm text-gray-500">
                  <Calendar className="h-4 w-4 mr-1" />
                  <span>{formatDate(report.dateOfReport)}</span>
                </div>

                <div className="text-sm">
                  <p className="font-medium text-gray-700 mb-1">Test Type:</p>
                  <p className="text-gray-600 mb-3">
                    {report.testType || "Not specified"}
                  </p>

                  <p className="font-medium text-gray-700 mb-1">Results:</p>
                  {report.results ? (
                    <div className="space-y-1">
                      {Object.entries(report.results)
                        .slice(0, 2)
                        .map(([key, value]) => (
                          <p key={key} className="text-gray-600">
                            <span className="capitalize">{key}:</span> {value}
                          </p>
                        ))}
                      {Object.keys(report.results).length > 2 && (
                        <p className="text-green-600 text-xs mt-1">
                          + more details
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-500">No results available</p>
                  )}
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3 text-right">
                <span className="text-green-600 text-sm font-medium">
                  View details →
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
