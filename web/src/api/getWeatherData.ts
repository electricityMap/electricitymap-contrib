import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { addHours, startOfHour, subHours } from 'date-fns';
import { getInterpolatedData } from 'features/weather-layers/weatherUtils';
import type { Maybe } from 'types';

import { FIVE_MINUTES, getBasePath, getHeaders } from './helpers';

export type WeatherType = 'wind' | 'solar';

export interface ForecastEntry {
  data: number[];
  header: {
    dx: number;
    dy: number;
    forecastTime: number;
    la1: number;
    lo1: number;
    nx: number;
    ny: number;
    parameterCategory: number;
    parameterNumber: number;
    refTime: string;
  };
}
export type GfsForecastResponse = ForecastEntry[];

const GFS_STEP_ORIGIN = 6; // hours
const GFS_STEP_HORIZON = 1; // hours

// Data is bucketed into groups for every six hours, so we need to find the closest step in the past
function getForecastStartTime(now: Date) {
  // Warning: solar will not be available at horizon 0 so always do at least horizon 1
  let origin = subHours(startOfHour(now), GFS_STEP_HORIZON);
  if (origin.getUTCHours() % GFS_STEP_ORIGIN !== 0) {
    origin = getForecastStartTime(origin);
  }
  return origin;
}

const getBeforeForcastEndTime = (now: Date) =>
  addHours(startOfHour(now), 0).toISOString();

const getAfterForecastEndTime = (now: Date) =>
  addHours(startOfHour(now), GFS_STEP_HORIZON).toISOString();

const targetTimeFunction = {
  before: getBeforeForcastEndTime,
  after: getAfterForecastEndTime,
};

export async function fetchGfsForecast(
  resource: WeatherType,
  startTime: Date,
  endTime: Date,
  period: 'before' | 'after',
  retries = 0
): Promise<GfsForecastResponse> {
  const targetTime = targetTimeFunction[period](endTime);

  const path: URL = new URL(`v10/gfs/${resource}`, getBasePath());
  path.searchParams.append('refTime', startTime.toISOString());
  path.searchParams.append('targetTime', targetTime);

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };
  const response = await fetch(path, requestOptions);
  if (response.ok) {
    const { data } = await response.json();
    return data;
  }

  if (retries >= 3 || response.status !== 404) {
    // TODO: Handle this error gracefully and show message to users that wind layer is not available
    // TODO: Log to Sentry if status is not 404
    throw new Error(
      `Failed to fetch GFS forecast after ${retries} retries (status: ${response.status})`
    );
  }

  // Retry again with a previous step date if request failed with 404
  return fetchGfsForecast(
    resource,
    subHours(startTime, GFS_STEP_ORIGIN),
    endTime,
    period,
    retries + 1
  );
}

async function getWeatherData(type: WeatherType) {
  const now = new Date();

  const startTime = getForecastStartTime(now);
  const before = fetchGfsForecast(type, startTime, now, 'before');
  const after = fetchGfsForecast(type, startTime, now, 'after');

  const forecasts = await Promise.all([before, after]).then((values) => values);
  const interdata = getInterpolatedData(type, forecasts);
  return interdata;
}

interface UseWeatherQueryOptions
  extends Omit<UseQueryOptions<Maybe<GfsForecastResponse>>, 'queryKey'> {
  type: WeatherType;
}

const useGetWeather = (options: UseWeatherQueryOptions) => {
  const { type, ...queryOptions } = options;
  return useQuery<Maybe<GfsForecastResponse>>({
    queryKey: [type],
    queryFn: () => getWeatherData(type),
    staleTime: FIVE_MINUTES,
    gcTime: FIVE_MINUTES,
    retry: false,
    ...queryOptions,
  });
};

export const useGetWind = (options?: Omit<UseWeatherQueryOptions, 'type'>) =>
  useGetWeather({ type: 'wind', ...options });
export const useGetSolar = (options?: Omit<UseWeatherQueryOptions, 'type'>) =>
  useGetWeather({ type: 'solar', ...options });
