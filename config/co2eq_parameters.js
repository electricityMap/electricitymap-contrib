var exports = module.exports = {};

const co2eqParameters = require('./co2eq_parameters.json');

exports.footprintOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.emissionFactors.defaults[mode];
  const override = (co2eqParameters.emissionFactors.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).value;
};
exports.sourceOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.emissionFactors.defaults[mode];
  const override = (co2eqParameters.emissionFactors.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).source;
};
exports.defaultExportIntensityOf = zoneKey =>
  (co2eqParameters.fallbackZoneMixes[zoneKey] || {}).carbonIntensity;
exports.defaultRenewableRatioOf =(zoneKey) => {
    //if zonekey has ratios in co2eqparameters, then those ratios
    const key = (Object.keys(co2eqParameters.fallbackZoneMixes[zoneKey].powerOriginRatios || {}).length === 0) ? zoneKey : 'defaults' ;
    const ratios = co2eqParameters.fallbackZoneMixes[key].powerOriginRatios;
    
    let renewableRatio = 0;
    Object.keys(ratios).forEach(function (fuelKey) {
      if (exports.renewableAccessor(zoneKey, fuelKey, 1) === 1) {
        renewableRatio += co2eqParameters.fallbackZoneMixes[zoneKey].powerOriginRatios[fuelKey];
      }
    });
    return renewableRatio
}
  (co2eqParameters.fallbackZoneMixes[zoneKey] || {}).renewableRatio;

exports.defaultFossilFuelRatioOf = function(zoneKey) {
  //if zonekey has ratios in co2eqparameters, then those ratios
  const key = (Object.keys(co2eqParameters.fallbackZoneMixes[zoneKey].powerOriginRatios || {}).length === 0) ? zoneKey : 'defaults' ;
  const ratios = co2eqParameters.fallbackZoneMixes[key].powerOriginRatios;
  
  let fossilFuelRatio = 0;
  Object.keys(ratios).forEach(function (fuelKey) {
    if (exports.fossilFuelAccessor(zoneKey, fuelKey, 1) === 1) {
      fossilFuelRatio += co2eqParameters.fallbackZoneMixes[zoneKey].powerOriginRatios[fuelKey];
    }
  });
  return fossilFuelRatio
}
exports.fossilFuelAccessor = (zoneKey, k, v) => {
  return (k == 'coal' ||
          k == 'gas' ||
          k == 'oil' ||
          (k === 'unknown' && (zoneKey !== 'GB-ORK' && zoneKey !== 'UA')) ||
          k == 'other') ? 1 : 0;
}
exports.renewableAccessor = (zoneKey, k, v) => {
  return (exports.fossilFuelAccessor(zoneKey, k, v) ||
          k === 'nuclear') ? 0 : 1;
  // TODO(bl): remove storage from renewable list?
}

exports.defaultPowerOriginRatio = (zoneKey, fuelKey) => {
  //if no ratios found for that zoneKey, use defaults
  const key = (Object.keys(co2eqParameters.fallbackZoneMixes[zoneKey].powerOriginRatios || {}).length === 0) ? zoneKey : 'defaults' ;
  
  return co2eqParameters.fallbackZoneMixes[key].powerOriginRatios[fuelKey]
}

exports.powerOriginRatioFuel = function(fuelKey) {
  return function powerOriginRatioWithFuelSet(zoneKey) {
    return exports.powerOriginRatio(zoneKey, fuelKey)
  }
}
