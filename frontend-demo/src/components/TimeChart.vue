<template>
  <div class="timechart">
    <h3>Kommentarverteilung</h3>
    <div id="streamgraph"></div>
  </div>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import * as d3 from "d3";
import streamgraph from "../charts/streamgraph";

import { Getters } from "../store/const";
import { mapGetters } from "vuex";

export default {
  name: "TimeChart",
  data: function() {
    return {
      id: null,
      data: [],
      chart: streamgraph()
    };
  },
  computed: {
    ...mapGetters([Getters.selectedLabels]),
    playload_time_list: function() {
      return {
        name: this[Getters.selectedLabels][0],
        time_intervall: 120000000
      };
    }
  },
  mounted: function() {
    if (this[Getters.selectedLabels].length > 0) this.getData();
  },
  watch: {
    selectedLabels() {
      if (this[Getters.selectedLabels].length > 0) this.getData();
    },
    data: function() {
      this.drawChart();
    }
  },
  methods: {
    getData: async function() {
      const { data } = await Service.post(
        Endpoint.TIMESERIES_BYLABEL,
        this.playload_time_list
      );
      data.forEach(d => {
        d["time"] = new Date(d["_id"]);
        delete d["_id"];
        delete d["sum"];
      });
      this.data = data;
    },
    drawChart: function() {
      d3.select("#streamgraph")
        .datum(this.data)
        .call(this.chart);
    }
  }
};
</script>

<style type="text/css">
.path {
  clip-path: url(#clip);
}
</style>
