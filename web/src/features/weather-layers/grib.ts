import type { ForecastEntry } from 'api/getWeatherData';
import { addHours } from 'date-fns';

export const getReferenceTime = (grib: ForecastEntry) => new Date(grib.header.refTime);

export const getTargetTime = (grib: ForecastEntry) =>
  addHours(getReferenceTime(grib), grib.header.forecastTime).getTime();
