'use client'

import React, { useState } from 'react'
import Timekeeper from 'react-timekeeper'
import { FaRegClock } from 'react-icons/fa'

interface Props {
  label: string
  value: string            // 24-hour format like "14:00"
  displayValue?: string    // Optional: 12-hour format like "2:00 PM"
  onChange: (value: string) => void
}

// Convert "14:00" → "2:00 PM"
const parseTimeTo12Hour = (timeStr: string): string => {
  const [hourStr, minuteStr] = timeStr.split(':')
  let hour = parseInt(hourStr)
  const minute = parseInt(minuteStr)
  const isPM = hour >= 12

  if (hour === 0) hour = 12
  else if (hour > 12) hour -= 12

  const hourStrFormatted = hour.toString()
  const minuteStrFormatted = minute.toString().padStart(2, '0')
  const ampm = isPM ? 'PM' : 'AM'

  return `${hourStrFormatted}:${minuteStrFormatted} ${ampm}`
}

export default function StyledTimePicker({ label, value, displayValue, onChange }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="mb-4 relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>

      {/* Clock button and visible time */}
      <div className="flex items-center space-x-2">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="p-2 border rounded-md shadow-sm bg-white hover:bg-gray-100"
        >
          <FaRegClock />
        </button>

        {/* Display formatted time */}
        <span className="text-gray-700 text-sm">
          {displayValue || parseTimeTo12Hour(value)}
        </span>
      </div>

      {/* Time picker popover */}
      {isOpen && (
        <div className="absolute z-50 bg-white border rounded shadow-lg mt-2">
          <Timekeeper
            time={value || '12:00'}
            onChange={(newTime) => {
              onChange(newTime.formatted12)
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
