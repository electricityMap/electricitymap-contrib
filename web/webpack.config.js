const webpack = require('webpack');
const postcssPresetEnv = require('postcss-preset-env');

const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

const { version } = require('./public/client-version.json');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  devtool: isProduction ? 'source-map' : 'eval',
  entry: {
    bundle: './src/index.jsx',
    styles: './src/scss/styles.scss',
  },
  resolve: {
    extensions: ['.js', '.jsx', '.mjs', '.cjs'],
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
          { loader: 'postcss-loader', options: { postcssOptions: { plugins: [postcssPresetEnv] } } },
          { loader: 'sass-loader', options: { sourceMap: true } },
        ],
      },
      {
        test: [/\.(js|jsx)$/],
        exclude: [/node_modules/],
        loader: 'babel-loader',
        options: {
          cacheDirectory: true, // cache results for subsequent builds
        },
      },
    ],
  },
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'disabled',
      generateStatsFile: true,
      statsOptions: {
        all: false,
        assets: true,
        groupAssetsByChunk: true,
      },
      statsFilename: 'manifest.json',
    }),
    new OptimizeCssAssetsPlugin(),
    new MiniCssExtractPlugin({
      filename: `[name].${  isProduction ? '[chunkhash]' : 'dev'  }.css`,
      chunkFilename: `[name].${  isProduction ? '[chunkhash]' : 'dev'  }.css`,
    }),
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
};
