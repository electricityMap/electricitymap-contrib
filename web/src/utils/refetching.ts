import type { QueryClient } from '@tanstack/react-query';
import { ONE_MINUTE, QUERY_KEYS } from 'api/helpers';
import { addHours } from 'date-fns';

import { TimeRange } from './constants';
import { isValidHistoricalTimeRange } from './helpers';

/**
 * Refetches data when the hour changes to show fresh data.
 * Checks every minute if we have passed the hour and invalidates hourly queries
 * if so. Invalidating the query will cause it to refetch if it is actively in use by a mounted
 * component (e.g. the map or left panel for a specific zone), otherwise it will refetch the next
 * time the component is mounted (e.g. when going back to a zone previously viewed)
 */
export function refetchDataOnHourChange(queryClient: QueryClient) {
  let startHour = new Date().getUTCHours();
  setInterval(() => {
    const currentHour = new Date().getUTCHours();
    if (startHour !== currentHour) {
      console.info(`Refetching data for new hour: ${currentHour}`);

      // Invalidate 72 hourly state query
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.STATE, { aggregate: TimeRange.H72 }],
      });

      // Invalidate 72 hourly zone queries - this matches all zone queries
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.ZONE, { aggregate: TimeRange.H72 }],
      });

      // Reset the start hour
      startHour = currentHour;
    }
  }, ONE_MINUTE);
}

export function getStaleTime(timeRange: TimeRange, urlDatetime?: string) {
  if (!isValidHistoricalTimeRange(timeRange) || urlDatetime) {
    return 0;
  }
  const now = new Date();
  const nextHour = addHours(now, 1);
  return nextHour.getTime() - now.getTime();
}
