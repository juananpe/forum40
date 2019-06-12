<template>
    <div>
        <v-chart :options="chart_options" />
    </div>
</template>

<style>
/**
 * The default size is 600px×400px, for responsive charts
 * you may need to set percentage values as follows (also
 * don't forget to provide a size for the container).
 */
.echarts {
  width: 100;
  height: 100;
}
</style>

<script>
import ECharts from 'vue-echarts'
import 'echarts/lib/chart/bar'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/legend'

export default {
  components: {
    'v-chart': ECharts
  },
  methods : {

  },
  data () {
    var xAxisData = [];
    var data1 = [];
    var data2 = [];
    for (var i = 0; i < 100; i++) {
        xAxisData.push(i);
        data1.push(60 + (Math.sin(i / 5) * (i / 5 -10) + i / 6) * 5);
        data2.push(60 + (Math.cos(i / 5) * (i / 5 -10) + i / 6) * 5);
    }
    return {
        series : [],
        chart_options : {
            title: {
                text: '柱状图动画延迟'
            },
            legend: {
                data: ['bar', 'bar2'],
                align: 'left'
            },
            toolbox: {
                feature: {
                    magicType: {
                        type: ['stack', 'tiled']
                    },
                    dataView: {},
                    saveAsImage: {
                        pixelRatio: 2
                    }
                }
            },
            tooltip: {
                trigger: 'axis',
            },
            xAxis: {
                data: xAxisData,
                silent: false,
                splitLine: {
                    show: false
                }
            },
            yAxis: {
            },
            series: [{
                name: 'offtopic',
                type: 'bar',
                data: data1,
                animationDelay: function (idx) {
                    return idx * 10;
                }
            }, {
                name: 'inappropriate',
                type: 'bar',
                data: data2,
                animationDelay: function (idx) {
                    return idx * 10 + 100;
                }
            }],
            animationDelayUpdate: function (idx) {
                return idx * 5;
            }
        }
    }
  }
}
</script>