<template>
  <div id="app">
    <TopToolbar/>
    <TimeChart/>
    <UserCommentList/>
  </div>
</template>

<script>
import TopToolbar from "./components/TopToolbar.vue";
import TimeChart from "./components/TimeChart.vue";
import UserCommentList from "./components/UserCommentList.vue";

export default {
  name: "app",
  components: {
    TopToolbar,
    TimeChart,
    UserCommentList
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
}
</style>
