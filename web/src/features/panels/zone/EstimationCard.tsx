import Accordion from 'components/Accordion';
import FeedbackCard, { SurveyResponseProps } from 'components/app-survey/FeedbackCard';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { useAtom, useAtomValue } from 'jotai';
import { ChartNoAxesColumn, CircleDashed, TrendingUpDown } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaGithub } from 'react-icons/fa6';
import { ZoneMessage } from 'types';
import trackEvent from 'utils/analytics';
import { EstimationMethods, isTSAModel, TrackEvent } from 'utils/constants';
import {
  feedbackCardCollapsedNumberAtom,
  hasEstimationFeedbackBeenSeenAtom,
} from 'utils/state/atoms';

import { showEstimationFeedbackCard } from './util';

function postSurveyResponse({
  feedbackScore,
  inputText,
  reference: surveyReference,
}: SurveyResponseProps) {
  fetch(`https://hooks.zapier.com/hooks/catch/14671709/3l9daod/`, {
    method: 'POST',
    body: JSON.stringify({
      score: feedbackScore,
      feedback: inputText,
      reference: surveyReference,
    }),
  });
}

export default function EstimationCard({
  cardType,
  estimationMethod,
  estimatedPercentage,
  zoneMessage,
}: {
  cardType: string;
  estimationMethod?: EstimationMethods;
  estimatedPercentage?: number;
  zoneMessage?: ZoneMessage;
}) {
  const { t } = useTranslation();
  const [isFeedbackCardVisible, setIsFeedbackCardVisible] = useState(false);
  const feedbackCardCollapsedNumber = useAtomValue(feedbackCardCollapsedNumberAtom);
  const feedbackEnabled = useFeatureFlag('feedback-estimation-labels');
  const [hasFeedbackCardBeenSeen, setHasFeedbackCardBeenSeen] = useAtom(
    hasEstimationFeedbackBeenSeenAtom
  );

  useEffect(() => {
    setIsFeedbackCardVisible(
      feedbackEnabled &&
        showEstimationFeedbackCard(
          feedbackCardCollapsedNumber,
          isFeedbackCardVisible,
          hasFeedbackCardBeenSeen,
          setHasFeedbackCardBeenSeen
        )
    );
  }, [
    feedbackEnabled,
    feedbackCardCollapsedNumber,
    isFeedbackCardVisible,
    hasFeedbackCardBeenSeen,
    setHasFeedbackCardBeenSeen,
  ]);

  switch (cardType) {
    case 'outage': {
      return <OutageCard zoneMessage={zoneMessage} estimationMethod={estimationMethod} />;
    }
    case 'aggregated': {
      return <AggregatedCard estimatedPercentage={estimatedPercentage} />;
    }
    case 'estimated': {
      return (
        <div>
          {isTSAModel(estimationMethod) ? (
            <EstimatedTSACard />
          ) : (
            <EstimatedCard estimationMethod={estimationMethod} />
          )}
          {isFeedbackCardVisible && isTSAModel(estimationMethod) && (
            <FeedbackCard
              surveyReference={estimationMethod}
              postSurveyResponse={postSurveyResponse}
              primaryQuestion={t('feedback-card.estimations.primary-question')}
              secondaryQuestionHigh={t('feedback-card.estimations.secondary-question')}
              secondaryQuestionLow={t('feedback-card.estimations.secondary-question')}
              subtitle={t('feedback-card.estimations.subtitle')}
            />
          )}
        </div>
      );
    }
  }
}

