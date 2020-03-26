import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';

import { dispatchApplication } from '../store';
import { getCo2Scale } from '../helpers/scales';
import { __, getFullZoneName } from '../helpers/translation';
import { navigateToURL } from '../helpers/router';
import { flagUri } from '../helpers/flags';

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-scale'),
  require('d3-selection'),
);

function withZoneRankings(zones) {
  return zones.map((zone) => {
    const ret = Object.assign({}, zone);
    ret.ranking = zones.indexOf(zone) + 1;
    return ret;
  });
}

function getCo2IntensityAccessor(electricityMixMode) {
  return d => (electricityMixMode === 'consumption'
    ? d.co2intensity
    : d.co2intensityProduction);
}

function sortAndValidateZones(zones, accessor) {
  return zones
    .filter(accessor)
    .sort((x, y) => {
      if (!x.co2intensity && !x.countryCode) {
        return d3.ascending(
          x.shortname || x.countryCode,
          y.shortname || y.countryCode,
        );
      }
      return d3.ascending(
        accessor(x) || Infinity,
        accessor(y) || Infinity,
      );
    });
}

function processZones(zonesData, accessor) {
  const zones = d3.values(zonesData);
  const validatedAndSortedZones = sortAndValidateZones(zones, accessor);
  return withZoneRankings(validatedAndSortedZones);
}

function zoneMatchesQuery(zone, queryString) {
  if (!queryString) return true;
  const queries = queryString.split(' ');
  return queries.every(query =>
    getFullZoneName(zone.countryCode)
      .toLowerCase()
      .indexOf(query.toLowerCase()) !== -1);
}

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  gridZones: state.data.grid.zones,
  searchQuery: state.application.searchQuery,
});

const ZoneList = ({
  colorBlindModeEnabled,
  electricityMixMode,
  gridZones,
  searchQuery,
}) => {
  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const co2IntensityAccessor = getCo2IntensityAccessor(electricityMixMode);
  const zones = processZones(gridZones, co2IntensityAccessor)
    .filter(z => zoneMatchesQuery(z, searchQuery));

  const ref = React.createRef();
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);

  // Click action
  const handleClick = (countryCode) => {
    dispatchApplication('centeredZoneName', countryCode);
    navigateToURL(`/zone/${countryCode}`);
  };

  // Keyboard navigation
  useEffect(() => {
    const scrollToItemIfNeeded = (index) => {
      const item = ref.current && ref.current.children[index];
      if (!item) return;

      const parent = item.parentNode;
      const parentComputedStyle = window.getComputedStyle(parent, null);
      const parentBorderTopWidth = parseInt(parentComputedStyle.getPropertyValue('border-top-width'), 10);
      const overTop = item.offsetTop - parent.offsetTop < parent.scrollTop;
      const overBottom = (item.offsetTop - parent.offsetTop + item.clientHeight - parentBorderTopWidth) > (parent.scrollTop + parent.clientHeight);
      const alignWithTop = overTop && !overBottom;

      if (overTop || overBottom) {
        item.scrollIntoView(alignWithTop);
      }
    };
    const keyHandler = (e) => {
      if (e.key) {
        if (e.key === 'Enter' && zones[selectedItemIndex]) {
          handleClick(zones[selectedItemIndex].countryCode);
        } else if (e.key === 'ArrowUp') {
          const prevItemIndex = selectedItemIndex === null ? 0 : Math.max(0, selectedItemIndex - 1);
          scrollToItemIfNeeded(prevItemIndex);
          setSelectedItemIndex(prevItemIndex);
        } else if (e.key === 'ArrowDown') {
          const nextItemIndex = selectedItemIndex === null ? 0 : Math.min(zones.length - 1, selectedItemIndex + 1);
          scrollToItemIfNeeded(nextItemIndex);
          setSelectedItemIndex(nextItemIndex);
        } else if (e.key.match(/^[A-z]$/)) {
          // Focus on the first item if modified the search query
          scrollToItemIfNeeded(0);
          setSelectedItemIndex(0);
        }
      }
    };
    document.addEventListener('keyup', keyHandler);
    return () => {
      document.removeEventListener('keyup', keyHandler);
    };
  });

  return (
    <div className="zone-list" ref={ref}>
      {zones.map((zone, ind) => (
        <a
          key={zone.shortname}
          className={selectedItemIndex === ind ? 'selected' : ''}
          onClick={() => handleClick(zone.countryCode)}
        >
          <div className="ranking">{zone.ranking}</div>
          <img className="flag" src={flagUri(zone.countryCode, 32)} />
          <div className="name">
            <div className="zone-name">{__(`zoneShortName.${zone.countryCode}.zoneName`)}</div>
            <div className="country-name">{__(`zoneShortName.${zone.countryCode}.countryName`)}</div>
          </div>
          <div
            className="co2-intensity-tag"
            style={{ backgroundColor: co2ColorScale(co2IntensityAccessor(zone)) }}
          />
        </a>
      ))}
    </div>
  );
};

export default connect(mapStateToProps)(ZoneList);
