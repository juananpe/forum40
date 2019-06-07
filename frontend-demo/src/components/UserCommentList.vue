<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-layout row>
      <v-flex xs2>
        <v-text-field v-model="textsearch" label="Kommentartextsuche" @change="loadTable" clearable></v-text-field>
      </v-flex>
    </v-layout>

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
          <td @click="commentClicked(props)" class="text-xs-left commenttext">
            <div v-if="!props.expanded">
              <span v-html="highlight(shortText(commentText(props)), textsearch)"></span>
            </div>

            <b v-else>
              <span v-html="highlight(commentText(props), textsearch)"></span>
              {{(props.item.title||'') + ' ' + props.item.text}}
            </b>
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
import Service, { Endpoint } from "../api/db";
import { Getters, Mutations } from "../store/const";
import { mapGetters, mapMutations } from "vuex";
import moment from "moment";

export default {
  name: "UserCommentList",
  data() {
    return {
      comments: [],
      loading: false,
      textsearch: "",
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
    ...mapGetters([Getters.selectedLabels, Getters.labelParameters]),
    countQueryString() {
      const getParams = [`${this[Getters.labelParameters]}`];
      if (this.textsearch) getParams.push(`keyword=${this.textsearch}`);
      const queryString = getParams.filter(e => e).join("&");
      return queryString;
    },
    pageQueryString() {
      const limit =
        this.pagination.rowsPerPage === -1
          ? this.totalItems
          : this.pagination.rowsPerPage;
      const skip = (this.pagination.page - 1) * limit;
      const pageQueryString =
        this.countQueryString + `&skip=${skip}&limit=${limit}`;
      return pageQueryString;
    }
  },
  mounted() {
    this.loadTable();
  },
  watch: {
    [Getters.selectedLabels]: function() {
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
    ...mapMutations([Mutations.setSelectedComment]),
    async loadTable() {
      this.loading = true;
      this.pagination.page = 1;
      const p1 = this.setToalCommentNumber();
      const p2 = this.fetchComments();
      await Promise.all([p1, p2]);
      this.loading = false;
    },
    commentText(props) {
      return (props.item.title || "") + " " + props.item.text;
    },
    shortText(text) {
      return this.$options.filters.truncate(text, this.teaserTextLength);
    },
    highlight: function(words, query) {
      if (query) {
        const highlightedText = words.replace(
          query,
          '<span class="highlight">' + query + "</span>"
        );
        return highlightedText;
      }
      return words;
    },
    async fetchComments() {
      const { data } = await Service.get(
        `${Endpoint.COMMENTS}?${this.pageQueryString}`
      );
      this.comments = data;
    },
    async setToalCommentNumber() {
      const { data } = await Service.get(
        `${Endpoint.COMMENTS_COUNT}?${this.countQueryString}`
      );
      this.totalItems = data.count;
    },
    commentClicked(props) {
      props.expanded = !props.expanded;
      if (props.expanded) {
        const selectedComment = props.item;
        this[Mutations.setSelectedComment](selectedComment);
      } else {
        this[Mutations.setSelectedComment]({});
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
.commenttext >>> .highlight {
  background-color: yellow;
}
</style>
