import { Button } from 'components/Button';
import { FormattedTime } from 'components/Time';
import { addDays, subDays, subHours } from 'date-fns';
import { useAtomValue } from 'jotai';
import { ArrowRightToLine, ChevronLeft, ChevronRight } from 'lucide-react';
import { memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import trackEvent from 'utils/analytics';
import { MAX_HISTORICAL_LOOKBACK_DAYS, TrackEvent } from 'utils/constants';
import { useNavigateWithParameters } from 'utils/helpers';
import {
  endDatetimeAtom,
  isHourlyAtom,
  selectedDatetimeIndexAtom,
  startDatetimeAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

function HistoricalTimeHeader() {
  const { i18n } = useTranslation();
  const startDatetime = useAtomValue(startDatetimeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const timeRange = useAtomValue(timeRangeAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const { urlDatetime } = useParams<RouteParameters>();
  const navigate = useNavigateWithParameters();

  const isWithinHistoricalLimit = useMemo(() => {
    if (!urlDatetime) {
      return true;
    }

    const targetDate = subHours(new Date(urlDatetime), 1);

    const maxHistoricalDate = subDays(new Date(), MAX_HISTORICAL_LOOKBACK_DAYS);

    return targetDate >= maxHistoricalDate;
  }, [urlDatetime]);

  function handleRightClick() {
    if (!endDatetime || !urlDatetime) {
      return;
    }
    trackEvent(TrackEvent.HISTORICAL_NAVIGATION, {
      direction: 'forward',
    });

    const nextDay = addDays(endDatetime, 1);

    const fourHoursAgo = subHours(new Date(), 4);

    if (nextDay >= fourHoursAgo) {
      navigate({ datetime: '' });
      return;
    }
    navigate({ datetime: nextDay.toISOString() });
  }

  function handleLeftClick() {
    if (!endDatetime || !isWithinHistoricalLimit) {
      return;
    }
    trackEvent(TrackEvent.HISTORICAL_NAVIGATION, {
      direction: 'backward',
    });

    const previousDay = subDays(endDatetime, 1);

    navigate({ datetime: previousDay.toISOString() });
  }

  function handleLatestClick() {
    trackEvent(TrackEvent.HISTORICAL_NAVIGATION, {
      direction: 'latest',
    });
    navigate({ datetime: '' });
  }

  if (!isHourly && startDatetime && endDatetime) {
    return (
      <div className="flex min-h-6 flex-row items-center justify-center">
        <FormattedTime
          datetime={selectedDatetime.datetime}
          language={i18n.languages[0]}
          timeRange={timeRange}
          className="text-sm font-semibold"
        />
      </div>
    );
  }

  return (
    <div className="relative flex h-6 w-full items-center">
      <div className="absolute flex w-full items-center justify-between px-10">
        <Button
          backgroundClasses="bg-transparent"
          onClick={handleLeftClick}
          size="sm"
          type="tertiary"
          isDisabled={!isWithinHistoricalLimit}
          icon={
            <ChevronLeft
              size={22}
              className={twMerge(
                'text-brand-green dark:text-success-dark',
                !isWithinHistoricalLimit && 'opacity-50'
              )}
            />
          }
        />
        <FormattedTime
          datetime={selectedDatetime.datetime}
          language={i18n.languages[0]}
          timeRange={timeRange}
          className="text-sm font-semibold"
        />
        <Button
          backgroundClasses="bg-transparent"
          size="sm"
          onClick={handleRightClick}
          type="tertiary"
          isDisabled={!urlDatetime}
          icon={
            <ChevronRight
              className={twMerge(
                'text-brand-green dark:text-success-dark',
                !urlDatetime && 'opacity-50'
              )}
              size={22}
            />
          }
        />
      </div>
      <Button
        backgroundClasses="absolute z-1 right-2"
        size="sm"
        type="tertiary"
        onClick={handleLatestClick}
        isDisabled={!urlDatetime}
        icon={
          <ArrowRightToLine
            className={twMerge(
              'text-brand-green dark:text-success-dark',
              !urlDatetime && 'opacity-50'
            )}
            size={22}
          />
        }
      />
    </div>
  );
}

export default memo(HistoricalTimeHeader);
