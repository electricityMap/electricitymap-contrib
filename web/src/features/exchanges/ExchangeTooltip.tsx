import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { ZoneName } from 'components/ZoneName';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import { ExchangeArrowData } from 'types';
import { TimeAverages } from 'utils/constants';
import { formatEnergy, formatPower } from 'utils/formatting';
import { timeAverageAtom } from 'utils/state/atoms';

interface ExchangeTooltipProperties {
  exchangeData: ExchangeArrowData;
}

export default function ExchangeTooltip(
  properties: ExchangeTooltipProperties
): ReactElement {
  const { key, f, ci } = properties.exchangeData;
  const { __ } = useTranslation();
  const isExporting = f > 0;
  const roundedNetFlow = Math.abs(Math.round(f));
  const zoneFrom = key.split('->')[isExporting ? 0 : 1];
  const zoneTo = key.split('->')[isExporting ? 1 : 0];
  const [timeAverage] = useAtom(timeAverageAtom);
  const isHourly = timeAverage === TimeAverages.HOURLY;

  return (
    <div className="text-start text-base font-medium">
      {__('tooltips.crossborderexport')}:
      <div>
        <div className="flex items-center pb-2">
          <ZoneName zone={zoneFrom} textStyle="max-w-[165px]" /> <p className="mx-2">→</p>{' '}
          <ZoneName zone={zoneTo} textStyle="max-w-[165px]" />
          <b className="font-bold">
            : {isHourly ? formatPower(roundedNetFlow) : formatEnergy(roundedNetFlow)}
          </b>
        </div>
      </div>
      {__('tooltips.carbonintensityexport')}:
      <div className="pt-1">
        {ci > 0 && (
          <div className="inline-flex items-center gap-x-1">
            <CarbonIntensityDisplay withSquare co2Intensity={ci} />
          </div>
        )}
      </div>
    </div>
  );
}
