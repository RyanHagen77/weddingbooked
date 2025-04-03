'use client'

import React, { useState } from 'react'
import Timekeeper from 'react-timekeeper'
import { FaRegClock } from 'react-icons/fa'

interface Props {
  label: string
  value: string
  onChange: (value: string) => void
}

const formatTo12Hour = (raw: string) => {
  // Ensures time is formatted like "12:00 PM"
  return raw.toUpperCase().replace(/\s?(AM|PM)/, ' $1');
};

export default function StyledTimePicker({ label, value, onChange }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="mb-4 relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>

      <div className="flex items-center space-x-2">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="p-2 border rounded-md shadow-sm bg-white hover:bg-gray-100"
        >
          <FaRegClock />
        </button>
        <span className="text-gray-700 text-sm">{value || 'Select Time'}</span>
      </div>

      {isOpen && (
        <div className="absolute z-50 bg-white border rounded shadow-lg mt-2">
          <Timekeeper
            time={value}
            onChange={(newTime) => {
              const formatted = formatTo12Hour(newTime.formatted12);
              onChange(formatted);
            }}
            onDoneClick={() => setIsOpen(false)}
            switchToMinuteOnHourSelect
            coarseMinutes={5}
            config={{
              TIMEPICKER_WIDTH: 200,
              FONT_SIZE: '14px',
            }}
          />
        </div>
      )}
    </div>
  )
}
