<template>
  <div>
    <h3>Comment List</h3>
    <button v-on:click="fetchComments()">Load comments</button>

    <div class="container">
      <div v-for="comment in allComments" :key="comment.id" class="comment">
        <div>
          <b>{{comment.title}}</b>
          <div>{{comment.timestamp['$date']}}</div>
        </div>
        <div>{{comment.text}}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from "vuex";

export default {
  name: "CommentList",
  methods: {
    ...mapActions(["fetchComments"])
  },
  computed: mapGetters(["allComments"])
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.container {
  display: flex;
  flex-wrap: wrap;
}

.comment {
  flex: 1 0 21%;
  padding: 10px;
  border: 1px solid #ddd;
}
</style>
