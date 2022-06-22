const { defineConfig } = require('cypress');

module.exports = defineConfig({
  projectId: '9z8tgk',
  baseUrl: 'http://localhost:8080',
  video: false,
  fixturesFolder: '../mockserver/public',
});
