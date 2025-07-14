'use client'

import React, { useState } from 'react'
import Timekeeper from 'react-timekeeper'
import { FaRegClock } from 'react-icons/fa'

const ClockIcon: React.FC = () => <>{FaRegClock({})}</>;

interface Props {
  label: string
  value: string
  onChange: (value: string) => void
}

const formatTo12Hour = (time: string): string => {
  const [hourStr, minuteStr] = time.split(':')
  let hour = parseInt(hourStr)
  const minute = parseInt(minuteStr)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  hour = hour % 12 || 12
  return `${hour}:${minute.toString().padStart(2, '0')} ${ampm}`
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
          <ClockIcon />
        </button>
        <span className="text-gray-700 text-sm">
          {value ? formatTo12Hour(value) : 'Select Time'}
        </span>
      </div>

      {isOpen && (
        <div className="absolute z-50 bg-white border rounded shadow-lg mt-2">
          <Timekeeper
            time={value || '12:00'}
            onChange={(newTime) => onChange(newTime.formatted24)}
            onDoneClick={() => setIsOpen(false)}
            switchToMinuteOnHourSelect
            coarseMinutes={5}
          />
        </div>
      )}
    </div>
  )
}
