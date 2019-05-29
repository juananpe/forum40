<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-data-table
      :headers="commentsTableHeader"
      :items="comments"
      :expand="expand"
      :loading="loading"
      :pagination.sync="pagination"
      :total-items="totalItems"
      item-key="_id.$oid"
    >
      <template v-slot:items="props">
        <tr @click="props.expanded = !props.expanded">
          <td class="text-xs-left">
            <div
              v-if="!props.expanded"
            >{{((props.item.title||'') + props.item.text) | truncate(teaserTextLength)}}</div>
            <b v-else>{{(props.item.title||'') + props.item.text}}</b>
          </td>
          <td class="text-xs-left">{{ props.item.timestamp['$date'] | moment}}</td>
          <td>
            <v-layout row>
              <v-flex pr-1>
                <v-btn small outline color="success" class="action-left">
                  <v-icon>done</v-icon>
                </v-btn>
              </v-flex>
              <v-flex pl-1>
                <v-btn small outline color="error" class="action-right">
                  <v-icon>clear</v-icon>
                </v-btn>
              </v-flex>
            </v-layout>
          </td>
        </tr>
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
      expand: false,
      totalItems: 100,
      teaserTextLength: 80,
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
          value: "text",
          width: "85%"
        },
        {
          text: "Datum",
          align: "left",
          sortable: false,
          value: "timestamp",
          width: "10%"
        },
        {
          text: "Annotation",
          align: "left",
          sortable: false,
          value: "annotation",
          width: "5%"
        }
      ]
    };
  },
  filters: {
    moment: function(date) {
      return moment(date)
        .locale("de")
        .format("MMMM Do YY");
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
      const skip = (this.pagination.page - 1) * numberOfElements;
      const { data } = await Service.get(
        `db/comments/${this.label}/${skip}/${numberOfElements}`
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
