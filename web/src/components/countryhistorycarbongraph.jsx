import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';

import { getTooltipPosition } from '../helpers/graph';
import { useCo2ColorScale } from '../hooks/theme';
import { useCurrentZoneHistory, useCurrentZoneHistoryDatetimes } from '../hooks/redux';

import MapCountryTooltip from './tooltips/mapcountrytooltip';
import AreaGraph from './graph/areagraph';
import { getCO2IntensityByMode } from '../helpers/zonedata';

const prepareGraphData = (historyData, co2ColorScale, electricityMixMode) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const data = historyData.map((d) => ({
    carbonIntensity: getCO2IntensityByMode(d, electricityMixMode),
    datetime: new Date(d.stateDatetime),
    // Keep a pointer to original data
    meta: d,
  }));
  const layerKeys = ['carbonIntensity'];
  const layerFill = (key) => (d) => co2ColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = (state) => ({
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
});

const CountryHistoryCarbonGraph = ({ electricityMixMode, isMobile }) => {
  const [graphIndex, setGraphIndex] = useState(0);
  const [tooltip, setTooltip] = useState(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);
  const co2ColorScale = useCo2ColorScale();

  const historyData = useCurrentZoneHistory();
  const datetimes = useCurrentZoneHistoryDatetimes();
  const startTime = datetimes.at(0);
  const endTime = datetimes.at(-1);

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData, co2ColorScale, electricityMixMode),
    [historyData, co2ColorScale, electricityMixMode]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(
    () => (timeIndex) => {
      setGraphIndex(timeIndex);
      setSelectedLayerIndex(0); // Select the first (and only) layer even when hovering over graph background.
    },
    [setSelectedLayerIndex]
  );
  const mouseOutHandler = useMemo(
    () => () => {
      setSelectedLayerIndex(null);
      setGraphIndex(null);
    },
    [setSelectedLayerIndex]
  );
  // Graph marker callbacks
  const markerUpdateHandler = useMemo(
    () => (position, datapoint) => {
      setTooltip({
        position: getTooltipPosition(isMobile, position),
        zoneData: datapoint.meta,
      });
    },
    [setTooltip, isMobile]
  );
  const markerHideHandler = useMemo(
    () => () => {
      setTooltip(null);
    },
    [setTooltip]
  );

  return (
    <React.Fragment>
      <AreaGraph
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        startTime={startTime}
        endTime={endTime}
        valueAxisLabel="g / kWh"
        backgroundMouseMoveHandler={mouseMoveHandler}
        backgroundMouseOutHandler={mouseOutHandler}
        layerMouseMoveHandler={mouseMoveHandler}
        layerMouseOutHandler={mouseOutHandler}
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        selectedTimeIndex={graphIndex}
        selectedLayerIndex={selectedLayerIndex}
        isMobile={isMobile}
        height="8em"
      />
      {tooltip && (
        <MapCountryTooltip
          position={tooltip.position}
          zoneData={tooltip.zoneData}
          onClose={() => {
            setTooltip(null);
          }}
        />
      )}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryCarbonGraph);
