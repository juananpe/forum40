<template>
  <div>
    <h3>Kommentar-Thread</h3>
    <p></p>
    <div v-for="(comment, i) in comments" v-bind:key="comment.id">
      <v-layout>
        <v-flex :[dynamicFlex(i)]="true" mb-1>
          <div :class="dynamicClasses(i)">
            #{{i+1}}
            <UserComment :comment="comment"/>
          </div>
        </v-flex>
      </v-layout>
    </div>
  </div>
</template>

<script>
import { State, Getters } from "../store/const";
import { mapState, mapGetters } from "vuex";
import Service, { Endpoint } from "../api/db";
import UserComment from "./UserComment";

export default {
  data() {
    return {
      comments: []
    };
  },
  methods: {
    dynamicFlex(i) {
      return `offset-xs${i}`;
    },
    dynamicClasses(i) {
      const lastElement = i == this.comments.length - 1;
      return {
        indigo: !lastElement,
        "white--text": !lastElement,
        yellow: lastElement,
        "black--text": lastElement
      };
    }
  },
  computed: {
    ...mapState([State.selectedComment]),
    ...mapGetters([Getters.selectedCommentId])
  },
  watch: {
    async selectedComment() {
      //fetch parent comments
      if (this.selectedCommentId) {
        const { data } = await Service.get(
          Endpoint.COMMENTS_PARENTS(this.selectedCommentId)
        );
        const comments = data.comments;
        this.comments = comments;
      } else {
        this.comments = [];
      }
    }
  },
  components: {
    UserComment
  }
};
</script>

<style>
</style>
