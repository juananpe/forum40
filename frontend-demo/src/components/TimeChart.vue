<template>
  <div class="timechart">

      <div id="streamgraph"> </div>

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
      data: "noData",
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
  mounted : function() {
    this.getData()
  },
  watch: {
    currentLabel(newValue, oldValue) {
      this.getData()
    },
    data : function() {
      this.drawChart()
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
        this.data = data
      });
    },
    drawChart: function() {
        d3.select("#streamgraph")
            .datum(this.data)
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
