// components/StyledTimePicker.tsx
import Timekeeper from 'react-timekeeper'

interface Props {
  label: string
  value: string
  onChange: (value: string) => void
}

export default function StyledTimePicker({ label, value, onChange }: Props) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="border rounded-md shadow p-2 bg-white">
        <Timekeeper
          time={value}
          onChange={(newTime) => onChange(newTime.formatted12)}
          switchToMinuteOnHourSelect
        />
      </div>
    </div>
  )
}
