import type { Duration } from 'date-fns';
import { ElectricityModeType } from 'types';

export const metaTitleSuffix = ' | App | Electricity Maps';
export const baseUrl = 'https://app.electricitymaps.com';

// The order here determines the order displayed
export enum TimeRange {
  H72 = '72h',
  M3 = '3mo',
  M12 = '12mo',
  ALL_MONTHS = 'all_months',
  ALL_YEARS = 'all_years',
}

export const MAX_HISTORICAL_LOOKBACK_DAYS = 30;

// used in TimeAxis & areWeatherLayersAllowedAtom
// accommodates 0-based index for 72 hours
export const HOURLY_TIME_INDEX: Partial<Record<TimeRange, number>> = {
  [TimeRange.H72]: 71,
};

export const historicalTimeRange = [TimeRange.H72];

export enum ToggleOptions {
  ON = 'on',
  OFF = 'off',
}

export enum ThemeOptions {
  LIGHT = 'light',
  DARK = 'dark',
  SYSTEM = 'system',
}

export enum Mode {
  CONSUMPTION = 'consumption',
  PRODUCTION = 'production',
}

export enum SpatialAggregate {
  COUNTRY = 'country',
  ZONE = 'zone',
}

export enum LeftPanelToggleOptions {
  ELECTRICITY = 'electricity',
  EMISSIONS = 'emissions',
}

export enum Charts {
  PRICE_CHART = 'price_chart',
  ORIGIN_CHART = 'origin_chart',
  BAR_BREAKDOWN_CHART = 'bar_breakdown_chart',
  CARBON_CHART = 'carbon_chart',
  EMISSION_CHART = 'emission_chart',
  NET_EXCHANGE_CHART = 'net_exchange_chart',
}

export enum TrackEvent {
  APP_BANNER_CTA_CLICKED = 'App Banner CTA Clicked',
  APP_BANNER_DISMISSED = 'App Banner Dismissed',
  SHARE_BUTTON_CLICKED = 'Share Button Clicked',
  SHARE_CHART = 'Share Chart',
  FUTURE_PRICE_EXPANDED = 'Future Price Expanded',
  PRODUCTION_CONSUMPTION_CLICKED = 'Production Consumption Clicked',
  HEADER_LINK_CLICKED = 'HeaderLink Clicked',
  LANGUAGE_SELECTED = 'Language Selected',
  ESTIMATION_CARD_EXPANDED = 'EstimationCard Expanded',
  CONTRIBUTE_ON_GITHUB_BUTTON_CLICKED = 'Contribute On GitHub Button Clicked',
  COLORBLIND_MODE_TOGGLED = 'Colorblind Mode Toggled',
  SPATIAL_AGGREGATE_CLICKED = 'Spatial Aggregate Clicked',
  THEME_SELECTED = 'Theme Selected',
  PANEL_PRODUCTION_BUTTON_CLICKED = 'PanelProductionButton Clicked',
  PANEL_EMISSION_BUTTON_CLICKED = 'PanelEmissionButton Clicked',
  ESTIMATION_CARD_METHODOLOGY_LINK_CLICKED = 'EstimationCard Methodology Link Clicked',
  METHODOLOGIES_AND_DATA_SOURCES_EXPANDED = 'Methodologies and Data Sources Expanded',
  SOLAR_ENABLED = 'Solar Enabled',
  SOLAR_DISABLED = 'Solar Disabled',
  WIND_ENABLED = 'Wind Enabled',
  WIND_DISABLED = 'Wind Disabled',
  HISTORICAL_NAVIGATION = 'Historical Navigation',
}

// color of different production modes are based on various industry standards
export const modeColor: { [mode in ElectricityModeType]: string } = {
  solar: '#FFC700',
  wind: '#69D6F8',
  hydro: '#1878EA',
  'hydro storage': '#2B3CD8',
  'battery storage': '#1DA484',
  biomass: '#008043',
  geothermal: '#A73C15',
  nuclear: '#9D71F7',
  gas: '#AAA189',
  coal: '#545454',
  oil: '#584745',
  unknown: '#ACACAC',
};

export const modeOrder = [
  'nuclear',
  'geothermal',
  'biomass',
  'coal',
  'wind',
  'solar',
  'hydro',
  'hydro storage',
  'battery storage',
  'gas',
  'oil',
  'unknown',
] as const;

/**
 * The order of modes use the following logic:
 * 1. renewables first (sorted alphabetically)
 * 2. low carbon (nuclear)
 * 3. fossil fuels (sorted alphabetically)
 * 4. storage (sorted alphabetically)
 */
export const modeOrderBarBreakdown = [
  'biomass',
  'geothermal',
  'hydro',
  'solar',
  'wind',
  'nuclear',
  'battery storage',
  'hydro storage',
  'coal',
  'gas',
  'oil',
  'unknown',
] as const;