function BaseCard({
  estimationMethod,
  estimatedPercentage,
  zoneMessage,
  icon,
  showMethodologyLink,
  textColorTitle,
  cardType,
}: {
  estimationMethod?: EstimationMethods;
  estimatedPercentage?: number;
  zoneMessage?: ZoneMessage;
  icon: React.ReactElement;
  showMethodologyLink: boolean;
  textColorTitle: string;
  cardType: string;
}) {
  const [feedbackCardCollapsedNumber, setFeedbackCardCollapsedNumber] = useAtom(
    feedbackCardCollapsedNumberAtom
  );
  const isCollapsedDefault = estimationMethod === 'outage' ? false : true;
  const [isCollapsed, setIsCollapsed] = useState(isCollapsedDefault);

  const trackToggle = () => {
    if (isCollapsed) {
      trackEvent(TrackEvent.ESTIMATION_CARD_EXPANDED, { cardType: cardType });
    }
    setFeedbackCardCollapsedNumber(feedbackCardCollapsedNumber + 1);
  };
  const { t } = useTranslation();

  const title = useGetEstimationTranslation('title', estimationMethod);

  const bodyText = useGetEstimationTranslation(
    'body',
    estimationMethod,
    estimatedPercentage
  );

  return (
    <div
      className={`w-full rounded-lg px-3 py-1.5 ${
        estimationMethod == 'outage'
          ? 'bg-warning/20 dark:bg-warning-dark/20'
          : 'bg-neutral-100 dark:bg-gray-800'
      } mb-4 border border-neutral-200 transition-all dark:border-gray-700`}
    >
      <Accordion
        onClick={() => trackToggle()}
        className={textColorTitle}
        icon={icon}
        title={title}
        isCollapsed={isCollapsed}
        setState={setIsCollapsed}
      >
        <div className="flex flex-col gap-2">
          <div
            data-testid="body-text"
            className={`text-sm font-normal text-neutral-600 dark:text-neutral-400`}
          >
            {estimationMethod != 'outage' && bodyText}
            {estimationMethod == 'outage' && (
              <ZoneMessageBlock zoneMessage={zoneMessage} />
            )}
          </div>
          {showMethodologyLink && (
            <a
              href="https://www.electricitymaps.com/methodology#missing-data"
              target="_blank"
              rel="noreferrer"
              data-testid="methodology-link"
              className={`text-sm font-semibold text-black underline dark:text-white`}
              onClick={() => {
                trackEvent(TrackEvent.ESTIMATION_CARD_METHODOLOGY_LINK_CLICKED, {
                  cardType: cardType,
                });
              }}
            >
              {t(`estimation-card.link`)}
            </a>
          )}
        </div>
      </Accordion>
    </div>
  );
}

function OutageCard({
  zoneMessage,
  estimationMethod,
}: {
  zoneMessage?: ZoneMessage;
  estimationMethod?: string;
}) {
  const { t } = useTranslation();
  const zoneMessageText =
    estimationMethod === EstimationMethods.THRESHOLD_FILTERED
      ? { message: t(`estimation-card.${EstimationMethods.THRESHOLD_FILTERED}.body`) }
      : zoneMessage;
  return (
    <BaseCard
      estimationMethod={EstimationMethods.OUTAGE}
      zoneMessage={zoneMessageText}
      icon={<TrendingUpDown size={16} />}
      showMethodologyLink={false}
      textColorTitle="text-warning dark:text-warning-dark"
      cardType="outage-card"
    />
  );
}

function AggregatedCard({ estimatedPercentage }: { estimatedPercentage?: number }) {
  return (
    <BaseCard
      estimationMethod={EstimationMethods.AGGREGATED}
      estimatedPercentage={estimatedPercentage}
      zoneMessage={undefined}
      icon={<ChartNoAxesColumn size={16} />}
      showMethodologyLink={false}
      textColorTitle="text-black dark:text-white"
      cardType="aggregated-card"
    />
  );
}

function EstimatedCard({
  estimationMethod,
}: {
  estimationMethod: EstimationMethods | undefined;
}) {
  return (
    <BaseCard
      estimationMethod={estimationMethod}
      zoneMessage={undefined}
      icon={<TrendingUpDown size={16} />}
      showMethodologyLink={true}
      textColorTitle={'text-warning dark:text-warning-dark'}
      cardType="estimated-card"
    />
  );
}

function EstimatedTSACard() {
  return (
    <BaseCard
      estimationMethod={EstimationMethods.TSA}
      zoneMessage={undefined}
      icon={<CircleDashed size={16} />}
      showMethodologyLink={true}
      textColorTitle="text-black dark:text-white"
      cardType="estimated-card"
    />
  );
}

function truncateString(string_: string, number_: number) {
  return string_.length <= number_ ? string_ : string_.slice(0, number_) + '...';
}

function ZoneMessageBlock({ zoneMessage }: { zoneMessage?: ZoneMessage }) {
  const { t } = useTranslation();

  if (!zoneMessage || !zoneMessage.message) {
    return null;
  }

  return (
    <span className="inline overflow-hidden">
      {truncateString(zoneMessage.message, 300)}{' '}
      {zoneMessage?.issue && zoneMessage.issue != 'None' && (
        <span className="mt-1 inline-flex">
          <a
            className="inline-flex items-center gap-1 text-sm font-semibold text-black underline dark:text-white"
            href={`https://github.com/electricitymaps/electricitymaps-contrib/issues/${zoneMessage.issue}`}
          >
            <span className="pl-1 underline">{t('estimation-card.outage-details')}</span>
            <FaGithub size={18} />
          </a>
        </span>
      )}
    </span>
  );
}
