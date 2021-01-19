<template>
  <div class="comment-list">
    <UserComment 
      v-for="similarComment of similarComments"
      :key="similarComment.id"
      :comment="similarComment"
    />
  </div>
</template>

<script>
import Service, { Endpoint } from "../../api/db";
import UserComment from './UserComment';

export default {
  components: {
    UserComment,
  },
  props: ['comment'],
  data() {
    return {
      similarComments: [],
    }
  },
  watch: {
    comment: {
      immediate: true,
      async handler(comment) {
        const { data } = await Service.get(Endpoint.COMMENTS_SIMILAR(comment.id));
        this.similarComments = data;
      },
    },
  },
}
</script>

<style scoped>
  .comment-list > *:not(:first-child) {
    margin-top: 1rem;
  }
</style>
