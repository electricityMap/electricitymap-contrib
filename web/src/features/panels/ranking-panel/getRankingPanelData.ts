import { getCountryName, getZoneName } from 'translation/translation';
import type { GridState, ZoneKey } from 'types';
import { SpatialAggregate } from 'utils/constants';
import { getCO2IntensityByMode } from 'utils/helpers';

import { getHasSubZones, isGenerationOnlyZone } from '../zone/util';
import { ZoneRowType } from './ZoneList';

function filterZonesBySpatialAggregation(
  zoneKey: ZoneKey,
  spatialAggregation: string
): boolean {
  const hasSubZones = getHasSubZones(zoneKey);
  const isSubZone = zoneKey ? zoneKey.includes('-') : true;
  const isCountryView = spatialAggregation === SpatialAggregate.COUNTRY;
  if (isCountryView && isSubZone) {
    return false;
  }
  if (!isCountryView && hasSubZones) {
    return false;
  }
  return true;
}

export const getRankedState = (
  data: GridState | undefined,
  getCo2colorScale: (co2intensity: number) => string,
  sortOrder: 'asc' | 'desc',
  datetimeIndex: string,
  electricityMode: string,
  spatialAggregation: string
): ZoneRowType[] => {
  if (!data) {
    return [];
  }
  const gridState = data.data.datetimes[datetimeIndex];

  if (!gridState || !gridState.z) {
    return [];
  }

  const zoneState = Object.entries(gridState.z);

  const orderedZones: ZoneRowType[] = [];

  zoneState.sort((a, b) => {
    // Sort by carbon intensity
    const aCarbonIntensity = getCO2IntensityByMode(a[1], electricityMode) ?? 0;
    const bCarbonIntensity = getCO2IntensityByMode(b[1], electricityMode) ?? 0;
    return sortOrder === 'asc'
      ? aCarbonIntensity - bCarbonIntensity
      : bCarbonIntensity - aCarbonIntensity;
  });

  // Define the ranking of the zones, starting from 1
  let ranking = 1;

  for (const [key, value] of zoneState) {
    const co2intensity = value
      ? getCO2IntensityByMode(value, electricityMode)
      : undefined;

    // Filter out zones that don't have a carbon intensity value
    // or are generation only zones
    // or don't match the spatial aggregation
    if (
      !co2intensity ||
      isGenerationOnlyZone(key) ||
      !filterZonesBySpatialAggregation(key, spatialAggregation)
    ) {
      continue;
    }

    const fillColor = co2intensity ? getCo2colorScale(co2intensity) : undefined;
    orderedZones.push({
      zoneId: key as keyof GridState,
      color: fillColor,
      co2intensity,
      countryName: getCountryName(key),
      zoneName: getZoneName(key),
      ranking: ranking,
    });
    ranking++; // Increment the ranking
  }

  return orderedZones;
};
