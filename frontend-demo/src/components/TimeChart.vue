<template>
  <div>
    <v-chart :options="chart_options" :autoresize="true" />
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

import { State, Getters } from "../store/const";
import { mapState, mapGetters } from "vuex";

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
    ...mapState([State.labels]),
    ...mapGetters([
      Getters.selectedLabels,
      Getters.getSelectedSource,
      Getters.keywordfilter,
      Getters.timeFrequency
    ])
  },
  watch: {
    timeFrequency() {
      this.updateChart();
    },
    selectedLabels() {
      if (this[Getters.selectedLabels].length > 0)
        this.updateChart_OnLabelChange();
      else this.resetChartToOrigin();
    },
    keywordfilter() {
      this.updateChart();
    }
  },
  mounted: async function() {
    var p1 = this.initChart();
    await Promise.all([p1]);
    if (this[Getters.selectedLabels].length > 0)
      this.updateChart_OnLabelChange();
    else this.resetChartToOrigin();
  },
  methods: {
    initChart: async function() {
      const { data } = await Service.get(Endpoint.LABELS(1));
      data.labels.push("Gesamtheit");

      data.labels.forEach(labelName => {
        this.chart_options.legend.selected[labelName] = false;
        var series = {
          name: labelName,
          type: "bar",
          barGap: "0%",
          barCategoryGap: "10%",
          data: [],
          animationDelay: function(idx) {
            return idx * 0;
          }
        };
        this.chart_options.series.push(series);
      });
    },
    addSeriesToChat: function(data, name) {
      var seriesId = this.chart_options.series.findIndex(x => x.name == name);
      if (name != "Gesamtheit") {
        this.local_chart_state.push(name);
      } else {
        this.chart_options.xAxis.data = data["time"];
      }

      // quick fix
      if (this.chart_options.xAxis.data.length == 0) {
        this.chart_options.xAxis.data = data["time"];
      }

      this.chart_options.legend.selected[name] = true;
      this.chart_options.series[seriesId].data = data.data;
    },
    resetChartToOrigin: async function() {
      this.removeAllLabels();

      const { data } = await Service.get(
        `${this.selectEndpoint()}?source_id=${this[Getters.getSelectedSource].id}&${this.textFilterArg("?")}`
      );

      if (this[Getters.selectedLabels].length == 0) {
        this.addSeriesToChat(data, "Gesamtheit");
      }
    },
    updateChart: async function() {
      var chart_options = this.chart_options;
      var selectEndpoint = this.selectEndpoint;
      var textFilterArg = this.textFilterArg;
      chart_options.series.forEach(async (x) => {
        if (chart_options.legend.selected[x.name]) {
          const label_id = this[State.labels][x.name];
          const { data } = label_id ? 
              await Service.get(`${selectEndpoint()}?source_id=${this[Getters.getSelectedSource].id}&label=${label_id}${textFilterArg("&")}`) 
              : 
              await Service.get(`${selectEndpoint()}?source_id=${this[Getters.getSelectedSource].id}&${textFilterArg("&")}`);
          
          chart_options.xAxis.data = data["time"];
          x.data = data.data;
        }
      });
    },
    updateChart_OnLabelChange: async function() {
      var seriesId = this.chart_options.series.findIndex(
        x => x.name == "Gesamtheit"
      );
      if (seriesId != -1) {
        this.chart_options.series[seriesId].data = [];
        this.chart_options.legend.selected["Gesamtheit"] = false;
      }

      if (this[Getters.selectedLabels].length > this.local_chart_state.length) {
        var label = this[Getters.selectedLabels][
          this[Getters.selectedLabels].length - 1
        ];
        const label_id = this[State.labels][label];
        const { data } = await Service.get(
          `${this.selectEndpoint()}?source_id=${this[Getters.getSelectedSource].id}&label=${label_id}${this.textFilterArg("&")}`
        );
        this.addSeriesToChat(data, label);
      }
      this.removeDisabledLabels();
    },
    textFilterArg: function(prefix) {
      if (this[Getters.keywordfilter]) {
        return `${prefix}keyword=${this[Getters.keywordfilter]}`;
      } else {
        return "";
      }
    },
    selectEndpoint: function() {
      var endpoint = "";
      switch (this[Getters.timeFrequency]) {
        case "d":
          endpoint = Endpoint.COMMENTS_GROUP_BY_DAY;
          break;
        case "m":
          endpoint = Endpoint.COMMENTS_GROUP_BY_MONTH;
          break;
        case "y":
          endpoint = Endpoint.COMMENTS_GROUP_BY_YEAR;
          break;
        default:
        // code block
      }
      return endpoint;
    },
    removeAllLabels: function() {
      this.local_chart_state = [];
      this.chart_options.series.forEach(x => (x.data = []));
      for (var key in this.chart_options.legend.selected) {
        this.chart_options.legend.selected[key] = false; // TODO O(1)
      }

      this[Getters.selectedLabels].forEach(function() {
        this.chart_options.legend.selected["label"] = false;
      });
    },
    removeDisabledLabels: function() {
      var diff = this.local_chart_state.filter(
        i => this[Getters.selectedLabels].indexOf(i) < 0
      );
      while (diff.length > 0) {
        var labelName = diff.pop();
        this.chart_options.legend.selected[labelName] = false;
        var seriesId = this.chart_options.series.findIndex(
          x => x.name == labelName
        );
        this.local_chart_state = this.local_chart_state.filter(
          x => x != labelName
        );
        this.chart_options.series[seriesId].data = [];
      }
    }
  },
  data() {
    return {
      radios: "m",
      local_chart_state: [],
      chart_options: {
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
        dataZoom: [
          {
            type: "inside"
          },
          {
            type: "slider"
          }
        ],
        tooltip: {
          trigger: "axis"
        },
        _xAxis: {
          data: [],
          silent: false,
          splitLine: {
            show: false
          }
        },
        get xAxis() {
          return this._xAxis;
        },
        set xAxis(value) {
          this._xAxis = value;
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