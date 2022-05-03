import React from 'react';
import { isFinite } from 'lodash';

import { getShortenedZoneNameWithCountry } from '../../helpers/translation';
import { useCo2ColorScale } from '../../hooks/theme';
import { flagUri } from '../../helpers/flags';
import styled from 'styled-components';

export const CarbonIntensity = ({ intensity }) => {
  const co2ColorScale = useCo2ColorScale();

  return (
    <>
      <div className="emission-rect" style={{ backgroundColor: co2ColorScale(intensity) }} />
      {' '}
      <b>{Math.round(intensity) || '?'}</b> gCO₂eq/kWh
    </>
  );
};

export const MetricRatio = ({ value, total, format }) => (
  <small>{`(${isFinite(value) ? format(value) : '?'} / ${isFinite(total) ? format(total) : '?'})`}</small>
);

const Flag = styled.img`
  margin-right: 4px;
`;

export const ZoneName = ({ zone }) => (
  <>
    <Flag className="flag" alt={`flag-${zone}`} src={flagUri(zone)} />
    {getShortenedZoneNameWithCountry(zone)}
  </>
);
