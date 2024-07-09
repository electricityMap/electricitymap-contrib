import useGetZone from 'api/getZone';
import { useAtom } from 'jotai';
import { useParams } from 'react-router-dom';
import { Mode, SpatialAggregate } from 'utils/constants';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';

import {
  getDataBlockPositions,
  getExchangeData,
  getExchangesToDisplay,
  getProductionData,
} from '../bar-breakdown/utils';

const DEFAULT_BAR_PX_HEIGHT = 265;

export default function useBarBreakdownChartData() {
  // TODO: Create hook for using "current" selectedTimeIndex of data instead
  const { data: zoneData, isLoading } = useGetZone();
  const { zoneId } = useParams();
  const [viewMode] = useAtom(spatialAggregateAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);
  const isCountryView = viewMode === SpatialAggregate.COUNTRY;
  const currentData = zoneData?.zoneStates?.[selectedDatetime.datetimeString];
  const isConsumption = mixMode === Mode.CONSUMPTION;
  if (isLoading) {
    return { isLoading };
  }

  if (!zoneId || !zoneData || !selectedDatetime.datetimeString || !currentData) {
    return {
      height: DEFAULT_BAR_PX_HEIGHT,
      zoneDetails: undefined,
      currentZoneDetail: undefined,
      exchangeData: [],
      productionData: [],
      isLoading: false,
    };
  }

  const exchangeKeys = getExchangesToDisplay(zoneId, isCountryView, zoneData.zoneStates);

  const productionData = getProductionData(currentData); // TODO: Consider memoing this
  const exchangeData = isConsumption
    ? getExchangeData(currentData, exchangeKeys, mixMode)
    : []; // TODO: Consider memoing this

  const { exchangeY } = getDataBlockPositions(
    //TODO this naming could be more descriptive
    productionData.length,
    exchangeData
  );
  return {
    height: exchangeY,
    zoneDetails: zoneData, // TODO: Data is returned here just to pass it back to the tooltip
    currentZoneDetail: currentData,
    exchangeData,
    productionData,
    isLoading: false,
  };
}
