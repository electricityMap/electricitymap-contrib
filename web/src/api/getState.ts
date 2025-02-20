import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import type { GridState, RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { isValidHistoricalTimeRange } from 'utils/helpers';
import { getStaleTime } from 'utils/refetching';
import { timeRangeAtom } from 'utils/state/atoms';

import {
  cacheBuster,
  getBasePath,
  getHeaders,
  getParameters,
  isValidDate,
  QUERY_KEYS,
  TIME_RANGE_TO_BACKEND_PATH,
} from './helpers';

const getState = async (
  timeRange: TimeRange,
  is1HourAppDelay: boolean,
  targetDatetime?: string
): Promise<GridState> => {
  const shouldQueryHistorical =
    targetDatetime &&
    isValidDate(targetDatetime) &&
    isValidHistoricalTimeRange(timeRange);

  const path: URL = new URL(
    `v10/state/${TIME_RANGE_TO_BACKEND_PATH[timeRange]}${getParameters(
      shouldQueryHistorical,
      is1HourAppDelay,
      targetDatetime
    )}`,
    getBasePath()
  );

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  if (!targetDatetime) {
    path.searchParams.append('cacheKey', cacheBuster());
  }
  const response = await fetch(path, requestOptions);
  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

const useGetState = (): UseQueryResult<GridState> => {
  const { urlDatetime } = useParams<RouteParameters>();
  const timeRange = useAtomValue(timeRangeAtom);
  const is1HourAppDelay = useFeatureFlag('1-hour-app-delay');
  return useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: timeRange,
        targetDatetime: urlDatetime,
        is1HourAppDelay,
      },
    ],
    queryFn: () => getState(timeRange, is1HourAppDelay, urlDatetime),
    staleTime: getStaleTime(timeRange, urlDatetime),
    refetchOnWindowFocus: true,
  });
};

export default useGetState;
