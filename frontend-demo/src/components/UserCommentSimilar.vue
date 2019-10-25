<template>
  <td colspan="100%" class="elevation-1">
    <v-btn
      v-if="!similar_comments.length"
      outlined
      small
      color="primary"
      text
      @click="loadSimilarComments()"
    >Ähnliche Kommentare anzeigen</v-btn>

    <v-container fluid>
      <v-row dense>
        <v-col v-for="(comment, i) in similar_comments" :key="i">
          <v-card class="mx-auto" max-width="344" outlined>
            <v-list-item three-line>
              <v-list-item-content>
                <v-list-item-title class="headline mb-1">{{i+1}}. {{comment.title}}</v-list-item-title>
                <v-list-item-subtitle>{{comment.text}}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </td>
</template>
  

<script>
import Service, { Endpoint } from "../api/db";

export default {
  props: {
    comment: Object
  },
  data() {
    return {
      similar_comments: []
    };
  },
  methods: {
    async loadSimilarComments() {
      const payload = {
        comments: [this.comment.text],
        n: 3
      };
      try {
        const { data } = await Service.post(Endpoint.COMMENTS_SIMILAR, payload);
        this.similar_comments = data[0];
        console.log(data[0]);
      } catch (e) {
        console.error("Could not load similar comments!");
      }
    }
  }
};
</script>

<style>
</style>