import { describe, expect, it } from 'vitest';

import { filterExchanges } from './arrows';

const mockExchangesToExcludeZoneView = ['exchange1', 'exchange2', 'exchange4'];

const mockExchangesToExcludeCountryView = ['exchange3', 'exchange5'];

const mockExchangesResponses = {
  exchange1: {
    '2024-01-31T12:00:00Z': { co2intensity: 137.68, netFlow: -44 },
    '2024-01-31T13:00:00Z': { co2intensity: 133.44, netFlow: -57 },
  },
  exchange2: {
    '2024-01-31T14:00:00Z': { co2intensity: 131.44, netFlow: -56 },
    '2024-01-31T15:00:00Z': { co2intensity: 135.82, netFlow: -55 },
  },
  exchange3: {
    '2024-01-31T16:00:00Z': { co2intensity: 168.29, netFlow: -55 },
    '2024-01-31T17:00:00Z': { co2intensity: 199.8, netFlow: -13 },
  },
  exchange4: {
    '2024-01-31T18:00:00Z': { co2intensity: 199.73, netFlow: -18 },
    '2024-01-31T19:00:00Z': { co2intensity: 195.2, netFlow: -18 },
  },
  exchange5: {
    '2024-01-31T20:00:00Z': { co2intensity: 188.22, netFlow: -11 },
    '2024-01-31T21:00:00Z': { co2intensity: 178.86, netFlow: -50 },
  },
};

const expectedAfterZoneViewFilter = {
  exchange3: mockExchangesResponses.exchange3,
  exchange5: mockExchangesResponses.exchange5,
};

const expectedAfterCountryViewFilter = {
  exchange1: mockExchangesResponses.exchange1,
  exchange2: mockExchangesResponses.exchange2,
  exchange4: mockExchangesResponses.exchange4,
};

describe('filterExchanges', () => {
  it('should return an empty object if no exchanges are passed', () => {
    expect(filterExchanges({}, mockExchangesToExcludeZoneView)).toEqual({});
  });

  it('should return all exchanges if no exclusions are passed', () => {
    expect(filterExchanges(mockExchangesResponses, [])).toEqual(mockExchangesResponses);
  });

  it('should filter out zone view exchanges', () => {
    expect(
      filterExchanges(mockExchangesResponses, mockExchangesToExcludeZoneView)
    ).toEqual(expectedAfterZoneViewFilter);
  });

  it('should filter out country view exchanges', () => {
    expect(
      filterExchanges(mockExchangesResponses, mockExchangesToExcludeCountryView)
    ).toEqual(expectedAfterCountryViewFilter);
  });

  it('should throw an error if exchanges is not an object', () => {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore This is deliberately passing a non-object to test the function.
    expect(() => filterExchanges(null, mockExchangesToExcludeZoneView)).toThrow(
      TypeError
    );
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore This is deliberately passing a non-object to test the function.
    expect(() => filterExchanges(undefined, mockExchangesToExcludeZoneView)).toThrow(
      TypeError
    );
  });

  it('should throw an error if exclusions is not an array', () => {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore This is deliberately passing a non-array to test the function.
    expect(() => filterExchanges(mockExchangesResponses, null)).toThrow(TypeError);
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore This is deliberately passing a non-array to test the function.
    expect(() => filterExchanges(mockExchangesResponses, undefined)).toThrow(TypeError);
  });
});
