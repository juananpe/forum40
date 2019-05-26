<template>
  <div id="app">
    <DataSelector/>
    <TimeChart/>
    <UserCommentList/>
  </div>
</template>

<script>
import TimeChart from "./components/TimeChart.vue";
import UserCommentList from "./components/UserCommentList.vue";
import DataSelector from "./components/DataSelector.vue";

export default {
  name: "app",
  components: {
    DataSelector,
    TimeChart,
    UserCommentList,
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
