import React from 'react';
import getSymbolFromCurrency from 'currency-symbol-map';
import { TimeDisplay } from '../timeDisplay';

import Tooltip from '../tooltip';
import styled from 'styled-components';

const StyledTimeDisplay = styled(TimeDisplay)`
  font-size: smaller;
  margin-top: 0px;
`;

const PriceTooltip = ({ position, zoneData, onClose }) => {
  if (!zoneData) {
    return null;
  }

  const priceIsDefined = zoneData.price && typeof zoneData.price.value === 'number';
  const currency = priceIsDefined ? getSymbolFromCurrency(zoneData.price.currency) : '?';
  const value = priceIsDefined ? zoneData.price.value : '?';

  return (
    <Tooltip id="price-tooltip" position={position} onClose={onClose}>
      <StyledTimeDisplay date={zoneData.stateDatetime} />
      {value} {currency} / MWh
    </Tooltip>
  );
};

export default PriceTooltip;
