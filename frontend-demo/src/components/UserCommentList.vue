<template>
  <div>
    <h3>Comment List</h3>

    <button v-on:click="fetchComments()">Load comments</button>

    <div class="container">
      <v-layout row wrap>
        <v-flex xs3 v-for="comment in allComments" :key="comment.id">
          <user-comment v-bind="comment" @annotated="annotated"></user-comment>
        </v-flex>
      </v-layout>
    </div>
  </div>
</template>

<script>
import UserComment from "./UserComment";
import { mapGetters, mapActions, mapMutations } from "vuex";

export default {
  name: "CommentList",
  methods: {
    ...mapActions(["fetchComments"]),
    ...mapMutations(["setComments"]),
    annotated: function({ comment_id, label }) {
      let comments = this.allComments.filter(
        comment => comment._id.$oid !== comment_id
      );
      this.setComments(comments);
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
</style>
