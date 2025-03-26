// components/SearchAndFilter.js
import { Search, X } from "lucide-react";

export default function SearchAndFilter({
  searchTerm,
  setSearchTerm,
  filterStatus,
  setFilterStatus,
  statusOptions,
  totalCount,
  filteredCount,
}) {
  // Clear search field
  const clearSearch = () => {
    setSearchTerm("");
  };

  return (
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
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
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
            {statusOptions.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {/* Results Summary */}
        <div className="flex items-end">
          <p className="text-gray-600">
            Showing {filteredCount} of {totalCount} deliveries
          </p>
        </div>
      </div>
    </div>
  );
}
