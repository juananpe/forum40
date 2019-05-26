<template>
  <div>
    <h3>Comment List</h3>
    <button v-on:click="fetchComments()">Load comments</button>

    <div class="container">
      <div v-for="comment in allComments" :key="comment.id" class="comment">
        <user-comment v-bind="comment" @annotated="annotated"></user-comment>
      </div>
    </div>
  </div>
</template>

<script>
import UserComment from "./UserComment";
import { mapGetters, mapActions } from "vuex";

export default {
  name: "CommentList",
  methods: {
    ...mapActions(["fetchComments"]),
    annotated: function({ comment_id, label }) {
      console.log(`Annotated ${comment_id} with ${label}`);
    }
  },
  computed: mapGetters(["allComments"]),
  components: {
    UserComment
  }
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
