var webpack = require('webpack');
var fs = require('fs');
var glob = require('glob');

var ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
    devtool: (process.env.NODE_ENV === 'production' ? 'sourcemap' : 'eval'),
    entry: { bundle:'./app/main.js', styles: './app/styles.css' },
    module: {
        rules: [
            // Extract css files
            {
                test: /\.css$/,
                exclude: /^node_modules$/, 
                use: ExtractTextPlugin.extract({
                    fallback: 'style-loader',
                    use: [{ loader: 'css-loader', options: { url: false } }]
                })
            }
        ]
    },
    plugins: [
        new ExtractTextPlugin('[name].' + (process.env.NODE_ENV === 'production' ? '[chunkhash]' : 'dev') + '.css'),
        new webpack.optimize.CommonsChunkPlugin({
            name: 'vendor',
            minChunks: function (module) {
                // this assumes your vendor imports exist in the node_modules directory
                return module.context && module.context.indexOf('node_modules') !== -1;
            }
        }),
        new webpack.optimize.OccurrenceOrderPlugin(),
        function() {
            this.plugin('done', function(stats) {
            fs.writeFileSync(
                __dirname + '/public/dist/manifest.json',
                JSON.stringify(stats.toJson()));
            });
        }
    ],
    output: {
        filename: '[name].' + (process.env.NODE_ENV === 'production' ? '[chunkhash]' : 'dev') + '.js',
        path: __dirname + '/public/dist/'
    }
};
