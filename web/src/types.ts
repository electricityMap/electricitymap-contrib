import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from '@turf/turf';
import { LineString, MultiLineString, Point } from 'geojson';
import { EstimationMethods, TimeRange } from 'utils/constants';

export type Maybe<T> = T | null | undefined;

export type ZoneKey = string;

export interface GridState {
  _disclaimer: string;
  createdAt: string;
  datetimes: {
    /** Object representing the grid state at a single point in time */
    [datetimeKey: string]: {
      /** Array of all exchanges */
      e: {
        [key: ZoneKey]: StateExchangeData;
      };
      /** Array of all zones */
      z: {
        [key: ZoneKey]: StateZoneData;
      };
    };
  };
}

export interface StateZoneData {
  /** Object representing all production values */
  p: {
    /** Carbon intensity */
    ci?: number | null;
    /** Fossil ratio */
    fr?: number | null;
    /** Renewable ratio */
    rr?: number | null;
  };
  /** Object representing all consumption values */
  c: {
    /** Carbon intensity */
    ci?: number | null;
    /** Fossil ratio */
    fr?: number | null;
    /** Renewable ratio */
    rr?: number | null;
  };
  /** Represents if a zone is estimated or not, will be true for hourly data else number */
  e?: string | number | null;
  /** Represents if the zone has a outage message or not */
  o?: boolean | null;
}

export interface StateExchangeData {
  /** The carbon intensity of the exchange */
  ci: number;
  /** The net flow of the exchange */
  f: number;
}

export interface ExchangeArrowData {
  co2intensity: number;
  netFlow: number;
  rotation: number;
  lonlat: [number, number];
  key: string;
}

export interface ZoneOverviewForTimePeriod {
  [dateTimeKey: string]: ZoneOverview;
}

export interface ZoneOverview {
  zoneKey: string;
  co2intensity?: number;
  co2intensityProduction?: number;
  stateDatetime: string;
  fossilFuelRatio: number;
  renewableRatio: number;
  estimationMethod?: EstimationMethods;
  estimatedPercentage?: number;
}

export type GenerationType =
  | 'biomass'
  | 'coal'
  | 'gas'
  | 'hydro'
  | 'nuclear'
  | 'oil'
  | 'solar'
  | 'unknown'
  | 'geothermal'
  | 'wind';

export type ElectricityStorageType = 'hydro storage' | 'battery storage';
export type ElectricityStorageKeyType = 'battery' | 'hydro';

export type ElectricityModeType = GenerationType | ElectricityStorageType;

export type Exchange = { [key: string]: number };

export interface ZoneDetail extends ZoneOverview {
  _isFinestGranularity: boolean;
  estimatedPercentage?: number;
  measuredPercentage?: number;
  completenessPercentage?: number;
  // Capacity is only available on hourly details
  capacity?: { [key in ElectricityModeType]: number | null };
  capacitySources?: { [key in ElectricityModeType]: string[] | null };
  dischargeCo2Intensities: { [key in ElectricityStorageKeyType]: number };
  dischargeCo2IntensitySources: { [key in ElectricityStorageKeyType]: string };
  exchange: Exchange;
  exchangeCapacities?: {
    [key: ZoneKey]: number[];
  };
  exchangeCo2Intensities: Exchange;
  fossilFuelRatio: number;
  fossilFuelRatioProduction: number;
  isValid: boolean;
  maxCapacity: number;
  maxDischarge: number;
  maxExport: number;
  maxExportCapacity: number;
  maxImport: number;
  maxImportCapacity: number;
  maxProduction: number;
  maxStorage: number;
  maxStorageCapacity: number;
  price?: {
    value: number;
    currency: string;
    disabledReason?: string;
  };
  production: { [key in GenerationType]: Maybe<number> };
  productionCo2Intensities: { [key in GenerationType]: number };
  productionCo2IntensitySources: { [key in GenerationType]: string };
  renewableRatio: number;
  renewableRatioProduction: number;
  source: string[];
  storage: { [key in ElectricityStorageKeyType]: Maybe<number> };
  totalCo2Consumption: number;
  totalCo2Discharge: number | null;
  totalCo2Export: number | null;
  totalCo2Import: number | null;
  totalCo2NetExchange: number | null;
  totalCo2Production: number;
  totalCo2Storage: number | null;
  totalConsumption: number;
  totalDischarge: number | null;
  totalExport: number | null;
  totalImport: number | null;
  totalProduction: number | null;
  totalStorage: number | null;
}

export interface ZoneDetails {
  hasData: boolean;
  futurePrice: FuturePriceData;
  //TODO Remove from backend, most likely unused
  stateAggregation: 'daily' | 'hourly' | 'monthly' | 'yearly';
  zoneStates: {
    [key: string]: ZoneDetail;
  };
  zoneMessage?: ZoneMessage;
}

export interface ZoneMessage {
  message: string;
  issue?: string;
}

export interface GeometryProperties {
  center: [number, number];
  color: string;
  countryKey: string;
  isAggregatedView: boolean;
  isHighestGranularity: boolean;
  zoneId: string;
  zoneName: string;
}
export interface StateGeometryProperties {
  center?: [number, number];
  stateName?: string;
  stateId?: string;
}

export interface MapGeometries extends FeatureCollection<Geometry> {
  features: Array<MapGeometry>;
}

export interface StatesGeometries extends FeatureCollection<Geometry> {
  features: Array<StatesGeometry>;
}
export interface MapGeometry extends Feature<Polygon | MultiPolygon> {
  geometry: MultiPolygon | Polygon;
  Id?: number;
  properties: GeometryProperties;
}

export interface StatesGeometry extends Feature<LineString | MultiLineString | Point> {
  geometry: LineString | MultiLineString | Point;
  Id?: number;
  properties: StateGeometryProperties;
}

export interface MapTheme {
  co2Scale: {
    steps: number[];
    colors: string[];
  };
  oceanColor: string;
  strokeWidth: number;
  strokeColor: string;
  stateBorderColor: string;
  clickableFill: string;
  nonClickableFill: string;
}

export interface FuturePriceData {
  entryCount: number;
  priceData: {
    [key: string]: number;
  };
  currency: string;
  source: string;
  zoneKey: ZoneKey;
}

// Type for the URL parameters that determine app state
export type RouteParameters = {
  resolution?: string;
  zoneId?: string;
  urlTimeRange?: TimeRange;
  urlDatetime?: string;
};
