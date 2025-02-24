import {
  Item as ToggleGroupItem,
  Root as ToggleGroupRoot,
} from '@radix-ui/react-toggle-group';
import { TFunction } from 'i18next';
import { memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { TimeRange } from 'utils/constants';

const createOption = (time: TimeRange, t: TFunction) => ({
  value: time,
  label: t(`time-controller.${time}`),
  dataTestId: `time-controller-${time}`,
});

export interface TimeRangeToggleProps {
  timeRange: TimeRange;
  onToggleGroupClick: (newTimeRange: TimeRange) => void;
}

function TimeRangeToggle({ timeRange, onToggleGroupClick }: TimeRangeToggleProps) {
  const { t } = useTranslation();

  const options = useMemo(
    () => Object.values(TimeRange).map((value) => createOption(value, t)),
    [t]
  );

  return (
    <ToggleGroupRoot
      className={
        'mt-1 flex h-11 min-w-fit grow items-center justify-between gap-1 rounded-full bg-gray-300/50 p-1 dark:bg-gray-700/50'
      }
      type="multiple"
      aria-label="Toggle between time averages"
    >
      {options.map(
        ({ value, label, dataTestId }) =>
          value != TimeRange.ALL_YEARS && (
            <ToggleGroupItem
              key={`group-item-${value}-${label}`}
              data-testid={dataTestId}
              value={value}
              aria-label={label}
              onClick={() => onToggleGroupClick(value)}
              className={`
          h-full grow basis-0 select-none rounded-full text-xs font-semibold capitalize
            ${
              timeRange === value
                ? 'bg-white/80 text-brand-green outline outline-1 outline-neutral-200 dark:bg-gray-600/80 dark:text-white dark:outline-gray-400/10'
                : ''
            }
            focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-2 focus-visible:outline-brand-green dark:focus-visible:outline-brand-green-dark`}
            >
              {label}
            </ToggleGroupItem>
          )
      )}
    </ToggleGroupRoot>
  );
}

export default memo(TimeRangeToggle);
