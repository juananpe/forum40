<template>
  <v-card v-if="comment">
    <v-card-title>{{comment.title}}</v-card-title>
    <v-card-text>
      <p>{{comment.text}}</p>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: "UserComment",
  props: {
    comment: Object,
  }
};
</script>
