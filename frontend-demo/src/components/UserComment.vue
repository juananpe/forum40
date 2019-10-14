<template>
  <v-card v-if="comment">
    <v-card-title primary-title>
      <div>
        UserId: {{this.comment.user_id}}
        {{this.comment.timestamp | moment}}
        <br>
        <h3 class="headline">
          <b>{{this.comment.title}}</b>
        </h3>
      </div>
    </v-card-title>
    <v-card-text>
      <p>{{this.comment.text}}</p>
    </v-card-text>
  </v-card>
</template>

<script>
import moment from "moment";
export default {
  name: "UserComment",
  props: {
    comment: Object
  },
  filters: {
    moment: function(date) {
      return moment(date)
        .locale("de")
        .format("HH:mm - Do MMM YYYY");
    }
  }
};
</script>