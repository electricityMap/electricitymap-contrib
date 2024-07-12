import { describe, expect, it, vi } from 'vitest';

import { TimeAverages } from './constants';
import {
  formatCo2,
  formatDate,
  formatEnergy,
  formatPower,
  getDateTimeFormatOptions,
} from './formatting';

describe('formatEnergy', () => {
  it('handles NaN input', () => {
    const actual = formatEnergy({ value: Number.NaN });
    const expected = Number.NaN;
    expect(actual).to.deep.eq(expected);
  });

  it('handles custom number of digits', () => {
    const actual = formatEnergy({ value: 1.234_567, numberDigits: 4 });
    const expected = '1.235 MWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles default number kWh', () => {
    const actual = formatEnergy({ value: 0.002_234_567 });
    const expected = '2.23 kWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles MWh', () => {
    const actual = formatEnergy({ value: 1.234_567 });
    const expected = '1.23 MWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GWh', () => {
    const actual = formatEnergy({ value: 1222.234_567 });
    const expected = '1.22 GWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TWh', () => {
    const actual = formatEnergy({ value: 1_222_000.234_567 });
    const expected = '1.22 TWh';
    expect(actual).to.deep.eq(expected);
  });

  it('Converts PWh to TWh', () => {
    const actual = formatEnergy({ value: 1_222_000_000.234_567 });
    const expected = '1220 TWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles zero input', () => {
    const actual = formatEnergy({ value: 0 });
    const expected = '0 Wh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 1 input for number of digits', () => {
    const actual = formatEnergy({ value: 12_313, numberDigits: 1 });
    const expected = '10 GWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 0 input for number of digits', () => {
    const actual = formatEnergy({ value: 12_313, numberDigits: 0 });
    const expected = '10 GWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles W with decimal', () => {
    const actual = formatPower({ value: 0.000_054_6, total: 0.0006 });
    const expected = '54.6 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles W without decimal', () => {
    const actual = formatPower({ value: 0.000_05, total: 0.0006 });
    const expected = '50 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles kW with decimal', () => {
    const actual = formatPower({ value: 0.000_05, total: 0.05 });
    const expected = '0.05 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles kW without decimal', () => {
    const actual = formatPower({ value: 0.003, total: 0.05 });
    const expected = '3 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles d and total being the same', () => {
    const actual = formatPower({ value: 0.05, total: 0.05 });
    const expected = '50 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles MW', () => {
    const actual = formatPower({ value: 0.009, total: 30 });
    const expected = '0.009 MW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GW', () => {
    const actual = formatPower({ value: 6.5, total: 70_000 });
    const expected = '0.0065 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GW with d being small', () => {
    const actual = formatPower({ value: 0.000_05, total: 70_000 });
    const expected = '0.00000005 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GW with d being very small', () => {
    const actual = formatPower({ value: 0.000_000_05, total: 70_000 });
    const expected = '~0 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GW with d being 0', () => {
    const actual = formatPower({ value: 0, total: 70_000 });
    const expected = '0 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TW', () => {
    const actual = formatPower({ value: 45, total: 890_000_000 });
    const expected = '0.000045 TW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TW with small d', () => {
    const actual = formatPower({ value: 0.000_05, total: 890_000_000 });
    const expected = '0.00000000005 TW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TW with bug precision', () => {
    const actual = formatPower({ value: 42_059.836_85, total: 890_000_000 });
    const expected = '0.0421 TW';
    expect(actual).to.deep.eq(expected);
  });
});

describe('formatPower', () => {
  it('handles NaN input', () => {
    const actual = formatPower({ value: Number.NaN });
    const expected = Number.NaN;
    expect(actual).to.deep.eq(expected);
  });

  it('handles custom number of digits', () => {
    const actual = formatPower({ value: 1.234_567, numberDigits: 4 });
    const expected = '1.235 MW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles default number kW', () => {
    const actual = formatPower({ value: 0.002_234_567 });
    const expected = '2.23 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles MW', () => {
    const actual = formatPower({ value: 1.234_567 });
    const expected = '1.23 MW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GW', () => {
    const actual = formatPower({ value: 1222.234_567 });
    const expected = '1.22 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TW', () => {
    const actual = formatPower({ value: 1_222_000.234_567 });
    const expected = '1.22 TW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles zero input', () => {
    const actual = formatPower({ value: 0 });
    const expected = '0 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 1 input for number of digits', () => {
    const actual = formatPower({ value: 12_313, numberDigits: 1 });
    const expected = '10 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 0 input for number of digits', () => {
    const actual = formatPower({ value: 12_313, numberDigits: 0 });
    const expected = '10 GW';
    expect(actual).to.deep.eq(expected);
  });
});

describe('formatCo2', () => {
  it('handles grams', () => {
    const actual = formatCo2({ value: 20 });
    const expected = '20 g';
    expect(actual).to.deep.eq(expected);
  });
  it('handles kilograms', () => {
    const actual = formatCo2({ value: 1000 });
    const expected = '1 kg';
    expect(actual).to.deep.eq(expected);
  });
  it('handles tonnes', () => {
    const actual = formatCo2({ value: 1_000_000 });
    const expected = '1 t';
    expect(actual).to.deep.eq(expected);
  });

  it('uses same unit as another value would', () => {
    const actual = formatCo2({ value: 23_500, total: 2_350_000 });
    const expected = '0.0235 t';
    expect(actual).to.deep.eq(expected);
  });

  it('adds decimals if comparing with tonnes', () => {
    const actual = formatCo2({ value: 200_500, total: 2_350_000 });
    const expected = '0.201 t';
    expect(actual).to.deep.eq(expected);
  });
  it('adds decimals if comparing with large tonnes', () => {
    const actual = formatCo2({ value: 200_500, total: 992_350_000 });
    const expected = '0.201 t';
    expect(actual).to.deep.eq(expected);
  });
  it('handles real data value', () => {
    const actual = formatCo2({ value: 740_703_650 });
    const expected = '741 t';
    expect(actual).to.deep.eq(expected);
  });
  it('handles kilotonnes', () => {
    const actual = formatCo2({ value: 99_000_000_000 });
    const expected = '99 kt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles megatonnes', () => {
    const actual = formatCo2({ value: 99_000_000_000_000 });
    const expected = '99 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles megatonnes close to 1Gt rounding down', () => {
    const actual = formatCo2({ value: 994_320_320_231_123 });
    const expected = '994 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values up to 1 trillion grams, rounding up', () => {
    const actual = formatCo2({ value: 999_900_000_000_000 });
    const expected = '1000 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values above 1 trillion', () => {
    const actual = formatCo2({ value: 6_700_000_000_000_000 });
    const expected = '6.7 Gt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values petatonnes', () => {
    const actual = formatCo2({ value: 1.5e21 });
    const expected = '1500 Tt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles negative values g', () => {
    const actual = formatCo2({ value: -9 });
    const expected = '−9 g';
    expect(actual).to.eq(expected);
  });
  it('handles negative values kg', () => {
    const actual = formatCo2({ value: -9000 });
    const expected = '−9 kg';
    expect(actual).to.eq(expected);
  });
  it('handles negative values t', () => {
    const actual = formatCo2({ value: -9_000_000 });
    const expected = '−9 t';
    expect(actual).to.eq(expected);
  });
  it('handles negative values kt', () => {
    const actual = formatCo2({ value: -9_000_000_000 });
    const expected = '−9 kt';
    expect(actual).to.eq(expected);
  });
  it('handles negative values Mt', () => {
    const actual = formatCo2({ value: -99_000_000_000_000 });
    const expected = '−99 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('uses same unit as another value would - negative t', () => {
    const actual = formatCo2({ value: -23_000, total: -2_350_000 });
    const expected = '−0.023 t';
    expect(actual).to.deep.eq(expected);
  });
  it('uses same unit as another value would - negative kg', () => {
    const actual = formatCo2({ value: -23_000, total: -24_000 });
    const expected = '−23 kg';
    expect(actual).to.deep.eq(expected);
  });
  it('handles real data value - negative', () => {
    const actual = formatCo2({ value: -740_703_650 });
    const expected = '−741 t';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values petatonnes - negative', () => {
    const actual = formatCo2({ value: -1.5e21 });
    const expected = '−1500 Tt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles megatonnes close to 1Gt rounding down - negative', () => {
    const actual = formatCo2({ value: -994_320_320_231_123 });
    const expected = '−994 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values up to 1 trillion grams, rounding up - negative', () => {
    const actual = formatCo2({ value: -999_900_000_000_000 });
    const expected = '−1000 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles negative values correct when value to match is positive', () => {
    const actual = formatCo2({ value: -1_400_000_000, total: 1_400_000_000 });
    const expected = '−1.4 kt';
    expect(actual).to.eq(expected);
  });
});

describe('getDateTimeFormatOptions', () => {
  it('handles hourly data', () => {
    const actual = getDateTimeFormatOptions(TimeAverages.HOURLY);
    const expected = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      timeZoneName: 'short',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('handles daily data', () => {
    const actual = getDateTimeFormatOptions(TimeAverages.DAILY);
    const expected = {
      dateStyle: 'long',
      timeZone: 'UTC',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('handles monthly data', () => {
    const actual = getDateTimeFormatOptions(TimeAverages.MONTHLY);
    const expected = {
      month: 'long',
      year: 'numeric',
      timeZone: 'UTC',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('handles yearly data', () => {
    const actual = getDateTimeFormatOptions(TimeAverages.YEARLY);
    const expected = {
      year: 'numeric',
      timeZone: 'UTC',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('logs an error on unknown data', () => {
    // Spy on console.error to check if it is called
    const consoleErrorSpy = vi.spyOn(console, 'error');

    const actual = getDateTimeFormatOptions('ThisAggregateDoesNotExist' as TimeAverages);
    const expected = {};
    expect(actual).to.deep.eq(expected);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'ThisAggregateDoesNotExist is not implemented'
    );

    // Restore the spy
    consoleErrorSpy.mockRestore();
  });
});

// These tests rely on the internal implementation of the `Intl.DateTimeFormat` object
// and may fail if the Node version changes. Simply update the snapshot if that is the case.
describe('formatDate', () => {
  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles hourly data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeAverages.HOURLY
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles daily data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeAverages.DAILY
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles monthly data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeAverages.MONTHLY
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles yearly data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeAverages.YEARLY
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it('logs an error on unknown data', () => {
    // Spy on console.error to check if it is called
    const consoleErrorSpy = vi.spyOn(console, 'error');

    const actual = formatDate(
      new Date('2021-01-01T00:00:00Z'),
      'en',
      'ThisAggregateDoesNotExist' as TimeAverages
    );
    const expected = '1/1/2021';
    expect(actual).to.deep.eq(expected);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'ThisAggregateDoesNotExist is not implemented'
    );

    // Restore the spy
    consoleErrorSpy.mockRestore();
  });
});
