<template>
  <div class="hello">

    <div id="example-1">
      <button v-on:click="getData()">getData</button>
    </div>

    <h1>{{ id }}</h1>
    <h1>{{ playload_time_list }}</h1>
    <h1>{{ msg }}</h1>


  </div>
</template>

<script>
import axios from "axios";
import Service from "../api/db";

export default {
  name: "HelloWorld",
  data: function() {
    return {
      id: String,
      msg: "noData"
    };
  },
  computed : {
    playload_time_list: function() {
      return {
        "id": this.id,
        "time_intervall": 360000000
      }
    }
  },
  methods: {
    getData: function() {
      Service.post("db/comments/timeseriesByLabel", this.playload_time_list, (status, data) => (this.msg = data));
      console.log(this.msg)
    }
  },
  mounted: function() {

    Service.get("db/labels/id/sentimentnegative", (status, data) => (this.id = data['id']));

    console.log(this.playload_time_list)
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
