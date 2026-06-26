import { useCallback, useEffect, useState } from "react";
import { getApiError } from "../api/client";

/**
 * Generic paginated-list state for table pages.
 *
 * @param fetcher async (params) => response — params include {page, page_size, ...filters}
 * @param options { pageSize, initialFilters }
 */
export function usePagedList(fetcher, { pageSize = 10, initialFilters = {} } = {}) {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState(initialFilters);
  const [data, setData] = useState({ items: [], total: 0, total_pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const cleaned = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== "" && v !== null && v !== undefined)
      );
      const res = await fetcher({ page, page_size: pageSize, ...cleaned });
      setData(res.data);
    } catch (err) {
      setError(getApiError(err));
      setData({ items: [], total: 0, total_pages: 0 });
    } finally {
      setLoading(false);
    }
  }, [fetcher, page, pageSize, filters]);

  useEffect(() => {
    load();
  }, [load]);

  const setFilter = useCallback((key, value) => {
    setPage(1);
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setPage(1);
    setFilters(initialFilters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    page, setPage,
    pageSize,
    filters, setFilter, resetFilters,
    items: data.items,
    total: data.total,
    totalPages: data.total_pages,
    loading, error,
    reload: load,
  };
}
