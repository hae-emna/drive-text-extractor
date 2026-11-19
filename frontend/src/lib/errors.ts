import { ApiError } from '../api/client'

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  return new ApiError('unexpected', 'Something went wrong. Please try again.', 0)
}
