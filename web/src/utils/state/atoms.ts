import { atom, useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { dateToDatetimeString, useNavigateWithParameters } from 'utils/helpers';

import {
  Mode,
  SpatialAggregate,
  ThemeOptions,
  TimeAverages,
  ToggleOptions,
} from '../constants';

// TODO: Move these atoms to relevant features
// TODO: Make some of these atoms also sync with URL (see atomWithCustomStorage.ts)

export const timeAverageAtom = atom<TimeAverages>(TimeAverages.HOURLY);

export function useTimeAverageSync() {
  const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
  const { urlTimeAverage } = useParams<{ urlTimeAverage: string }>();
  const navigateWithParameters = useNavigateWithParameters();

  // Update atom when URL changes
  useEffect(() => {
    if (urlTimeAverage && urlTimeAverage !== timeAverage) {
      setTimeAverage(urlTimeAverage as TimeAverages);
    }
  }, [setTimeAverage, timeAverage, urlTimeAverage]); // Only depend on URL changes

  // Combined setter that updates both atom and URL
  const setTimeAverageAndNavigate = (newTimeAverage: TimeAverages) => {
    setTimeAverage(newTimeAverage);
    navigateWithParameters({ timeAverage: newTimeAverage });
  };
  return [timeAverage, setTimeAverageAndNavigate] as const;
}
export const isHourlyAtom = atom((get) => get(timeAverageAtom) === TimeAverages.HOURLY);

// TODO: consider another initial value
export const selectedDatetimeIndexAtom = atom({ datetime: new Date(), index: 0 });
export const endDatetimeAtom = atom<Date | undefined>(undefined);
export const startDatetimeAtom = atom<Date | undefined>(undefined);
export const selectedDatetimeStringAtom = atom<string>((get) => {
  const { datetime } = get(selectedDatetimeIndexAtom);
  return dateToDatetimeString(datetime);
});

export const spatialAggregateAtom = atomWithStorage(
  'country-mode',
  SpatialAggregate.ZONE
);
export const productionConsumptionAtom = atomWithStorage('mode', Mode.CONSUMPTION);
export const isConsumptionAtom = atom<boolean>(
  (get) => get(productionConsumptionAtom) === Mode.CONSUMPTION
);

export const areWeatherLayersAllowedAtom = atom<boolean>(
  (get) => get(isHourlyAtom) && get(selectedDatetimeIndexAtom).index === 24
);

export const solarLayerAtom = atomWithStorage('solar', ToggleOptions.OFF);
export const isSolarLayerEnabledAtom = atom<boolean>(
  (get) => get(solarLayerAtom) === ToggleOptions.ON && get(areWeatherLayersAllowedAtom)
);

export const windLayerAtom = atomWithStorage('wind', ToggleOptions.OFF);
export const isWindLayerEnabledAtom = atom<boolean>(
  (get) => get(windLayerAtom) === ToggleOptions.ON && get(areWeatherLayersAllowedAtom)
);

export const solarLayerLoadingAtom = atom<boolean>(false);
export const windLayerLoadingAtom = atom<boolean>(false);

export const displayByEmissionsAtom = atom<boolean>(false);

export const themeAtom = atomWithStorage('theme', ThemeOptions.SYSTEM);

export const hasOnboardingBeenSeenAtom = atomWithStorage(
  'onboardingSeen',
  localStorage.getItem('onboardingSeen') ?? false
);

export const hasEstimationFeedbackBeenSeenAtom = atomWithStorage(
  'estimationFeedbackSeen',
  localStorage.getItem('estimationFeedbackSeen') ?? false
);

export const feedbackCardCollapsedNumberAtom = atom(0);

export const colorblindModeAtom = atomWithStorage('colorblindModeEnabled', false);

export const dataSourcesCollapsedBarBreakdownAtom = atom<boolean>(true);

export const dataSourcesCollapsedBreakdownAtom = atom<boolean>(true);

export const dataSourcesCollapsedEmissionAtom = atom<boolean>(true);

export const userLocationAtom = atom<string | undefined>(undefined);

export const hasSeenSurveyCardAtom = atomWithStorage('hasSeenSurveyCard', false);

export const hasSeenUsSurveyCardAtom = atomWithStorage('hasSeenUsSurveyCard', false);

export const rankingPanelAccordionCollapsedAtom = atomWithStorage(
  'rankingPanelAccordionCollapsed',
  false
);

export const futurePriceCollapsedAtom = atom<boolean>(true);
