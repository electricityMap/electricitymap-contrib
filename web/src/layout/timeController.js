import React from 'react';
import { connect } from 'react-redux';
import TimeSlider from '../components/timeslider_new';

import { useCurrentDatetimes } from '../hooks/redux';
import { useFeatureToggle } from '../hooks/router';
import { dispatchApplication } from '../store';
import styled from 'styled-components';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const handleTimeAggregationChange = (aggregate) => {
  dispatchApplication('selectedTimeAggregate', aggregate);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
  selectedTimeAggregate: state.application.selectedTimeAggregate,
});

const StyledTimeSlider = styled(TimeSlider)`
  position: absolute;
  bottom: 0;
  padding: 12px 24px;
  background: white;
  left: 10px;
  bottom: 10px;
  border-radius: 15px;
  text-align: center;
  overflow-y: visible;
  width: calc((14vw + 16rem) - 70px); // Ensures it is smaller than countrypanel
  z-index: 999; // TODO: find the needed one
  position: fixed;
  box-shadow: rgba(0, 0, 0, 0.66) 0px 10px 36px 0px, rgba(0, 0, 0, 0.06) 0px 0px 0px 1px;

  .time-slider-axis-container {
    width: 100%;
    height: 20px;
    overflow: visible;
  }

  .domain {
    display: none;
  }

  @media (max-width: 767px) {
    padding-top: 4px;
    padding-bottom: 10px;
    padding-top: 20px;
    padding-left: 12px;
    padding-right: 12px;
    box-sizing: border-box;
    bottom: 0px;
    left: 0px;
    width: 100%;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
  }
`;

const TimeController = ({ selectedZoneTimeIndex, selectedTimeAggregate }) => {
  const datetimes = useCurrentDatetimes();
  const isHistoryFeatureEnabled = useFeatureToggle('history');

  if (!isHistoryFeatureEnabled) {
    return null;
  }

  const startTime = datetimes[0];
  const endTime = datetimes[datetimes.length - 1];

  return (
    <StyledTimeSlider
      onChange={handleZoneTimeIndexChange}
      selectedTimeIndex={selectedZoneTimeIndex}
      handleTimeAggregationChange={handleTimeAggregationChange}
      selectedTimeAggregate={selectedTimeAggregate}
      datetimes={datetimes}
      startTime={startTime}
      endTime={endTime}
    />
  );
};

export default connect(mapStateToProps)(TimeController);
