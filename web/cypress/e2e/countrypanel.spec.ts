// TODO: Convert to component test
describe('Country Panel', () => {
  beforeEach(() => {
    cy.intercept('/dummy').as('dummy');
    cy.interceptAPI('v6/state/hourly');
  });

  it('interacts with details', () => {
    cy.interceptAPI('v6/details/hourly/DK-DK2');
    cy.visit('/zone/DK-DK2?skip-onboarding=true&lang=en-GB');
    cy.waitForAPISuccess('v6/state/hourly');
    cy.waitForAPISuccess('v6/details/hourly/DK-DK2');

    cy.contains('East Denmark');
    cy.contains('Carbon Intensity');
    cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').contains('232');
    // cy.get('[data-test-id=zone-header-lowcarbon-gauge]').trigger('mouseover');
    // cy.contains('Includes renewables and nuclear');
    cy.get('[data-test-id=zone-header-lowcarbon-gauge]').trigger('mouseout');

    cy.contains('Carbon emissions').should('have.attr', 'aria-checked', 'false');
    cy.contains('Carbon emissions').click().should('have.attr', 'aria-checked', 'true');
    cy.contains('0 t/min');
    cy.contains('Electricity consumption').click();

    // // test graph tooltip
    // cy.get('[data-test-id=details-carbon-graph]').trigger('mousemove', 'left');
    // // ensure hovering the graph does not change underlying data
    // cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').should(
    //   'have.text',
    //   '232'
    // );
    cy.get('[data-test-id=time-slider-input] ').should(
      'have.attr',
      'aria-valuenow',
      '24'
    );
    // ensure tooltip is shown and changes depending on where on the graph is being hovered
    cy.get('[data-test-id=details-carbon-graph]').trigger('mousemove', 'left');
    cy.get('[data-test-id=carbon-chart-tooltip]').should('be.visible');
    cy.get('[data-test-id=carbon-chart-tooltip] ').should('contain.text', '234');

    cy.get('[data-test-id=details-carbon-graph]').trigger('mouseout');
    cy.get('[data-test-id=details-carbon-graph]').trigger('mousemove', 'center');
    cy.get('[data-test-id=carbon-chart-tooltip]').should('contain.text', '206');
    cy.get('[data-test-id=details-carbon-graph]').trigger('mouseout');

    // cy.get('[data-test-id=time-slider-input] ').setSliderValue(1_661_306_400_000);
    cy.get('[data-test-id=left-panel] [data-test-id=co2-square-value]').should(
      'contain.text',
      '232'
    );

    cy.get('[data-test-id=left-panel-back-button]').click();
  });

  // it('asserts countryPanel contains "no-recent-data" message', () => { TODO bring back when we have a no recent data message
  //   cy.interceptAPI('v6/details/hourly/UA');
  //   cy.visit('/zone/UA?lang=en-GB');
  //   cy.waitForAPISuccess('v6/state/hourly');
  //   cy.waitForAPISuccess('v6/details/hourly/UA');

  //   cy.get('[data-test-id=no-data-overlay-message]')
  //     .should('exist')
  //     .contains('Data is temporarily unavailable for the selected time');
  // });

  // it('asserts countryPanel contains no parser message when zone has no data', () => {
  //   cy.visit('/zone/CN?lang=en-GB');
  //   cy.waitForAPISuccess('v6/state/hourly');
  //   cy.get('[data-test-id=no-parser-message]').should('exist');
  // });
});
