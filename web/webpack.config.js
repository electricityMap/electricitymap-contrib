const webpack = require('webpack');
const fs = require('fs');
const autoprefixer = require('autoprefixer');

const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');

const { version } = require('./public/client-version.json');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  devtool: isProduction ? 'sourcemap' : 'eval',
  entry: {
    bundle: ['./src/index.jsx'],
    styles: './src/scss/styles.scss',
  },
  module: {
    rules: [
      // Extract css files
      {
        test: /\.(sa|sc|c)ss$/,
        exclude: /^node_modules$/,
        use: [
          MiniCssExtractPlugin.loader,
          { loader: 'css-loader', options: { url: false } },
          { loader: 'postcss-loader', options: { plugins: [autoprefixer()] } },
          { loader: 'sass-loader', options: { sourceMap: true } },
        ],
      },
      {
        test: [/\.(js|jsx)$/],
        exclude: [/node_modules/],
        loader: 'babel-loader',
        options: {
          presets: [['@babel/preset-env', {useBuiltIns: 'usage', corejs: 3}], '@babel/preset-react'],
          plugins: ['@babel/plugin-proposal-class-properties', ['@babel/plugin-transform-runtime', { corejs: { version: 3, proposals: true }}]],
          cacheDirectory: true, // cache results for subsequent builds
        },
      },
    ],
  },
  plugins: [
    new OptimizeCssAssetsPlugin(),
    new MiniCssExtractPlugin({
      filename: `[name].${  isProduction ? '[chunkhash]' : 'dev'  }.css`,
      chunkFilename: `[name].${  isProduction ? '[chunkhash]' : 'dev'  }.css`,
    }),
    new webpack.optimize.OccurrenceOrderPlugin(),
    function () {
      this.plugin('done', (stats) => {
        // Avoid dumping everything (~30mb)
        const output = {...stats.toJson({all: false, assets: true, groupAssetsByChunk: true})};
        fs.writeFileSync(
          `${__dirname}/public/dist/manifest.json`,
          JSON.stringify(output)
        );
      });
    },
    new webpack.DefinePlugin({
      ELECTRICITYMAP_PUBLIC_TOKEN: `"${process.env.ELECTRICITYMAP_PUBLIC_TOKEN || 'development'}"`,
      VERSION: JSON.stringify(version),
      'process.env': {
        NODE_ENV: JSON.stringify(isProduction ? 'production' : 'development'),
      },
    }),
  ],
  optimization: {
    splitChunks: {
      cacheGroups: {
        commons: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all',
        },
      },
    },
  },
  output: {
    // filename affects styles.js and bundle.js
    filename: `[name].${isProduction ? '[chunkhash]' : 'dev'}.js`,
    // chunkFilename affects `vendor.js`
    chunkFilename: `[name].${isProduction ? '[chunkhash]' : 'dev'}.js`,
    path: `${__dirname}/public/dist`,
    pathinfo: false,
  },
  // The following is required because of https://github.com/webpack-contrib/css-loader/issues/447
  node: {
    fs: 'empty',
  },
};
