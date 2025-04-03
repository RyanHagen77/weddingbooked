// components/TimeInput.tsx
'use client';

import React from 'react';
import TimePicker from 'react-time-picker';
import 'react-time-picker/dist/TimePicker.css';
import 'react-clock/dist/Clock.css';

interface TimeInputProps {
  value: string | null;
  onChange: (value: string | null) => void;
  label: string;
}

const TimeInput: React.FC<TimeInputProps> = ({ value, onChange, label }) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <TimePicker
          onChange={onChange}
          value={value}
          disableClock={false} // ✅ ENABLE CLOCK
          clearIcon={null}
          format="h:mm a"
          clockIcon={undefined} // You can customize this if you want
          className="w-full border rounded-md p-2"
          amPmAriaLabel="Select AM/PM"
        />
    </div>
  );
};

export default TimeInput;
