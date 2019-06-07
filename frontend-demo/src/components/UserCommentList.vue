<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-data-table
      :headers="commentsTableHeader"
      :items="comments"
      :expand="expand"
      :loading="loading"
      :rows-per-page-items="rowsPerPage"
      :pagination.sync="pagination"
      :total-items="totalItems"
      item-key="_id.$oid"
    >
      <template v-slot:items="props">
        <tr>
          <td @click="commentClicked(props)" class="text-xs-left">
            <div
              v-if="!props.expanded"
            >{{((props.item.title||'') + ' ' + props.item.text) | truncate(teaserTextLength)}}</div>

            <b v-else>{{(props.item.title||'') + ' ' + props.item.text}}</b>
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
import { mapState, mapGetters, mapMutations } from "vuex";
import moment from "moment";

export default {
  name: "UserCommentList",
  data() {
    return {
      comments: [],
      loading: false,
      selected: [],
      expand: false,
      totalItems: 0,
      rowsPerPage: [5, 10],
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
    ...mapState(["selectedLabels"]),
    ...mapGetters(["labelParameters"])
  },
  mounted() {
    this.loadTable();
  },
  watch: {
    selectedLabels() {
      this.setSelectedComment({});
      this.loadTable();
    },
    async pagination() {
      this.setSelectedComment({});
      this.loading = true;
      await this.fetchComments();
      this.loading = false;
    }
  },
  methods: {
    ...mapMutations(["setSelectedComment"]),
    async loadTable() {
      this.loading = true;
      this.pagination.page = 1;
      const p1 = this.setToalCommentNumber();
      const p2 = this.fetchComments();
      await Promise.all([p1, p2]);
      this.loading = false;
    },
    async fetchComments() {
      const numberOfElements =
        this.pagination.rowsPerPage === -1
          ? this.totalItems
          : this.pagination.rowsPerPage;
      const skip = (this.pagination.page - 1) * numberOfElements;
      const getParams = [
        `${this.labelParameters}`,
        `skip=${skip}`,
        `limit=${numberOfElements}`
      ];
      const queryString = getParams.filter(e => e).join("&");
      const { data } = await Service.get(`db/comments?${queryString}`);
      this.comments = data;
    },
    async setToalCommentNumber() {
      const { data } = await Service.get(
        `db/comments/count?${this.labelParameters}`
      );
      this.totalItems = data.count;
    },
    commentClicked(props) {
      props.expanded = !props.expanded;
      if (props.expanded) {
        const selectedComment = props.item;
        this.setSelectedComment(selectedComment);
      } else {
        this.setSelectedComment({});
      }
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
