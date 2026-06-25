import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const REQUEST_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second, will be multiplied by attempt number for exponential backoff

interface RetryConfig {
  count: number
  delay: number
}

class ApiClient {
  private client: AxiosInstance
  private retryConfig: Map<string, RetryConfig> = new Map()

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: REQUEST_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // Add standard headers
        config.headers['Content-Type'] = 'application/json'
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Add response interceptor for error handling and retries
    this.client.interceptors.response.use(
      (response) => {
        // Clear retry config on successful response
        const key = this.getRequestKey(response.config.method || '', response.config.url || '')
        this.retryConfig.delete(key)
        return response
      },
      async (error: AxiosError) => {
        console.error('[ApiClient] Response error:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          url: error.config?.url,
          code: error.code,
          message: error.message,
        })

        // Handle 401 Unauthorized - redirect to login
        if (error.response?.status === 401) {
          console.warn('[ApiClient] Unauthorized (401), redirecting to login')
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
          return Promise.reject(error)
        }

        // Handle network errors with retry logic
        if (!error.response && error.code !== 'ECONNABORTED') {
          const config = error.config
          if (config) {
            const key = this.getRequestKey(config.method || '', config.url || '')
            const retryState = this.retryConfig.get(key) || { count: 0, delay: RETRY_DELAY }

            if (retryState.count < MAX_RETRIES && this.isRetryableMethod(config.method)) {
              retryState.count++
              const backoffDelay = retryState.delay * retryState.count

              this.retryConfig.set(key, retryState)

              console.warn(`[ApiClient] Retrying ${config.method} ${config.url} (attempt ${retryState.count})`)

              // Wait for exponential backoff period
              await new Promise(resolve => setTimeout(resolve, backoffDelay))

              // Retry the request
              return this.client(config)
            } else {
              console.error(`[ApiClient] Max retries exceeded for ${config.method} ${config.url}`)
            }
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private getRequestKey(method: string, url: string): string {
    return `${method}:${url}`
  }

  private isRetryableMethod(method?: string): boolean {
    // Only retry GET requests and HEAD requests (idempotent)
    return method?.toUpperCase() === 'GET' || method?.toUpperCase() === 'HEAD'
  }

  get<T = any>(url: string, config?: any) {
    return this.client.get<T>(url, config)
  }

  post<T = any>(url: string, data?: any, config?: any) {
    return this.client.post<T>(url, data, config)
  }

  put<T = any>(url: string, data?: any, config?: any) {
    return this.client.put<T>(url, data, config)
  }

  delete<T = any>(url: string, config?: any) {
    return this.client.delete<T>(url, config)
  }

  patch<T = any>(url: string, data?: any, config?: any) {
    return this.client.patch<T>(url, data, config)
  }

  getClient(): AxiosInstance {
    return this.client
  }
}

export const apiClient = new ApiClient()
export const api = apiClient.getClient()
