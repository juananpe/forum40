<template>
  <v-progress-circular v-if="threadComments === null" :indeterminate="true" />

  <div v-else>
    <div v-for="(threadComment, i) in threadComments" v-bind:key="threadComment.id">
      <div :class="wrapperClasses(i)" :style="wrapperStyles(i)">
        <UserComment :comment="threadComment"/>
      </div>
    </div>
  </div>
</template>

<script>
import Service from "../../api/db";
import UserComment from './UserComment';

export default {
  components: {
    UserComment
  },
  props: ['comment'],
  data() {
    return {
      threadComments: null,
    }
  },
  watch: {
    comment: {
      immediate: true,
      async handler(comment) {
        this.threadComments = null;
        const { data } = await Service.getParentComments(comment.id);
        this.threadComments = data.comments;
      },
    },
  },
  methods: {
    wrapperStyles(i) {
      return {
        marginLeft: `${i*1}rem`,
        marginRight: `${(this.threadComments.length-i)*1}rem`,
      }
    },
    wrapperClasses(i) {
      const isLastElement = i == this.threadComments.length - 1;
      if (isLastElement) {
        return ['indigo lighten-3', 'rounded', 'pa-1']
      } else {
        return ['mb-3'];
      }
    }
  }
}
</script>

<style scoped>
  .comment {
    border-left: 0.4rem solid rgba(0, 0, 0, 0.2);
    padding: 0.4rem 0.8rem;
  }

  .rounded {
    border-radius: 0.25rem;
  }
</style>
