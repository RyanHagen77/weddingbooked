'use client'

import React, { useState } from 'react'
import Timekeeper from 'react-timekeeper'
import { FaRegClock } from 'react-icons/fa'

interface Props {
  label: string
  value: string // stored in 24-hour format like "14:00"
  onChange: (value: string) => void
}

// Converts "14:00" => "2:00 PM"
const formatTo12Hour = (time24: string): string => {
  if (!time24 || !time24.includes(':')) return ''
  const [hourStr, minuteStr] = time24.split(':')
  const hour = parseInt(hourStr, 10)
  const minute = parseInt(minuteStr, 10)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour % 12 || 12
  return `${displayHour}:${minute.toString().padStart(2, '0')} ${ampm}`
}

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
        <span className="text-gray-700 text-sm">
          {value ? formatTo12Hour(value) : 'Select Time'}
        </span>
      </div>

      {isOpen && (
        <div className="absolute z-50 bg-white border rounded shadow-lg mt-2">
          <Timekeeper
            time={value || '12:00'}
            onChange={(newTime) => {
              onChange(newTime.formatted24) // stored as "14:00"
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
