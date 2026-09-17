import { useState, useEffect, useCallback } from 'react';

/**
 * Generic data-fetching hook.
 *
 * @param {Function} apiFn  – The API function to call (from services/api.js)
 * @param {Array}    deps   – Dependency array. Re-fetches when values change.
 *                            Pass `null` as first dep to skip the fetch.
 * @returns {{ data, loading, error, refetch }}
 */
export function useApi(apiFn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const skip = deps[0] === null;

  const fetchData = useCallback(async () => {
    if (skip) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await apiFn(...deps);
      setData(result);
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}
