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
      item-key="id"
      single-expand
      show-expand
    >
      <template v-slot:item="props">
        <tr class="mb-2">
          <td @click="commentClicked(props)">
            <v-icon v-if="!props.isExpanded">expand_more</v-icon>

            <v-icon v-else>expand_less</v-icon>
          </td>
          <td @click="commentClicked(props)" class="text-left commenttext">
            <div v-if="!props.isExpanded">
              <span v-html="highlight(shortText(commentText(props)), keyword)"></span>
            </div>

            <b v-else>
              <span v-html="highlight(commentText(props), keyword)"></span>
            </b>
          </td>
          <td class="text-right">{{ props.item.timestamp | moment}}</td>
          <td v-for="(label, i) in selectedLabels" :key="props.item.id+i">
            <UserCommentAnnotation
              :commentId="props.item.id"
              :labelId="labels[label]"
              :personalLabel="getPeronalAnnotation(props.item, labels[label])"
              :majority="getGroupAnnotation(props.item, labels[label])"
              :confidence="Math.random()"
            />
          </td>
        </tr>
      </template>
      <template v-slot:expanded-item="{ item, headers }">
        <UserCommentSimilar :comment="item" />
      </template>
    </v-data-table>
  </div>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import { State, Getters, Mutations } from "../store/const";
import { mapState, mapGetters, mapMutations } from "vuex";
import moment from "moment";
import { EventBus, Events } from "../event-bus";
import UserCommentAnnotation from "./UserCommentAnnotation";
import UserCommentSimilar from "./UserCommentSimilar";

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
      teaserTextLength: 200,
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
    ...mapState([State.labels]),
    ...mapGetters([
      Getters.keywordfilter,
      Getters.selectedLabels,
      Getters.labelParameters,
      Getters.jwtUser,
      Getters.jwt
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
    EventBus.$on(Events.loggedIn, this.fetchComments);
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
    getPeronalAnnotation(comment, label_id) {
      const user_annotation = comment.user_annotation;
      if (user_annotation === undefined) return undefined; // no user labels
      const annotation = user_annotation.find(e => e[0] === label_id);
      if (annotation === undefined) return undefined; // no annotation for this label found
      return !!annotation[1];
    },
    getGroupAnnotation(comment, label_id) {
      const group_annotaitons = comment.group_annotation;
      if (group_annotaitons[0][0] === null) return undefined;

      const annotation = group_annotaitons.find(e => e[0] === label_id);
      if (annotation === undefined) return undefined;
      return annotation.slice(1);
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
        `${Endpoint.COMMENTS}?${this.pageQueryString}`,
        this[Getters.jwt]
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
    }
  },
  components: {
    UserCommentAnnotation,
    UserCommentSimilar
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.commenttext >>> .highlight {
  background-color: yellow;
}
</style>
