d3 = require('d3');
moment = require('moment');

function AreaGraph(selector, modeColor, modeOrder) {
    this.rootElement = d3.select(selector);
    this.graphElement = this.rootElement.append('g');

    // Create scales
    this.x = d3.scaleTime();
    this.y = d3.scaleLinear();
    this.z = d3.scaleOrdinal()
        .domain(modeOrder)
        .range(modeOrder.map(function(d) { return modeColor[d]; }));

    // 
    this.stack = d3.stack()
        .keys(modeOrder.reverse());
}

AreaGraph.prototype.data = function (arg) {
    if (!arg) return this._data;
    if (!arg.length) {
        this._data = [];
        return this;
    }

    // Parse data
    data = this._data = arg.map(function(d) {
        var obj = {
            datetime: moment(d.datetime).toDate()
        };
        // Add production
        d3.entries(d.production).forEach(function(o) { obj[o.key] = o.value; });
        return obj;
    });

    // Set domains
    this.x.domain(d3.extent(data, function(d) { return d.datetime; }));
    this.y.domain([
        d3.min(arg, function(d) { return d.totalExport; }),
        d3.max(arg, function(d) { return d.totalImport + d.totalProduction; })
    ]);

    return this;
}

AreaGraph.prototype.render = function () {
    // Convenience
    var x = this.x,
        y = this.y,
        z = this.z,
        stack = this.stack,
        data = this._data;

    // Set scale range, based on effective pixel size
    var width  = this.rootElement.node().getBoundingClientRect().width,
        height = this.rootElement.node().getBoundingClientRect().height;
    x.range([0, width]);
    y.range([height, 0]);

    var area = d3.area()
        .x(function(d, i) { return x(d.data.datetime); })
        .y0(function(d) { return y(d[0]); })
        .y1(function(d) { return y(d[1]); });

    var layer = this.graphElement
        .selectAll('.layer')
        .data(stack(data))
        .enter().append('g')
            .attr('class', 'layer');

    layer.append('path')
        .attr('class', 'area')
        .style('fill', function(d) { return z(d.key); })
        .attr('d', area);

    return this;
}

module.exports = AreaGraph;
