import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { AxiosError } from 'axios'

interface LoginFormData {
  username: string
  password: string
}

interface FormErrors {
  [key: string]: string
}

const Login: React.FC = () => {
  const navigate = useNavigate()
  const { login, state } = useAuth()
  const usernameInputRef = useRef<HTMLInputElement>(null)
  const passwordInputRef = useRef<HTMLInputElement>(null)
  const formRef = useRef<HTMLFormElement>(null)

  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Handle Chrome password manager autofill
  useEffect(() => {
    const handleAutofill = () => {
      // Delay to allow Chrome to complete autofill
      setTimeout(() => {
        if (usernameInputRef.current && passwordInputRef.current) {
          // Sync form data with actual input values
          const username = usernameInputRef.current.value
          const password = passwordInputRef.current.value
          if (username || password) {
            setFormData({
              username: username || '',
              password: password || '',
            })
          }
        }
      }, 100)
    }

    const form = formRef.current
    if (form) {
      form.addEventListener('animationstart', handleAutofill)
      return () => form.removeEventListener('animationstart', handleAutofill)
    }
  }, [])

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (state.isAuthenticated) {
      navigate('/dashboard')
    }
  }, [state.isAuthenticated, navigate])

  // Validate form fields
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required'
    } else if (formData.username.trim().length < 3) {
      newErrors.username = 'Username must be at least 3 characters'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
    // Clear submit error when user types
    if (submitError) {
      setSubmitError(null)
    }
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    
    // Validate form
    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      await login(formData.username, formData.password)
      navigate('/dashboard')
    } catch (err) {
      const error = err as AxiosError<any>
      
      if (error.response?.status === 401) {
        setSubmitError('Invalid username or password. Please try again.')
      } else if (error.code === 'ECONNABORTED' || error.message === 'Network Error') {
        setSubmitError('Connection error. Please check your network.')
      } else if (error.response?.data?.detail) {
        setSubmitError(error.response.data.detail)
      } else {
        setSubmitError('Login failed. Please try again later.')
      }
      
      // Log error details to console for debugging
      console.error('Login error:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Login</h1>
            <p className="text-slate-400 text-sm">
              Project Resource Management System
            </p>
          </div>

          {/* Error Alert */}
          {submitError && (
            <div className="mb-6 rounded-md border border-red-700 bg-red-900/20 p-4">
              <p className="text-sm text-red-300">{submitError}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6" ref={formRef}>
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="label">
                Username or Email
              </label>
              <input
                ref={usernameInputRef}
                id="username"
                name="username"
                type="text"
                placeholder="Enter your username or email"
                value={formData.username}
                onChange={handleInputChange}
                className={`input-field ${
                  errors.username ? 'border-red-600 focus:ring-red-500' : ''
                }`}
                disabled={isSubmitting}
                autoComplete="username"
              />
              {errors.username && (
                <p className="mt-2 text-xs text-red-400">{errors.username}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                ref={passwordInputRef}
                id="password"
                name="password"
                type="password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleInputChange}
                className={`input-field ${
                  errors.password ? 'border-red-600 focus:ring-red-500' : ''
                }`}
                disabled={isSubmitting}
                autoComplete="current-password"
              />
              {errors.password && (
                <p className="mt-2 text-xs text-red-400">{errors.password}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2 px-4 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors disabled:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center text-xs text-slate-400">
            <p>Demo credentials available in system documentation</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
