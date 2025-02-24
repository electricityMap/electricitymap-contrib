import useGetState from 'api/getState';
import TimeRangeToggle from 'components/TimeRangeToggle';
import TimeSlider from 'components/TimeSlider';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { getZoneTimezone, useNavigateWithParameters } from 'utils/helpers';
import {
  endDatetimeAtom,
  isHourlyAtom,
  isRedirectedToLatestDatetimeAtom,
  selectedDatetimeIndexAtom,
  startDatetimeAtom,
  useTimeRangeSync,
} from 'utils/state/atoms';
import { useIsBiggerThanMobile } from 'utils/styling';

import TimeAxis from './TimeAxis';
import TimeHeader from './TimeHeader';

export default function TimeController({ className }: { className?: string }) {
  const isHourly = useAtomValue(isHourlyAtom);
  const [selectedDatetime, setSelectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [numberOfEntries, setNumberOfEntries] = useState(0);
  const { data, isLoading: dataLoading } = useGetState();
  const isBiggerThanMobile = useIsBiggerThanMobile();
  const { zoneId } = useParams<RouteParameters>();
  const [selectedTimeRange, setTimeRange] = useTimeRangeSync();
  const setEndDatetime = useSetAtom(endDatetimeAtom);
  const setStartDatetime = useSetAtom(startDatetimeAtom);
  const { urlDatetime } = useParams();
  const zoneTimezone = getZoneTimezone(zoneId);
  const navigate = useNavigateWithParameters();
  const setIsRedirectedToLatestDatetime = useSetAtom(isRedirectedToLatestDatetimeAtom);
  // Show a loading state if isLoading is true or if there is only one datetime,
  // as this means we either have no data or only have latest hour loaded yet
  const isLoading = dataLoading || Object.keys(data?.datetimes ?? {}).length === 1;

  // TODO: Figure out whether we want to work with datetimes as strings
  // or as Date objects. In this case datetimes are easier to work with
  const datetimes = useMemo(
    () => (data ? Object.keys(data?.datetimes).map((d) => new Date(d)) : undefined),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- is loading is used to trigger the re-memoization on hour change
    [data, isLoading]
  );

  useEffect(() => {
    if (datetimes) {
      // This value is stored in state to avoid flickering when switching between time averages
      // as this effect means index will be one render behind if using datetimes directly
      setNumberOfEntries(datetimes.length - 1);
      // Reset the selected datetime when data changes
      setSelectedDatetime({
        datetime: datetimes.at(-1) as Date,
        index: datetimes.length - 1,
      });
      setEndDatetime(datetimes.at(-1));
      setStartDatetime(datetimes.at(0));
    }
  }, [data, datetimes, setEndDatetime, setSelectedDatetime, setStartDatetime]);

  // Sync the url to the datetime returned by the backend
  useEffect(() => {
    if (!datetimes || !urlDatetime) {
      return;
    }

    const endDatetime = datetimes.at(-1);
    if (!endDatetime) {
      return;
    }

    const urlDate = new Date(urlDatetime).getTime();
    const endDate = endDatetime.getTime();

    if (urlDate !== endDate) {
      setIsRedirectedToLatestDatetime(true);
      navigate({ datetime: '' });
    }
  }, [datetimes, urlDatetime, navigate, setIsRedirectedToLatestDatetime]);

  const onTimeSliderChange = useCallback(
    (index: number) => {
      // TODO: Does this work properly missing values?
      if (!datetimes) {
        return;
      }
      setSelectedDatetime({
        datetime: datetimes[index],
        index,
      });
    },
    [datetimes, setSelectedDatetime]
  );

  const onToggleGroupClick = useCallback(
    (timeRange: TimeRange) => {
      if (datetimes !== undefined) {
        const lastDatetime = datetimes.at(-1);
        if (lastDatetime) {
          // Set time slider to latest value before switching aggregate to avoid flickering
          setSelectedDatetime({
            datetime: lastDatetime,
            index: numberOfEntries,
          });
          setTimeRange(timeRange);
        }
      }
    },
    [setSelectedDatetime, datetimes, numberOfEntries, setTimeRange]
  );
  return (
    <div className={twMerge(className, 'flex flex-col gap-3')}>
      {isBiggerThanMobile && <TimeHeader />}
      <div className="flex items-center gap-2">
        <TimeRangeToggle
          timeRange={selectedTimeRange || TimeRange.H72}
          onToggleGroupClick={onToggleGroupClick}
        />
      </div>

      <div>
        {/* The above div is needed to treat the TimeSlider and TimeAxis as one DOM element */}
        <TimeSlider
          onChange={onTimeSliderChange}
          numberOfEntries={numberOfEntries}
          selectedIndex={selectedDatetime.index}
        />
        <TimeAxis
          datetimes={datetimes}
          selectedTimeRange={selectedTimeRange || TimeRange.H72}
          isLoading={isLoading}
          className="h-[22px] w-full overflow-visible"
          transform={`translate(12, 0)`}
          isLiveDisplay={isHourly && !urlDatetime}
          timezone={zoneTimezone}
          isTimeController={true}
        />
      </div>
    </div>
  );
}
