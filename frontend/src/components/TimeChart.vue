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
import Service from "../api/db";

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
    [Getters.getSelectedSource]() {
      this.sourceChanged()
    },
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
  methods: {
    sourceChanged: async function() {
      await this.initChart();
      this.resetChartToOrigin();
    },
    initChart: async function() {
      var source_id = this[Getters.getSelectedSource].id
      var response = Service.getLabels(source_id);
      return response.then((value) => {
        value.data.labels.push(this.$i18n.t("time_chart.series_total"));

        this.chart_options.series = []

          value.data.labels.forEach(labelName => {
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
          })

      })
    },
    addSeriesToChat: function(data, name) {
      var seriesId = this.chart_options.series.findIndex(x => x.name == name);
      if (name != this.$i18n.t("time_chart.series_total")) {
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

      const { data } = await this.getLabelTimeHistogram(null);

      if (this[Getters.selectedLabels].length == 0) {
        this.addSeriesToChat(data, this.$i18n.t("time_chart.series_total"));
      }
    },
    updateChart: async function() {
      var chart_options = this.chart_options;
      chart_options.series.forEach(async (x) => {
        if (chart_options.legend.selected[x.name]) {
          const labelId = this[State.labels][x.name];
          const { data } = await this.getLabelTimeHistogram(labelId);
          chart_options.xAxis.data = data["time"];
          x.data = data.data;
        }
      });
    },
    updateChart_OnLabelChange: async function() {
      var seriesId = this.chart_options.series.findIndex(
        x => x.name == this.$i18n.t("time_chart.series_total")
      );
      if (seriesId != -1) {
        this.chart_options.series[seriesId].data = [];
        this.chart_options.legend.selected[this.$i18n.t("time_chart.series_total")] = false;
      }

      if (this[Getters.selectedLabels].length > this.local_chart_state.length) {
        var label = this[Getters.selectedLabels][
          this[Getters.selectedLabels].length - 1
        ];
        const labelId = this[State.labels][label];
        const { data } = await this.getLabelTimeHistogram(labelId);
        this.addSeriesToChat(data, label);
      }
      this.removeDisabledLabels();
    },
    getLabelTimeHistogram: function (labelId) {
      const granularity = { y: 'year', m: 'month', d: 'day' }[this[Getters.timeFrequency]];
      
      return Service.getTimeHistogram(
        this[Getters.getSelectedSource].id,
        labelId,
        granularity,
        this[Getters.keywordfilter],
      );
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
