import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { Job, StartJobRequest } from '../../api/types'
import { toApiError } from '../../lib/errors'

export interface BatchJob {
  job: Job | null
  starting: boolean
  /** Starting, cancelling or following the job failed for good. */
  error: ApiError | null
  /** The last status poll failed; polling keeps retrying. */
  connectionLost: boolean
  start: (request: StartJobRequest) => Promise<void>
  cancel: () => Promise<void>
  /** Forget the current job (e.g. when another folder is listed). */
  reset: () => void
}

/** Starts a batch and follows it by polling until every file is final. */
export function useBatchJob(pollIntervalMs = 1000): BatchJob {
  const [job, setJob] = useState<Job | null>(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [connectionLost, setConnectionLost] = useState(false)
  const [retries, setRetries] = useState(0)

  const start = useCallback(async (request: StartJobRequest) => {
    setStarting(true)
    setError(null)
    try {
      setJob(await api.startJob(request))
    } catch (cause) {
      setError(toApiError(cause))
    } finally {
      setStarting(false)
    }
  }, [])

  const cancel = useCallback(async () => {
    if (!job) return
    try {
      setJob(await api.cancelJob(job.id))
    } catch (cause) {
      setError(toApiError(cause))
    }
  }, [job])

  const reset = useCallback(() => {
    setJob(null)
    setError(null)
    setConnectionLost(false)
  }, [])

  const jobId = job?.id
  const running = job?.status === 'running'
  const gone = error?.code === 'job_not_found'

  useEffect(() => {
    if (!jobId || !running || gone) return
    let active = true
    const timer = setTimeout(async () => {
      try {
        const next = await api.getJob(jobId)
        if (!active) return
        setConnectionLost(false)
        setJob(next)
      } catch (cause) {
        if (!active) return
        const apiError = toApiError(cause)
        if (apiError.code === 'job_not_found') setError(apiError)
        else setConnectionLost(true)
        // Changing state schedules the next attempt, even when the job itself did not change.
        setRetries((count) => count + 1)
      }
    }, pollIntervalMs)
    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [jobId, running, gone, job, retries, pollIntervalMs])

  return { job, starting, error, connectionLost, start, cancel, reset }
}
