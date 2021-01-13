module.exports = {
  productionSourceMap: false,
  devServer: {
    disableHostCheck: true
  },
  transpileDependencies: [
    'vue-echarts',
    'resize-detector'
  ]
}