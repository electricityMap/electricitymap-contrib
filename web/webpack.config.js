const webpack = require('webpack');
const fs = require('fs');
const glob = require('glob');

const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  devtool: isProduction ? 'sourcemap' : 'eval',
  entry: { bundle: ['@babel/polyfill', './src/main.js'], styles: './src/styles.css' },
  module: {
    noParse: /(mapbox-gl)\.js$/,
    rules: [
      // Extract css files
      {
        test: /\.css$/,
        exclude: /^node_modules$/,
        use: [
          MiniCssExtractPlugin.loader,
          { loader: 'css-loader', options: { url: false } }
        ]
      },
      {
        test: [/\.js$/],
        exclude: [/node_modules/],
        loader: 'babel-loader',
        query: {
          presets: ['@babel/preset-env', '@babel/preset-react']
        }
      }
    ]
  },
  plugins: [
    new MiniCssExtractPlugin('[name].' + (isProduction ? '[hash]' : 'dev') + '.css'),
    new webpack.optimize.OccurrenceOrderPlugin(),
    function() {
      this.plugin('done', function(stats) {
        fs.writeFileSync(
          __dirname + '/public/dist/manifest.json',
          JSON.stringify(stats.toJson()));
      });
    },
    new webpack.DefinePlugin({
      'ELECTRICITYMAP_PUBLIC_TOKEN': `"${process.env.ELECTRICITYMAP_PUBLIC_TOKEN || 'development'}"`,
      'process.env': {
        'NODE_ENV': JSON.stringify(isProduction ? 'production' : 'development')
      }
    }),
  ],
  optimization: {
    splitChunks: {
      cacheGroups: {
        commons: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all'
        },
      }
    }
  },
  output: {
    filename: '[name].' + (isProduction ? '[chunkhash]' : 'dev') + '.js',
    path: __dirname + '/public/dist/'
  },
  // The following is required because of https://github.com/webpack-contrib/css-loader/issues/447
  node: {
    fs: "empty"
  }
};
