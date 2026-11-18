import { useState, useEffect, useCallback, useRef } from 'react';
import { getEvaluationTrips, runPrediction } from '../api/pathsnapApi';
import { TripSummary, PredictResponse } from '../types/api';
import { normalizeCoordinates, normalizeGpsObservations } from '../utils/coordinates';

export function usePrediction(isConnected: boolean) {
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [selectedTripId, setSelectedTripId] = useState<string>('');
  const [isLoadingTrips, setIsLoadingTrips] = useState<boolean>(false);
  const [tripFetchError, setTripFetchError] = useState<string | null>(null);

  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<PredictResponse | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number>(0);

  const abortControllerRef = useRef<AbortController | null>(null);
  const timerRef = useRef<number | null>(null);

  // Fetch trips when backend is connected
  const refreshTrips = useCallback(async () => {
    setIsLoadingTrips(true);
    setTripFetchError(null);
    try {
      const fetched = await getEvaluationTrips();
      setTrips(fetched);
      if (fetched.length > 0 && !selectedTripId) {
        setSelectedTripId(fetched[0].trip_id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve trips';
      setTripFetchError(msg);
    } finally {
      setIsLoadingTrips(false);
    }
  }, [selectedTripId]);

  useEffect(() => {
    if (isConnected) {
      refreshTrips();
    }
  }, [isConnected, refreshTrips]);

  const selectTrip = (tripId: string) => {
    // If predicting, abort current request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsPredicting(false);
    setSelectedTripId(tripId);
    setPredictionError(null);
  };

  const executePrediction = async () => {
    if (!selectedTripId) {
      setPredictionError('Please select an evaluation trip first.');
      return;
    }

    // Abort previous if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsPredicting(true);
    setPredictionError(null);
    setElapsedMs(0);

    const startTime = performance.now();
    timerRef.current = window.setInterval(() => {
      setElapsedMs(Math.round(performance.now() - startTime));
    }, 50);

    try {
      const rawResult = await runPrediction(selectedTripId, controller.signal);

      // Validate & normalize coordinates
      const cleanPredictedCoords = normalizeCoordinates(rawResult.predicted_route_coordinates);
      const cleanGpsCoords = normalizeGpsObservations(rawResult.gps_coordinates);

      const sanitizedResult: PredictResponse = {
        ...rawResult,
        predicted_route_coordinates: cleanPredictedCoords,
        gps_coordinates: cleanGpsCoords,
        metrics: rawResult.metrics || {},
      };

      setPredictionResult(sanitizedResult);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Normal cancellation
      }
      const msg = err instanceof Error ? err.message : 'Prediction request failed';
      setPredictionError(msg);
      setPredictionResult(null);
    } finally {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setIsPredicting(false);
      abortControllerRef.current = null;
    }
  };

  const resetPrediction = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsPredicting(false);
    setPredictionResult(null);
    setPredictionError(null);
  };

  return {
    trips,
    selectedTripId,
    isLoadingTrips,
    tripFetchError,
    refreshTrips,
    selectTrip,
    isPredicting,
    predictionResult,
    predictionError,
    elapsedMs,
    executePrediction,
    resetPrediction,
  };
}

