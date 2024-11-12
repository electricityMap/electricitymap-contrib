import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { RouteParameters } from 'types';
import { TimeAverages } from 'utils/constants';
import { timeAverageAtom, URL_TO_TIME_AVERAGE } from 'utils/state/atoms';

import { cacheBuster, getBasePath, getHeaders, isValidDate, QUERY_KEYS } from './helpers';

const getZone = async (
  timeAverage: TimeAverages,
  zoneId: string,
  targetDatetime?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');

  const shouldQueryHistorical =
    targetDatetime && isValidDate(targetDatetime) && timeAverage === TimeAverages.HOURLY;

  const path: URL = new URL(
    `v8/details/${URL_TO_TIME_AVERAGE[timeAverage]}/${zoneId}${
      shouldQueryHistorical ? `?targetDate=${targetDatetime}` : ''
    }`,
    getBasePath()
  );
  !targetDatetime && path.searchParams.append('cacheKey', cacheBuster());

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(path, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: ZoneDetails };
    if (!data.zoneStates) {
      throw new Error('No data returned from API');
    }
    return data;
  }

  throw new Error(await response.text());
};

const useGetZone = (): UseQueryResult<ZoneDetails> => {
  const {
    zoneId,
    urlTimeAverage = TimeAverages.HOURLY,
    urlDatetime,
  } = useParams<RouteParameters>();

  return useQuery<ZoneDetails>({
    queryKey: [
      QUERY_KEYS.ZONE,
      {
        zone: zoneId,
        aggregate: urlTimeAverage,
        targetDatetime: urlDatetime,
      },
    ],
    queryFn: async () => {
      if (!zoneId) {
        throw new Error('Zone ID is required');
      }
      return getZone(urlTimeAverage, zoneId, urlDatetime);
    },
  });
};

export default useGetZone;
