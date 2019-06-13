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
    
    playload_time_list: function() {
      return {
        name: this[Getters.selectedLabels],
        time_intervall: this.time_intervall
      };
    },
    /*timeseriesQueryString() {
       const getParams = [`${this[Getters.labelParameters]}`];
       getParams.push(`time_intervall=${this.time_intervall}`);
       const queryString = getParams.filter(e => e).join("&");
       return queryString;
    }*/
  },
   watch: {
    selectedLabels() {
      if (this[Getters.selectedLabels].length > 0) this.getData(); else this.getDataNoSelectionasync()
    }
  },
  mounted: function() {
    if (this[Getters.selectedLabels].length > 0) this.getData(); else this.getDataNoSelectionasync();
  },
  methods: {
    formatTimeArray: function (array) {
      return array.map(x => new Date(x).toISOString().slice(0,10))
    },
    addSeriesToChat: function (data, name) {
      data["time"] = this.formatTimeArray(data["time"])
      this.chart_options.xAxis.data = data["time"]
      var series = {
            name: name,
            type: "bar",
            data: data["data"],
            animationDelay: function(idx) {
              return idx * 1;
          }
        }
        this.chart_options.series.push(series)
    },
    getDataNoSelectionasync: async function() {
      this.chart_options.series = []
      const { data } = await Service.get(`db/comments/timeseries_all?time_intervall=262850000`); // TODO query
      this.addSeriesToChat(data, "Gesamtheit")
    },
    getData: async function() {
      this.chart_options.series = [] // TODO keep the required series
      this[Getters.selectedLabels].forEach( async element => {
        const { data } = await Service.get(`db/comments/timeseries_single?label=${element}&time_intervall=262850000`); // TODO query
        this.addSeriesToChat(data, element)
      });
    },
  },
  data() {
    return {
       id: null,
      time_intervall: 360000000,
      chart_options: {
        title: {
          text: "柱状图动画延迟"
        },
        legend: {
          data: ["bar", "bar2"],
          align: "left"
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
        series: [
          {
            name: "1",
            type: "bar",
            data: [],
            animationDelay: function(idx) {
              return idx * 10;
            }
          },
          {
            name: "2",
            type: "bar",
            data: [],
            animationDelay: function(idx) {
              return idx * 10;
            }
          },
          {
            name: "3",
            type: "bar",
            data: [],
            animationDelay: function(idx) {
              return idx * 10;
            }
          }
        ],
        animationDelayUpdate: function(idx) {
          return idx * 5;
        }
      }
    };
  }
};
</script>