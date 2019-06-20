<template>
  <div>
    <v-chart :options="chart_options" :autoresize="true"/>
  </div>
</template>

<style>
/**
 * The default size is 600px×400px, for responsive charts
 * you may need to set percentage values as follows (also
 * don't forget to provide a size for the container).
 */
.echarts {
  width: 100%;
  height: 100;
}
</style>

<script>
import Service, { Endpoint } from "../api/db";

import { Getters } from "../store/const";
import { mapGetters } from "vuex";

import ECharts from "vue-echarts";
import "echarts/lib/chart/bar";
import "echarts/lib/component/tooltip";
import "echarts/lib/component/legend";
import "echarts/lib/component/dataZoom";

export default {
  components: {
    "v-chart": ECharts
  },
    computed: {
    ...mapGetters([
        Getters.selectedLabels, 
        Getters.labelParameters]),

  },
   watch: {
    selectedLabels() {
      if (this[Getters.selectedLabels].length > 0) this.getData(); else this.getDataNoSelectionasync()
    }
  },
  mounted: async function() {
    var p1 = this.initChart()
    await Promise.all([p1]);
    if (this[Getters.selectedLabels].length > 0) this.getData(); else this.getDataNoSelectionasync();
  },
  methods: {
    initChart: async function() {
      const { data } = await Service.get(Endpoint.LABELS);
      data.labels.push("Gesamtheit")
    
      data.labels.forEach(labelName => {
        this.chart_options.legend.selected[labelName] = false
        var series = {
            name: labelName,
            type: "bar",
            data: [],
            animationDelay: function(idx) {
              return idx * 0;
          }
        }
        this.chart_options.series.push(series)
      })
    },
    addSeriesToChat: function (data, name) {
      data["time"] = data["time"]
      this.chart_options.xAxis.data = data["time"]
      var seriesId = this.chart_options.series.findIndex(x => x.name == name)
      if(name != "Gesamtheit") {
        this.local_chart_state.push(name)
      }
      this.chart_options.legend.selected[name] = true
      this.chart_options.series[seriesId].data = data.data
    },
    getDataNoSelectionasync: async function() {
      this.removeAllLabels()

      const { data } = await Service.get(`db/comments/timeseries_all?time_intervall=462850000`); // TODO query
      this.addSeriesToChat(data, "Gesamtheit")
    },
    getData: async function() {
      var seriesId = this.chart_options.series.findIndex(x => x.name == 'Gesamtheit')
      if(seriesId != -1) {
        this.chart_options.series[seriesId].data = []
      }

      if(this[Getters.selectedLabels].length > this.local_chart_state.length) {
          var label = this[Getters.selectedLabels][this[Getters.selectedLabels].length -1]
          const { data } = await Service.get(`db/comments/groupByMonth?label=${label}`); // TODO query
          this.addSeriesToChat(data, label)
      }
      this.removeDisabledLabels()
    },
    removeAllLabels: function() {
      this.local_chart_state = []
      this.chart_options.series.forEach(x => x.data = [])
    },
    removeDisabledLabels: function() {
      var diff = this.local_chart_state.filter(i =>  this[Getters.selectedLabels].indexOf(i) < 0)
      while(diff.length > 0) {
        var labelName = diff.pop()
        this.chart_options.legend.selected[labelName] = false
        var seriesId = this.chart_options.series.findIndex(x => x.name == labelName)
        this.local_chart_state = this.local_chart_state.filter(x => x != labelName)
        this.chart_options.series[seriesId].data = []
      }
    }
  },
  data() {
    return {
      local_chart_state: [],
      diff : [],
      time_intervall: 5000000000,
      chart_options: {
        title: {
          text: "柱状图动画延迟"
        },
        legend: {
          align: "left",
          show: false,
          selected: {}
        },
        toolbox: {
          feature: {
            magicType: {
              type: ["stack", "tiled"]
            },
            dataView: {},
            saveAsImage: {
              pixelRatio: 2
            }
          }
        },
            dataZoom: [{
        type: 'inside'
    }, {
        type: 'slider'
    }],
        tooltip: {
          trigger: "axis"
        },
        xAxis: {
          data: [],
          silent: false,
          splitLine: {
            show: false
          }
        },
        yAxis: {},
        series: [],
        animationDelayUpdate: function(idx) {
          return idx * 0;
        }
      }
    };
  }
};
</script>