import {
  Item as ToggleGroupItem,
  Root as ToggleGroupRoot,
} from '@radix-ui/react-toggle-group';
import { TFunction } from 'i18next';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { TimeAverages } from 'utils/constants';

const createOption = (time: TimeAverages, t: TFunction) => ({
  value: time,
  label: t(`time-controller.${time}`),
  dataTestId: `time-controller-${time}`,
});

export interface TimeAverageToggleProps {
  timeAverage: TimeAverages;
  onToggleGroupClick: (newTimeAverage: TimeAverages) => void;
}

function TimeAverageToggle({ timeAverage, onToggleGroupClick }: TimeAverageToggleProps) {
  const { t } = useTranslation();
  const options = useMemo(
    () =>
      Object.keys(TimeAverages).map((time) =>
        createOption(time.toLowerCase() as TimeAverages, t)
      ),
    [t]
  );

  return (
    <ToggleGroupRoot
      className={
        'flex h-11 min-w-fit grow items-center justify-between gap-1 rounded-full bg-gray-200/80 p-1 backdrop-blur-sm dark:bg-gray-800/80'
      }
      type="multiple"
      aria-label="Toggle between time averages"
    >
      {options.map(({ value, label, dataTestId }) => (
        <ToggleGroupItem
          key={`group-item-${value}-${label}`}
          data-test-id={dataTestId}
          value={value}
          aria-label={label}
          onClick={() => onToggleGroupClick(value)}
          className={`
          h-full grow basis-0 select-none border border-transparent text-sm font-semibold capitalize
            ${
              timeAverage === value
                ? 'rounded-full border-[#e5e5e5] bg-white/80 text-brand-green dark:border-gray-400/10 dark:bg-gray-600/80 dark:text-white'
                : ''
            }`}
        >
          <p>{label}</p>
        </ToggleGroupItem>
      ))}
    </ToggleGroupRoot>
  );
}

export default TimeAverageToggle;