// A mapping between the TimeRange enum and the corresponding Duration for the date-fns add/substract method
export const timeAxisMapping: Record<TimeRange, keyof Duration> = {
  [TimeRange.H72]: 'hours',
  [TimeRange.M3]: 'days',
  [TimeRange.M12]: 'months',
  [TimeRange.ALL_MONTHS]: 'months',
  [TimeRange.ALL_YEARS]: 'years',
};
/**
 * A mapping between the source name and a link to the source.
 * Sources are coming from zone YAML files (capacity and emission factors) or from parsers (production data).
 * The links have been collected from various sources and are not guaranteed to be up-to-date.
 * TODO: In future each link should ideally be stored in the zone configuration YAML files instead of here,
 * so that the link can be updated along with the source and more easily found and maintained.
 */
export const sourceLinkMapping: { [key: string]: string } = {
  'EU-ETS, ENTSO-E 2022':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/EU-emission-factors',
  'EU-ETS, ENTSO-E 2023':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/EU-emission-factors',
  Climatescope: 'https://www.global-climatescope.org/',
  'ree.es': 'https://www.ree.es/en',
  'saskpower.com': 'https://www.saskpower.com/Our-Power-Future',
  'bmreports.com': 'https://www.bmreports.com/bmrs/?q=foregeneration/capacityaggregated',
  'ons.org.br':
    'http://www.ons.org.br/Paginas/resultados-da-operacao/historico-da-operacao/capacidade_instalada.aspx',
  'IRENA.org':
    'https://www.irena.org/publications/2022/Apr/Renewable-Capacity-Statistics-2022',
  'ren.pt': 'https://datahub.ren.pt/en/electricity/monthly-balance/',
  'Ember, Yearly electricity data':
    'https://ember-climate.org/data/data-tools/data-explorer/',
  'coordinador.cl': 'https://www.coordinador.cl/',
  'opennem.org.au': 'https://opennem.org.au/facilities/',
  'taipower.com.tw': 'https://www.taipower.com.tw/en/',
  'EIA.gov': 'https://www.eia.gov/',
  'fingrid.fi': 'https://data.fingrid.fi/en/',
  'Fraunhofer ISE': 'https://energy-charts.info/charts/installed_power/chart.htm',
  'ieso.ca':
    'http://www.ieso.ca/en/Power-Data/Supply-Overview/Transmission-Connected-Generation',
  'entsoe.eu': 'https://transparency.entsoe.eu/',
  'rte-france.com': 'https://www.rte-france.com/eco2mix/les-chiffres-cles-delelectricite',
  'BEIS 2021':
    'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2021',
  'CEA 2022': 'https://cea.nic.in/daily-renewable-generation-report/?lang=en',
  'eGrid 2020':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/US-emission-factors',
  'eGrid 2021':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/US-emission-factors',
  'EIA 2020/BEIS 2021': 'https://www.eia.gov/',
  'Electricity Maps':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
  'Electricity Maps & Dra. Gabriela Muñoz Meléndez':
    'https://github.com/electricitymaps/electricitymaps-contrib/issues/1497',
  'Electricity Maps contrib issue number 1809':
    'https://github.com/electricitymaps/electricitymaps-contrib/issues/1809',
  'Electricity Maps, 2019 average':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
  'Electricity Maps, 2020 average':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
  'Electricity Maps, 2020 average. See disclaimer':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
  'Electricity Maps, 2021 average':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
  'Electricity Maps, 2023 average':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
  'Electricity Maps, CEN':
    'https://docs.google.com/spreadsheets/d/1-iXUGhAM_9Ft5ejlNVxaqaAwG8Octh3gSjU-dm4e96o/edit#gid=163148677',
  'EMBER 2022': 'https://ember-climate.org/data/data-tools/data-explorer/',
  'Enerdata 2022 Japanese National Average':
    'https://www.climate-transparency.org/wp-content/uploads/2022/10/CT2022-Japan-Web.pdf',
  EPPO: 'https://www.eppo.go.th/index.php/en/en-energystatistics/co2-statistic',
  'EU-ETS, TSOC 2021 Report':
    'https://tsoc.org.cy/files/reports/annual-reports/TSOC_Annual_Report_2021.pdf#page=34',
  'Guatemala AMM 2021-2022':
    'https://docs.google.com/spreadsheets/d/1CegROfej9HqRZTfihpjPpgZTYPUHrTNgTdHWbbP3w74/edit#gid=291258352',
  'HOPS 2018':
    'https://www.hops.hr/page-file/oEvvKj779KAhmQg10Gezt2/temeljni-podaci/Temeljni%20podaci%202018.pdf',
  'HOPS 2018 derived calculation':
    'https://github.com/electricitymaps/electricitymaps-contrib/pull/1965',
  'IEA 2015': 'https://www.iea.org/fuels-and-technologies/electricity',
  'IEA 2019': 'https://www.iea.org/fuels-and-technologies/electricity',
  'IEA 2020': 'https://www.iea.org/fuels-and-technologies/electricity',
  'IEA, Electricity generation mix in Mexico, 1 Jan - 30 Sep, 2019 and 2020, IEA, Paris':
    'https://www.iea.org/data-and-statistics/charts/electricity-generation-mix-in-mexico-1-jan-30-sep-2019-and-2020',
  'INCER ACV':
    'https://docs.google.com/spreadsheets/d/1w5DJ7sPen6axIHU8TCVcuzNCjlct4I6JAbhUlw-ZXu8/edit#gid=0',
  'IPCC 2014':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Default-emission-factors',
  'Mallia, E., Lewis, G. "Life cycle greenhouse gas emissions of electricity generation in the province of Ontario, Canada." Int J Life Cycle Assess 18, 377–391 (2013)':
    'https://link.springer.com/article/10.1007/s11367-012-0501-0',
  'Oberschelp, Christopher, et al. "Global emission hotspots of coal power generation."':
    'https://data.mendeley.com/datasets/dm3rjb9ymc/1',
  'SFOE, Electricity Maps':
    'https://docs.google.com/spreadsheets/d/1FLHQ6e9Es08BIqX654BM3SEb_fuAk4k4O-6cmRXyw_E/edit#gid=2007675878',
  'UK POST 2014': 'https://www.parliament.uk/globalassets/documents/post/postpn268.pdf',
  'UNECE 2022':
    'https://unece.org/sites/default/files/2022-04/LCA_3_FINAL%20March%202022.pdf',
  'UNECE 2022, WindEurope "Wind energy in Europe, 2021 Statistics and the outlook for 2022-2026" Wind Europe Proceedings (2021)':
    'https://unece.org/sites/default/files/2022-04/LCA_3_FINAL%20March%202022.pdf#page=37',
  'Wikipedia page for Renewable energy in Ukraine':
    'https://en.wikipedia.org/wiki/Renewable_energy_in_Ukraine',
  'Government of Canada':
    'https://open.canada.ca/data/en/dataset/5a6abd9d-d343-41ef-a525-7a1efb686300/resource/0c58139d-1811-466a-97ba-4c84b3fd83a2',
  'Chubu Electric Power 2022':
    'https://www.chuden.co.jp/corporate/publicity/datalist/juyo/dat_kousei/index.html',
  'Eurostat 2022':
    'https://ec.europa.eu/eurostat/documents/38154/4956218/Energy-Balances-January-2022-edition.zip/2dc71f1b-806a-b9ed-e77d-67b7c705197b?t=1643660477829',
  'sitr.cnd.com.pa': 'https://sitr.cnd.com.pa/m',
  'cndc.org.ni': 'https://www.cndc.org.ni/',
  'nyiso.com': 'https://www.nyiso.com/',
  'iso-ne.com': 'https://www.iso-ne.com/',
  'caiso.com': 'http://www.caiso.com/',
  'emcsg.com': 'https://www.emcsg.com/',
  'cndc.bo': 'https://www.cndc.bo/',
  'Electricity Maps Estimation':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Estimation-methods',
  '2021 annual mean carbon intensity by Electricity Maps':
    'https://github.com/electricitymaps/electricitymaps-contrib/wiki/Emission-factors#emission-factors-for-storage',
};

