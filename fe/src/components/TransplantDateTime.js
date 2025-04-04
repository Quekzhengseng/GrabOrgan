import { useState, useEffect } from "react";

export default function TransplantDateTimePicker({
  onChange,
  initialDateTime = "",
}) {
  const initialDate = initialDateTime ? initialDateTime.split("T")[0] : "";
  const initialTime = initialDateTime
    ? initialDateTime.split("T")[1]?.slice(0, 5)
    : "";

  const [selectedDate, setSelectedDate] = useState(initialDate);
  const [selectedTime, setSelectedTime] = useState(initialTime);

  useEffect(() => {
    if (selectedDate && selectedTime) {
      const datetime = `${selectedDate}T${selectedTime}`;
      onChange?.(datetime); // call the parent callback with the combined datetime
    }
  }, [selectedDate, selectedTime]);

  return (
    <div>
      <div>
        <label className="block text-sm font-semibold mb-1">
          Transplant Date
        </label>
        <input
          type="date"
          className="w-full border rounded p-2"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
      </div>

      <div className="mt-4">
        <label className="block text-sm font-semibold mb-1">
          Transplant Time (+8 GMT)
        </label>
        <select
          className="w-full border rounded p-2"
          value={selectedTime}
          onChange={(e) => setSelectedTime(e.target.value)}
        >
          <option value="">Select Time</option>
          {[
            "00:00",
            "00:30",
            "01:00",
            "01:30",
            "02:00",
            "02:30",
            "03:00",
            "03:30",
            "04:00",
            "04:30",
            "05:00",
            "05:30",
            "06:00",
            "06:30",
            "07:00",
            "07:30",
            "08:00",
            "08:30",
            "09:00",
            "09:30",
            "10:00",
            "10:30",
            "11:00",
            "11:30",
            "12:00",
            "12:30",
            "13:00",
            "13:30",
            "14:00",
            "14:30",
            "15:00",
            "15:30",
            "16:00",
            "16:30",
            "17:00",
            "17:30",
            "18:00",
            "18:30",
            "19:00",
            "19:30",
            "20:00",
            "20:30",
            "21:00",
            "21:30",
            "22:00",
            "22:30",
            "23:00",
            "23:30",
          ].map((time) => (
            <option key={time} value={time}>
              {time}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
