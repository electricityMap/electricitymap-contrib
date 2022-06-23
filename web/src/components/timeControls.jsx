import React from 'react';
import { useTranslation } from '../helpers/translation';
import styled, { css } from 'styled-components';
import { formatDate, formatTimeRange } from '../helpers/formatting';
import { TIME } from '../helpers/constants';
import { useSelector } from 'react-redux';

const Title = styled.span`
  font-size: calc(11px + 0.2vw);
  font-weight: 700;
  white-space: nowrap;
  height: 100%;
  display: flex;
  align-items: center;
  @media (max-width: 768px) {
    font-size: 13px;
  }
`;
const DateRangeOption = styled.span`
  font-size: 0.8rem;
  padding: 8px;
  margin-right: 5px;
  padding-left: 12px;
  padding-right: 12px;
  border-radius: 16px;
  white-space: nowrap;
  text-transform: capitalize;
  cursor: pointer;
  font-weight: ${(props) => (props.active ? 700 : 500)};
  opacity: ${(props) => (props.active ? 1 : 0.5)};
  ${(props) =>
    props.active &&
    css`
      background-color: white;
      box-shadow: 0.1px 0.1px 5px rgba(0, 0, 0, 0.1);
    `}
`;

const DateDisplay = styled.div`
  display: ${(props) => (props.loading ? 'none' : 'flex')};
  align-items: center;
  font-size: calc(9px + 0.2vw);
  background-color: #f0f0f0;
  padding-left: 12px;
  padding-right: 12px;
  border-radius: 30px;
  max-width: 300px;
  white-space: nowrap;
  height: 100%;
`;

const Wrapper = styled.div`
  display: flex;
  justify-content: space-between;
  height: 30px;
  @media (max-width: 315px) {
    flex-direction: column-reverse;
    align-items: center;
  }
`;

const DateOptionWrapper = styled.div`
  display: flex;
  justify-content: flex-start;
  padding-top: 8px;
`;

const getOptions = (language) => [
  {
    key: TIME.HOURLY,
    label: formatTimeRange(language, TIME.HOURLY),
  },
  {
    key: TIME.DAILY,
    label: formatTimeRange(language, TIME.DAILY),
  },
  {
    key: TIME.MONTHLY,
    label: formatTimeRange(language, TIME.MONTHLY),
  },
  {
    key: TIME.YEARLY,
    label: formatTimeRange(language, TIME.YEARLY),
  },
];

const TimeControls = ({ date, selectedTimeAggregate, handleTimeAggregationChange, isLoading }) => {
  const { __, i18n } = useTranslation();
  const options = getOptions(i18n.language);
  const zoneDatetimes = useSelector((state) => state.data.zoneDatetimes);

  return (
    <div>
      <Wrapper>
        <Title>{__('time-controller.title')}</Title>
        <DateDisplay loading={isLoading}>{formatDate(date, i18n.language, selectedTimeAggregate)}</DateDisplay>
      </Wrapper>
      <DateOptionWrapper>
        {options.map((o) => (
          <DateRangeOption
            key={o.key}
            active={o.key === selectedTimeAggregate}
            onClick={() => {
              handleTimeAggregationChange(o.key, zoneDatetimes);
            }}
          >
            {o.label}
          </DateRangeOption>
        ))}
      </DateOptionWrapper>
    </div>
  );
};

export default TimeControls;
