<template>
  <div id="app">
    <TimeChart/>
    <CommentList/>
  </div>
</template>

<script>
import TimeChart from "./components/TimeChart.vue";
import CommentList from "./components/CommentList.vue";

export default {
  name: "app",
  components: {
    TimeChart,
    CommentList
  }
};
</script>

<style>
#app {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
