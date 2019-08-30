<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-layout row>
      <v-flex xs12>
        <v-text-field
          v-model="keyword"
          label="Textsuche"
          @change="keywordChanged"
          append-icon="search"
          clearable
        ></v-text-field>
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
              <span v-html="highlight(shortText(commentText(props)), keyword)"></span>
            </div>

            <b v-else>
              <span v-html="highlight(commentText(props), keyword)"></span>
            </b>
          </td>
          <td class="text-xs-left">{{ props.item.timestamp['$date'] | moment}}</td>
          <td v-for="(label, i) in selectedLabels" :key="i">
            <UserCommentAnnotation
              :commentId="props.item._id.$oid"
              :initialLabel="getAnnotations(props.item, label)"
              :labelName="label"
            />
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
import { getLabels } from "../CommentsUtil";
import moment from "moment";
import UserCommentAnnotation from "./UserCommentAnnotation";

export default {
  name: "UserCommentList",
  data() {
    return {
      comments: [],
      loading: false,
      selected: [],
      expand: false,
      totalItems: 0,
      rowsPerPage: [15, 30],
      teaserTextLength: 250,
      labels: {},
      pagination: {
        page: 1,
        rowsPerPage: 15,
        descending: true,
        sortBy: "likes"
      },
      basicCommentsTableHeader: [
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
    ...mapGetters([
      Getters.keywordfilter,
      Getters.selectedLabels,
      Getters.labelParameters,
      Getters.jwtUser
    ]),
    commentsTableHeader() {
      const labelTableHeaders = this[Getters.selectedLabels].map(e => ({
        text: e,
        align: "center",
        sortable: false,
        value: "text",
        width: "15%"
      }));

      return this.basicCommentsTableHeader.concat(labelTableHeaders);
    },
    countQueryString() {
      const getParams = [`${this[Getters.labelParameters]}`];
      if (this.keyword) getParams.push(`keyword=${this.keyword}`);
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
    },
    keyword: {
      set(state) {
        this[Mutations.setKeywordfilter](state);
        this.loadTable();
      },
      get() {
        return this[Getters.keywordfilter];
      }
    }
  },
  async mounted() {
    this.loadTable();
    const { data } = await Service.get(Endpoint.LABELS);
    this.labels = data;
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
    ...mapMutations([Mutations.setSelectedComment, Mutations.setKeywordfilter]),
    async loadTable() {
      this.loading = true;
      this.pagination.page = 1;
      const p1 = this.setToalCommentNumber();
      const p2 = this.fetchComments();
      await Promise.all([p1, p2]);
      this.loading = false;
    },
    idForLabel(label) {
      const index = this.labels.labels.indexOf(label);
      return this.labels.ids[index];
    },
    labelForId(id) {
      const index = this.labels.ids.indexOf(id);
      return this.labels.labels[index];
    },
    getAnnotations(comment, label) {
      const labelId = this.idForLabel(label);
      const username = this[Getters.jwtUser];
      return getLabels(comment, labelId, username);
    },
    commentText(props) {
      return (props.item.title || "") + " " + props.item.text;
    },
    shortText(text) {
      return this.$options.filters.truncate(text, this.teaserTextLength);
    },
    highlight: function(words, query) {
      if (query) {
        const regEx = new RegExp("(" + query + ")", "ig");
        const highlightedText = words.replace(
          regEx,
          '<span class="highlight">' + "$1" + "</span>"
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
    },
    keywordChanged() {
      //this.loadTable();
    }
  },
  components: {
    UserCommentAnnotation
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
