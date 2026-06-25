import { AxiosError } from 'axios'
import { ApiError } from '../types'

/**
 * Get a user-friendly error message from an API response
 * @param error - The error object (either AxiosError or ApiError)
 * @returns A user-friendly error message string
 */
export const getErrorMessage = (error: any): string => {
  // Handle AxiosError
  if (error.response) {
    const status = error.response.status
    const data = error.response.data as any

    // Check if response has a detail field (common for API errors)
    if (data?.detail && typeof data.detail === 'string') {
      return data.detail
    }

    // Check if response has an error field
    if (data?.error && typeof data.error === 'string') {
      return data.error
    }

    // Handle specific status codes
    switch (status) {
      case 400:
        return data?.message || 'Invalid request. Please check your input.'
      case 401:
        return 'Your session has expired. Please login again.'
      case 403:
        return "You don't have permission to access this resource."
      case 404:
        return 'Resource not found.'
      case 409:
        return data?.message || 'Conflict with current state. Please try again.'
      case 422:
        return 'Validation error. Please check your input.'
      case 500:
        return 'Server error. Please try again later.'
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.'
      case 503:
        return 'Service unavailable. Please try again later.'
      default:
        return `An error occurred (${status}). Please try again.`
    }
  }

  // Handle network errors
  if (error.code === 'ECONNABORTED') {
    return 'Request timeout. Please check your network connection.'
  }

  if (!error.response) {
    return 'Connection error. Please check your network.'
  }

  // Handle generic errors
  if (error.message) {
    return error.message
  }

  return 'An unexpected error occurred. Please try again.'
}

/**
 * Check if an error is an authentication error (401)
 * @param error - The error object to check
 * @returns True if the error is a 401 Unauthorized error
 */
export const isAuthenticationError = (error: any): boolean => {
  return error?.response?.status === 401 || error?.status === 401
}

/**
 * Check if an error is an authorization error (403)
 * @param error - The error object to check
 * @returns True if the error is a 403 Forbidden error
 */
export const isAuthorizationError = (error: any): boolean => {
  return error?.response?.status === 403 || error?.status === 403
}

/**
 * Check if an error is a network error (no response from server)
 * @param error - The error object to check
 * @returns True if the error is a network error
 */
export const isNetworkError = (error: any): boolean => {
  return !error?.response && error?.code !== 'ECONNABORTED'
}

/**
 * Check if an error is a timeout error
 * @param error - The error object to check
 * @returns True if the error is a timeout error
 */
export const isTimeoutError = (error: any): boolean => {
  return error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')
}

/**
 * Check if an error is a validation error (400 or 422)
 * @param error - The error object to check
 * @returns True if the error is a validation error
 */
export const isValidationError = (error: any): boolean => {
  const status = error?.response?.status || error?.status
  return status === 400 || status === 422
}

/**
 * Check if an error is a server error (5xx)
 * @param error - The error object to check
 * @returns True if the error is a server error
 */
export const isServerError = (error: any): boolean => {
  const status = error?.response?.status || error?.status
  return status ? status >= 500 && status < 600 : false
}

/**
 * Check if an error is a client error (4xx)
 * @param error - The error object to check
 * @returns True if the error is a client error
 */
export const isClientError = (error: any): boolean => {
  const status = error?.response?.status || error?.status
  return status ? status >= 400 && status < 500 : false
}

/**
 * Get detailed error information for logging
 * @param error - The error object to analyze
 * @returns An object with error details
 */
export const getErrorDetails = (error: any) => {
  return {
    status: error?.response?.status || error?.status,
    message: getErrorMessage(error),
    code: error?.response?.data?.code || error?.code,
    isAuthError: isAuthenticationError(error),
    isAuthzError: isAuthorizationError(error),
    isNetworkError: isNetworkError(error),
    isValidationError: isValidationError(error),
    isServerError: isServerError(error),
    timestamp: new Date().toISOString(),
  }
}

/**
 * Handle API errors consistently across the application
 * Logs errors and returns user-friendly message
 * @param error - The error to handle
 * @param context - Optional context for logging (e.g., which operation failed)
 * @returns User-friendly error message
 */
export const handleApiError = (error: any, context?: string): string => {
  const errorDetails = getErrorDetails(error)

  // Log error details for debugging (in development only)
  if (import.meta.env.DEV) {
    console.error('[API Error]', {
      context,
      ...errorDetails,
      raw: error,
    })
  }

  // Handle authentication errors
  if (errorDetails.isAuthError) {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    // The API interceptor will handle redirect to login
  }

  return errorDetails.message
}
