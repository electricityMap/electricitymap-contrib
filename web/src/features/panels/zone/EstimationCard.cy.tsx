import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';
import { EstimationMethods } from 'utils/constants';

import EstimationCard from './EstimationCard';

const queryClient = new QueryClient();

describe('EstimationCard with FeedbackCard', () => {
  beforeEach(() => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard
            cardType="estimated"
            estimationMethod={EstimationMethods.CONSTRUCT_BREAKDOWN}
            zoneMessage={undefined}
          />
        </QueryClientProvider>
      </I18nextProvider>
    );
  });

  // TODO(Viktor): Move this to E2E tests, AVO-240
  it.skip('feedback card should only be visible when collapse button has been clicked', () => {
    cy.intercept('/feature-flags', {
      body: { 'feedback-estimation-labels': true },
    });
    cy.get('[data-testid=feedback-card]').should('not.exist');
    cy.get('[data-testid=collapse-button]').click();
    cy.get('[data-testid=feedback-card]').should('exist');
    cy.get('[data-testid=collapse-button]').click();
    cy.get('[data-testid=feedback-card]').should('exist');
  });

  it.skip('feedback card should only be visible if feature-flag is enabled', () => {
    cy.intercept('/feature-flags', {
      body: { 'feedback-estimation-labels': false },
    });
    cy.get('[data-testid=feedback-card]').should('not.exist');
    cy.get('[data-testid=collapse-button]').click();
    cy.get('[data-testid=feedback-card]').should('exist');
  });
});

describe('EstimationCard with known estimation method', () => {
  beforeEach(() => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard
            cardType="estimated"
            estimationMethod={EstimationMethods.TSA}
            zoneMessage={undefined}
          />
        </QueryClientProvider>
      </I18nextProvider>
    );
  });

  it('Estimation card contains expected information', () => {
    cy.get('[data-testid=title]').contains('Data is preliminary');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The data for this hour has not been reported yet and is based on preliminary data.'
    );
  });

  it('Toggles when collapse button is clicked', () => {
    cy.get('[data-testid="collapse-up"]').should('not.exist');
    cy.get('[data-testid="collapse-down"]').should('exist');
    cy.get('[data-testid="body-text"]').should('not.exist');
    cy.get('[data-testid="methodology-link"]').should('not.exist');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="collapse-up"]').should('exist');
    cy.get('[data-testid="collapse-down"]').should('not.exist');
    cy.get('[data-testid="body-text"]').should('exist');
    cy.get('[data-testid="methodology-link"]').should('exist');
  });
});

describe('EstimationCard', () => {
  it('Estimation card with unknown estimation method contains expected information', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard cardType="estimated" zoneMessage={undefined} />
        </QueryClientProvider>
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').contains('Data is estimated');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The published data for this zone is unavailable or incomplete. The data shown on the map is estimated using our best effort, but might differ from the actual values.'
    );
  });

  it('Estimation card with unknown card type should not return an estimation card', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard cardType="" zoneMessage={undefined} />
        </QueryClientProvider>
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').should('not.exist');
  });
});

describe('OutageCard', () => {
  beforeEach(() => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard
            cardType="outage"
            estimationMethod={EstimationMethods.CONSTRUCT_BREAKDOWN}
            zoneMessage={{ message: 'Outage Message', issue: 'issue' }}
          />
        </QueryClientProvider>
      </I18nextProvider>
    );
  });

  it('Outage message contains expected information', () => {
    cy.get('[data-testid=title]').contains('Ongoing issues');
  });

  it('For outage start as expanded and toggles collapse when collapse button is clicked', () => {
    cy.get('[data-testid="collapse-up"]').should('exist');
    cy.get('[data-testid="collapse-down"]').should('not.exist');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="collapse-up"]').should('not.exist');
    cy.get('[data-testid="collapse-down"]').should('exist');
  });
});

describe('AggregatedCard', () => {
  it('Aggregated card with estimation contains expected information', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard
            cardType="aggregated"
            estimatedPercentage={50}
            zoneMessage={undefined}
          />
        </QueryClientProvider>
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').contains('Data is aggregated');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The data consists of an aggregation of hourly values. 50% of the production values are estimated.'
    );
  });

  it('Aggregated card contains expected information', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard
            cardType="aggregated"
            estimationMethod={EstimationMethods.CONSTRUCT_BREAKDOWN}
            zoneMessage={undefined}
          />
        </QueryClientProvider>
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').contains('Data is aggregated');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The data consists of an aggregation of hourly values.'
    );
  });
});
