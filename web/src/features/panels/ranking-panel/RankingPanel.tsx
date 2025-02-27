import useGetState from 'api/getState';
import { useCo2ColorScale } from 'hooks/theme';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useAtomValue } from 'jotai';
import { ReactElement, useCallback, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { metaTitleSuffix } from 'utils/constants';
import {
  isConsumptionAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';

import { getRankedState } from './getRankingPanelData';
import RankingPanelAccordion from './RankingPanelAccordion';
import SearchBar from './SearchBar';
import { VirtualizedZoneList } from './ZoneList';

export default function RankingPanel(): ReactElement {
  const { t } = useTranslation();
  const getCo2colorScale = useCo2ColorScale();
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const [searchTerm, setSearchTerm] = useState('');
  const isConsumption = useAtomValue(isConsumptionAtom);
  const spatialAggregation = useAtomValue(spatialAggregateAtom);
  const canonicalUrl = useGetCanonicalUrl();
  const inputHandler = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = inputEvent;

    if (typeof target?.value === 'string') {
      const lowerCase = target.value.toLowerCase();
      setSearchTerm(lowerCase);
    }
  }, []);

  const { data } = useGetState();
  const rankedList = getRankedState(
    data,
    getCo2colorScale,
    'asc',
    selectedDatetimeString,
    isConsumption,
    spatialAggregation
  );

  const filteredList = rankedList.filter(
    (zone) =>
      zone.countryName?.toLowerCase().includes(searchTerm) ||
      zone.zoneName?.toLowerCase().includes(searchTerm) ||
      zone.zoneId.toLowerCase().includes(searchTerm) ||
      zone.fullZoneName?.toLowerCase().includes(searchTerm)
  );

  return (
    <div className="flex h-[calc(100vh-220px)] w-full flex-col py-3 pl-4 pr-1 ">
      <Helmet prioritizeSeoTags>
        <title>{t('misc.maintitle') + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>

      <div className="flex flex-grow flex-col overflow-hidden pr-2">
        <div className="pb-5">
          <h1>{t('ranking-panel.title')}</h1>
          <p className="text-sm">{t('ranking-panel.subtitle')}</p>
        </div>

        <SearchBar
          placeholder={t('ranking-panel.search')}
          searchHandler={inputHandler}
          value={searchTerm}
        />

        <div className="flex-grow overflow-y-auto">
          {filteredList.length === 0 && <div>{t('ranking-panel.no-results')}</div>}
          <VirtualizedZoneList data={filteredList} />
          {/* TODO: Revise the margin here once the scrollbars are fixed */}
        </div>
      </div>

      <div className="mt-auto pb-5 pr-3 pt-2">
        <RankingPanelAccordion />
      </div>
    </div>
  );
}
