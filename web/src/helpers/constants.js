// Production/imports-exports mode
const modeColor = {
  solar: '#f27406',
  wind: '#74cdb9',
  hydro: '#2772b2',
  'hydro storage': '#0052cc',
  battery: 'lightgray',
  'battery storage': '#b76bcf',
  biomass: '#166a57',
  geothermal: 'yellow',
  nuclear: '#AEB800',
  gas: '#bb2f51',
  coal: '#ac8c35',
  oil: '#867d66',
  unknown: '#ACACAC',
};
const modeOrder = [
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
];
const PRODUCTION_MODES = modeOrder.filter((d) => d.indexOf('storage') === -1);
const STORAGE_MODES = modeOrder.filter((d) => d.indexOf('storage') !== -1).map((d) => d.replace(' storage', ''));

const DEFAULT_FLAG_SIZE = 16;

const DATA_FETCH_INTERVAL = 5 * 60 * 1000; // 5 minutes

const LANGUAGE_NAMES = {
  ar: 'اللغة العربية الفصحى',
  cs: 'Čeština',
  da: 'Dansk',
  de: 'Deutsch',
  el: 'Ελληνικά',
  'en-GB': 'English',
  es: 'Español',
  et: 'Eesti',
  fi: 'Suomi',
  fr: 'Français',
  hr: 'Hrvatski',
  id: 'Bahasa Indonesia',
  it: 'Italiano',
  ja: '日本語',
  ko: '한국어',
  nl: 'Nederlands',
  'no-NB': 'Norsk (bokmål)',
  pl: 'Polski',
  'pt-BR': 'Português (Brasileiro)',
  ro: 'Română',
  ru: 'Русский',
  sk: 'Slovenčina',
  sv: 'Svenska',
  vi: 'Tiếng Việt',
  'zh-CN': '中文 (Mainland China)',
  'zh-HK': '中文 (Hong Kong)',
  'zh-TW': '中文 (Taiwan)',
};
const LOCALE_TO_FACEBOOK_LOCALE = {
  ar: 'ar_AR',
  cs: 'cs_CZ',
  da: 'da_DK',
  de: 'de_DE',
  el: 'el_GR',
  en: 'en_US',
  es: 'es_ES',
  et: 'et_EE',
  fi: 'fi_FI',
  fr: 'fr_FR',
  hr: 'hr_HR',
  id: 'id_ID',
  it: 'it_IT',
  ja: 'ja_JP',
  ko: 'ko_KR',
  nl: 'nl_NL',
  no: 'no_NB',
  'no-NB': 'no_NB',
  pl: 'pl_PL',
  'pt-BR': 'pt_BR',
  ro: 'ro_RO',
  ru: 'ru_RU',
  sk: 'sk_SK',
  sv: 'sv_SE',
  vn: 'vi_VN',
  'zh-cn': 'zh_CN',
  'zh-hk': 'zh_HK',
  'zh-tw': 'zh_TW',
};

const TIME = {
  HOURLY: 'hourly',
  DAILY: 'daily',
  MONTHLY: 'monthly',
  YEARLY: 'yearly',
};

const failedRequestType = {
  ZONE: 'zone',
  GRID: 'grid',
};

export {
  modeColor,
  modeOrder,
  PRODUCTION_MODES,
  STORAGE_MODES,
  DEFAULT_FLAG_SIZE,
  DATA_FETCH_INTERVAL,
  LANGUAGE_NAMES,
  LOCALE_TO_FACEBOOK_LOCALE,
  TIME,
  failedRequestType,
};
