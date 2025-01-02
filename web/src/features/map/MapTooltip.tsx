import * as Portal from '@radix-ui/react-portal';
import useGetState from 'api/getState';
import EstimationBadge from 'components/EstimationBadge';
import NoDataBadge from 'components/NoDataBadge';
import OutageBadge from 'components/OutageBadge';
import { TimeDisplay } from 'components/TimeDisplay';
import { getSafeTooltipPosition } from 'components/tooltips/utilities';
import ZoneGaugesWithCO2Square from 'components/ZoneGauges';
import { ZoneName } from 'components/ZoneName';
import { useAtomValue } from 'jotai';
import { TrendingUpDown } from 'lucide-react';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { StateZoneData } from 'types';
import { round } from 'utils/helpers';
import { selectedDatetimeStringAtom } from 'utils/state/atoms';

import { hoveredZoneAtom, mapMovingAtom, mousePositionAtom } from './mapAtoms';

const emptyZoneData: StateZoneData = {
  p: {},
  c: {},
};

export const TooltipInner = memo(function TooltipInner({
  zoneData,
  zoneId,
}: {
  zoneId: string;
  zoneData?: StateZoneData;
}) {
  const hasZoneData = Boolean(zoneData);
  zoneData ??= emptyZoneData;
  const { e, o } = zoneData;

  const estimated = typeof e === 'number' ? round(e ?? 0, 0) : e;

  return (
    <div className="flex w-full flex-col gap-2 py-3 text-center">
      <div className="flex flex-col px-3">
        <div className="flex w-full flex-row justify-between">
          <ZoneName zone={zoneId} textStyle="font-medium text-base font-poppins" />
          <DataValidityBadge
            hasOutage={Boolean(o)}
            estimated={estimated}
            hasZoneData={hasZoneData}
          />
        </div>
        <TimeDisplay
          zoneId={zoneId}
          className="self-start text-neutral-600 dark:text-neutral-400"
        />
      </div>
      <ZoneGaugesWithCO2Square zoneData={zoneData} />
    </div>
  );
});

TooltipInner.displayName = 'TooltipInner';

export const DataValidityBadge = memo(function DataValidityBadge({
  hasOutage,
  estimated,
  hasZoneData,
}: {
  hasOutage: boolean;
  estimated?: number | boolean | null;
  hasZoneData: boolean;
}) {
  const { t } = useTranslation();

  if (!hasZoneData) {
    return <NoDataBadge />;
  }
  if (hasOutage) {
    return <OutageBadge />;
  }
  if (estimated === true) {
    return (
      <EstimationBadge
        text={t('estimation-badge.fully-estimated')}
        Icon={TrendingUpDown}
      />
    );
  }
  if (estimated && estimated > 0.5) {
    return (
      <EstimationBadge
        text={t(`estimation-card.aggregated_estimated.pill`, {
          percentage: estimated,
        })}
        Icon={TrendingUpDown}
      />
    );
  }
  return null;
});

DataValidityBadge.displayName = 'DataValidityBadge';

export default function MapTooltip() {
  const mousePosition = useAtomValue(mousePositionAtom);
  const hoveredZone = useAtomValue(hoveredZoneAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const isMapMoving = useAtomValue(mapMovingAtom);
  const { data } = useGetState();

  if (!hoveredZone || isMapMoving) {
    return null;
  }

  const { zoneId } = hoveredZone;

  const { x, y } = mousePosition;
  const zoneData = data?.data?.datetimes[selectedDatetimeString]?.z[zoneId];

  const screenWidth = window.innerWidth;
  const tooltipWithDataPositon = getSafeTooltipPosition(x, y, screenWidth, 361, 170);

  return (
    <Portal.Root className="absolute left-0 top-0 hidden h-0 w-0 md:block">
      <div
        className="pointer-events-none relative w-[361px] rounded-2xl border border-neutral-200 bg-white text-sm shadow-lg dark:border-gray-700 dark:bg-gray-900 "
        style={{ left: tooltipWithDataPositon.x, top: tooltipWithDataPositon.y }}
      >
        <TooltipInner zoneData={zoneData} zoneId={zoneId} />
      </div>
    </Portal.Root>
  );
}
