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

      {{ msg }}


  </div>
</template>

<script>
import axios from "axios";
import Service from "../api/db";
import streamgraph from "../charts/streamgraph"

export default {
  name: "TimeChart",
  data: function() {
    return {
      msg: "noData",
      id: null,
      data: []
    };
  },
  computed : {
    playload_time_list: function() {
      return {
        "id": this.id,
        "time_intervall": 120000000
      }
    }
  },
    mounted: function() {
        Service.get("db/labels/id/sentimentnegative", (status, data) => (this.id = data['id']));
  },
  methods: {
    getData: function() {
      Service.post("db/comments/timeseriesByLabel", this.playload_time_list, (status, data) => (this.msg = JSON.parse(data)));
    },
    drawChart: function() {

        this.msg.forEach(d => {
    	    d["time"] = new Date(d["_id"])
    	    delete d["_id"]
    	    delete d["sum"]
        })

        var chart = streamgraph();

        d3.select("#streamgraph")
            .datum(this.msg)
            .call(chart)
        }
    }
};
</script>

<style type="text/css">
  .path {
    clip-path: url(#clip);
}
</style>
