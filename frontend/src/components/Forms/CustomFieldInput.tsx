import React from 'react'
import { CustomField } from '../../types'

interface CustomFieldInputProps {
  field: CustomField
  value: any
  onChange: (value: any) => void
  disabled?: boolean
  error?: string
}

/**
 * Render input based on field type
 */
function renderInput(
  field: CustomField,
  value: any,
  onChange: (value: any) => void,
  disabled?: boolean,
  error?: string
): React.ReactNode {
  const baseClasses = `w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
    error ? 'border-red-500' : 'border-gray-300'
  } ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`

  switch (field.field_type) {
    case 'text':
      return (
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={baseClasses}
          placeholder={field.is_required ? 'Required field' : 'Optional'}
        />
      )

    case 'number':
      return (
        <input
          type="number"
          value={value || ''}
          onChange={(e) => onChange(e.target.value === '' ? null : parseFloat(e.target.value))}
          disabled={disabled}
          className={baseClasses}
          placeholder="0"
          step="0.01"
        />
      )

    case 'date':
      return (
        <input
          type="date"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={baseClasses}
        />
      )

    case 'boolean':
      return (
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">
            {value ? 'Yes' : 'No'}
          </span>
        </label>
      )

    case 'dropdown':
      const options = Array.isArray(field.options)
        ? field.options
        : typeof field.options === 'object'
          ? Object.keys(field.options || {})
          : []

      return (
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={baseClasses}
        >
          <option value="">
            {field.is_required ? 'Select an option' : 'Select an option (optional)'}
          </option>
          {options.map((option: string) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      )

    default:
      return (
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={baseClasses}
          placeholder="Enter value"
        />
      )
  }
}

export const CustomFieldInput: React.FC<CustomFieldInputProps> = ({
  field,
  value,
  onChange,
  disabled = false,
  error,
}) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.name}
        {field.is_required && <span className="text-red-600 ml-1">*</span>}
      </label>

      {renderInput(field, value, onChange, disabled, error)}

      {error && <p className="text-red-600 text-sm mt-1">{error}</p>}

      {/* Validation rules info */}
      {field.validation_rules && (
        <div className="mt-1 text-xs text-gray-500">
          {field.validation_rules.min !== undefined && (
            <p>Minimum: {field.validation_rules.min}</p>
          )}
          {field.validation_rules.max !== undefined && (
            <p>Maximum: {field.validation_rules.max}</p>
          )}
          {field.validation_rules.pattern && (
            <p>Pattern: {field.validation_rules.pattern}</p>
          )}
        </div>
      )}
    </div>
  )
}
