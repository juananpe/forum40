<template>
  <v-progress-circular v-if="threadComments === null" :indeterminate="true" />

  <div v-else>
    <div v-for="(threadComment, i) in threadComments" v-bind:key="threadComment.id">
      <v-layout>
        <v-flex :[dynamicFlex(i)]="true" mb-1>
          <div :class="dynamicClasses(i)">
            #{{i+1}}
            <UserComment :comment="threadComment"/>
          </div>
        </v-flex>
      </v-layout>
    </div>
  </div>
</template>

<script>
import { Getters } from "../../store/const";
import { mapGetters } from "vuex";
import Service, { Endpoint } from "../../api/db";
import UserComment from './UserComment';

export default {
  components: {
    UserComment
  },
  props: ['comment'],
  computed: {
    ...mapGetters([Getters.jwt])
  },
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
        const { data } = await Service.get(
          Endpoint.COMMENTS_PARENTS(this.comment.id),
          this[Getters.jwt],
        );
        this.threadComments = data.comments;
      },
    },
  },
  methods: {
    dynamicFlex(i) {
      return `offset-xs${i}`;
    },
    dynamicClasses(i) {
      const lastElement = i == this.threadComments.length - 1;
      return {
        indigo: !lastElement,
        "white--text": !lastElement,
        yellow: lastElement,
        "black--text": lastElement
      };
    }
  }
}
</script>

<style scoped>
  .comment {
    border-left: 0.4rem solid rgba(0, 0, 0, 0.2);
    padding: 0.4rem 0.8rem;
  }
</style>