export const DEFAULT_ICON_SIZE = 16;
export const DEFAULT_TOAST_DURATION = 3 * 1000; // 3s

export enum EstimationMethods {
  TSA = 'ESTIMATED_TIME_SLICER_AVERAGE',
  CONSTRUCT_BREAKDOWN = 'ESTIMATED_CONSTRUCT_BREAKDOWN',
  CONSTRUCT_ZERO_BREAKDOWN = 'ESTIMATED_CONSTRUCT_ZERO_BREAKDOWN',
  FORECASTS_HIERARCHY = 'ESTIMATED_FORECASTS_HIERARCHY',
  MODE_BREAKDOWN = 'ESTIMATED_MODE_BREAKDOWN',
  RECONSTRUCT_BREAKDOWN = 'ESTIMATED_RECONSTRUCT_BREAKDOWN',
  RECONSTRUCT_PRODUCTION_FROM_CONSUMPTION = 'ESTIMATED_RECONSTRUCT_PRODUCTION_FROM_CONSUMPTION',
  AGGREGATED = 'aggregated',
  THRESHOLD_FILTERED = 'threshold_filtered',
  OUTAGE = 'outage',
  GENERAL_PURPOSE_ZONE_MODEL = 'ESTIMATED_GENERAL_PURPOSE_ZONE_MODEL',
}

export const isTSAModel = (estimationMethod: EstimationMethods | undefined) =>
  estimationMethod === EstimationMethods.TSA ||
  estimationMethod === EstimationMethods.FORECASTS_HIERARCHY;
