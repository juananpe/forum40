<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-layout>
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
      :loading="loading"
      :footer-props="footerprops"
      :items-per-page.sync="rowsPerPage"
      :page.sync="page"
      :expanded.sync="expanded"
      :server-items-length="totalItems"
      item-key="comment_id"
      single-expand
      show-expand
    >
      <template v-slot:item="props">
        <tr @click="commentClicked(props)" class="mb-2">
          <td>
            <v-icon v-if="!props.isExpanded">expand_more</v-icon>

            <v-icon v-else @click="commentClicked(props)">expand_less</v-icon>
          </td>
          <td class="text-left commenttext">
            <div v-if="!props.isExpanded">
              <span v-html="highlight(shortText(commentText(props)), keyword)"></span>
            </div>

            <b v-else>
              <span v-html="highlight(commentText(props), keyword)"></span>
            </b>
          </td>
          <td class="text-right">{{ props.item.timestamp | moment}}</td>
          <td v-for="(label, i) in selectedLabels" :key="props.item.comment_id+i">
            <!-- <UserCommentAnnotation
              :commentId="props.item.comment_id"
              :initialLabel="getAnnotations(props.item, label)"
              :labelName="label"
            /> -->
            Annotation
          </td>
        </tr>
      </template>
      <template v-slot:expanded-item="{ item, headers }">
        <td :colspan="headers.length" class="elevation-1">
          <v-btn
            outlined
            small
            color="primary"
            text
            @click="loadSimilarComments(item)"
          >Ähnliche Kommentare anzeigen</v-btn>
        </td>
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
      expanded: [],
      loading: false,
      selected: [],
      expand: false,
      totalItems: 0,
      footerprops: {
        "items-per-page-options": [15, 30]
      },
      teaserTextLength: 250,
      labels: {},
      page: 1,
      rowsPerPage: 15,
      basicCommentsTableHeader: [
        {
          text: "Kommentartext",
          align: "left",
          sortable: false,
          value: "text",
          width: "80%"
        },
        {
          text: "Datum",
          align: "right",
          sortable: false,
          value: "timestamp",
          width: "15%"
        }
      ]
    };
  },
  filters: {
    moment: function(date) {
      return moment(date)
        .locale("de")
        .format("DD. MMM YYYY");
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
        this.rowsPerPage === -1 ? this.totalItems : this.rowsPerPage;
      const skip = (this.page - 1) * limit;
      const queryString =
        this.countQueryString + `&skip=${skip}&limit=${limit}`;
      return queryString;
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
    async page() {
      this.setSelectedComment({});
      this.loading = true;
      await this.fetchComments();
      this.loading = false;
    },
    async rowsPerPage() {
      this.loading = true;
      await this.fetchComments();
      this.loading = false;
    }
  },
  methods: {
    ...mapMutations([Mutations.setSelectedComment, Mutations.setKeywordfilter]),
    async loadTable() {
      this.loading = true;
      this.page = 1;
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
      this.totalItems = data.count.count;
    },
    commentClicked(props) {
      props.expand(!props.isExpanded);

      if (!props.isExpanded) {
        // working like this, but don't know why
        const selectedComment = props.item;
        this[Mutations.setSelectedComment](selectedComment);
      } else {
        this[Mutations.setSelectedComment]({});
      }
    },
    keywordChanged() {
      //this.loadTable();
    },
    loadSimilarComments(item) {}
  },
  components: {
    UserCommentAnnotation
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.commenttext >>> .highlight {
  background-color: yellow;
}
</style>
