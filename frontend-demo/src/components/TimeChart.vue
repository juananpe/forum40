<template>
  <div class="timechart">
      <h1>Test Chart</h1>

      <div id="example-1">
        <button v-on:click="getData()">getData</button>
      </div>
      <div id="example-1">
        <button v-on:click="drawChart()">drawChart</button>
      </div>

      <div id="streamgraph"> </div>
      {{ id }} <br /> {{ playload_time_list }} <br /> {{ msg }}


  </div>
</template>

<script>
import axios from "axios";
import Service from "../api/db";
import streamgraph from "../charts/streamgraph"

import { mapGetters } from "vuex";

export default {
  name: "TimeChart",
  data: function() {
    return {
      msg: "noData",
      id: null,
      data: [],
      chart: streamgraph()
    };
  },
  computed : {
    ...mapGetters(["currentLabel"]),
    playload_time_list: function() {
      return {
        "name": this.currentLabel,
        "time_intervall": 120000000
      }
    }
  },
  methods: {
    getData: function() {
      Service.post("db/comments/timeseriesByLabel", this.playload_time_list, (status, data) => {
        data.forEach(d => {
    	    d["time"] = new Date(d["_id"])
    	    delete d["_id"]
    	    delete d["sum"]
        })
        this.msg = data
      });
    },
    drawChart: function() {
        d3.select("#streamgraph")
            .datum(this.msg)
            .call(this.chart)
        }
    }
};
</script>

<style type="text/css">
  .path {
    clip-path: url(#clip);
}
</style>
