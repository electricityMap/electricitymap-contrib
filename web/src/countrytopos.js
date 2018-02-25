const topo = require('./world.json');
const topojson = require('topojson');

var exports = module.exports = {};

exports.addCountryTopos = (countries) => {
  Object.keys(topo.objects).forEach((k) => {
    if (!topo.objects[k].arcs) { return; }
    let geo;
    // Do merge inner arcs for those
    if (['US'].indexOf(k.split('-')[0]) !== -1) {
      geo = topojson.feature(topo, topo.objects[k]);
    } else {
      geo = { geometry: topojson.merge(topo, [topo.objects[k]]) };
    }
    // Exclude countries with null geometries.
    if (geo.geometry) {
      countries[k] = geo;
    }
  });

  return countries;
};
