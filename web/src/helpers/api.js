import { json as jsonRequest } from 'd3-request';
import { sha256 } from 'js-sha256';
import Cookies from 'js-cookie';

import { isLocalhost, isProduction } from './environment';
import thirdPartyServices from '../services/thirdparty';

function isRemoteParam() {
  return (new URLSearchParams(window.location.search)).get('remote') === 'true';
}

// Use local endpoint only if ALL of the following conditions are true:
// 1. The app is running on localhost
// 2. The `remote` search param hasn't been explicitly set to true
// 3. Document domain has a non-empty value
function isUsingLocalEndpoint() {
  return isLocalhost() && !isRemoteParam() && document.domain !== '';
}

export function getEndpoint() {
  return isUsingLocalEndpoint() ? 'http://localhost:9000' : 'https://api.electricitymap.org';
}

export function protectedJsonRequest(path) {
  const url = getEndpoint() + path;
  const token = isUsingLocalEndpoint() ? 'development' : ELECTRICITYMAP_PUBLIC_TOKEN;
  const timestamp = new Date().getTime();

  return new Promise((resolve, reject) => {
    jsonRequest(url)
      .header('electricitymap-token', Cookies.get('electricitymap-token'))
      .header('x-request-timestamp', timestamp)
      .header('x-signature', sha256(token + path + timestamp))
      .get(null, (err, res) => {
        if (err) {
          reject(err);
        } else if (!res || !res.data) {
          reject(new Error(`Empty response received for ${url}`));
        } else {
          resolve(res.data);
        }
      });
  });
}

function trackError(err, appState) {
  console.error(`Error Caught! ${err}`);
  thirdPartyServices.reportError(err);
  thirdPartyServices.ga('event', 'exception', { description: err, fatal: false });
  thirdPartyServices.track('error', Object.assign({}, appState, { name: err.name, stack: err.stack }));
}

export function handleConnectionReturnCode(err, appState = {}) {
  if (err) {
    if (err.target) {
      // Avoid catching HTTPError 0
      // The error will be empty, and we can't catch any more info
      // for security purposes
      // See http://stackoverflow.com/questions/4844643/is-it-possible-to-trap-cors-errors
      if (err.target.status) {
        trackError(
          new Error(`HTTPError ${err.target.status} ${err.target.statusText} at ${err.target.responseURL}: ${err.target.responseText}`),
          appState
        );
      }
    } else {
      trackError(err, appState);
    }
  }
}
