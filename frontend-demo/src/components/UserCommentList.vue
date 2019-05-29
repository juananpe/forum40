<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-data-table
      v-bind:headers="commentsTableHeader"
      :items="comments"
      selected-key="title"
      v-model="selected"
      :loading="loading"
      :pagination.sync="pagination"
      :total-items="totalItems"
    >
      <template slot="items" scope="props">
        <td class="text-xs-left">
          <b>{{props.item.title}}</b>
          <br>
          {{ props.item.text }}
        </td>

        <td class="text-xs-left">{{ props.item.timestamp['$date'] | moment}}</td>
        <td>
          <v-btn small outline block color="success" class="action-left">
            <v-icon>done</v-icon>
          </v-btn>
          <v-btn small outline block color="error" class="action-right">
            <v-icon>clear</v-icon>
          </v-btn>
        </td>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import Service from "../api/db";
import { mapState } from "vuex";
import moment from "moment";

export default {
  name: "UserCommentList",
  data() {
    return {
      comments: [],
      loading: false,
      selected: [],
      totalItems: 100,
      pagination: {
        page: 1,
        rowsPerPage: 5,
        descending: true,
        sortBy: "likes"
      },
      commentsTableHeader: [
        {
          text: "Kommentartext",
          align: "left",
          sortable: false,
          value: "text"
        },
        {
          text: "Datum",
          align: "left",
          sortable: false
        },
        {
          text: "Annotation",
          align: "left",
          sortable: false
        }
      ]
    };
  },
  filters: {
    moment: function(date) {
      return moment(date)
        .locale("de")
        .format("MMMM Do YYYY");
    }
  },
  computed: {
    ...mapState(["label"])
  },
  mounted() {
    this.fetchComments();
  },
  watch: {
    label() {
      this.pagination.page = 1;
      this.fetchComments();
    },
    pagination() {
      this.fetchComments();
    }
  },
  methods: {
    async fetchComments() {
      this.loading = true;
      const numberOfElements =
        this.pagination.rowsPerPage === -1
          ? this.totalItems
          : this.pagination.rowsPerPage;
      const { data } = await Service.get(
        `db/comments/${this.label}/${this.pagination.page -
          1}/${numberOfElements}`
      );
      this.loading = false;
      this.comments = data;
    }
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
