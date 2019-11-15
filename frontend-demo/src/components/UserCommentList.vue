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
      <template
        v-for="(header, i) in commentsTableHeader"
        v-slot:[getHeaderSlotname(header.value)]="{header}"
      >
        <div :key="i">
          <div class="mb-1 columnTitle">{{header.text}}</div>
          <div v-if="header.labelColumn" :key="i" class="tableColumn">
            <v-icon v-if="loggedIn">person</v-icon>
            <v-icon v-if="!loggedIn">people</v-icon>
            <v-icon class="ml-1">{{svgPath}}</v-icon>
          </div>
        </div>
      </template>

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
              :personalLabel="getPeronalAnnotation(props.item.annotations, labels[label])"
              :majority="getGroupAnnotation(props.item.annotations, labels[label])"
              :confidence="getConfidence(props.item.annotations, labels[label])"
            />
          </td>
        </tr>
      </template>
      <template v-slot:expanded-item="{ item, headers }">
        <tr v-if="!similar_comments.length">
          <td></td>
          <td>
            <v-btn
              outlined
              small
              color="primary"
              text
              @click="loadSimilarComments(item)"
            >Ähnliche Kommentare anzeigen</v-btn>
          </td>
          <td></td>
        </tr>
        <tr
          class="elevation-1"
          v-for="(comment, i) in similar_comments.slice(0,MAX_COMMENTS)"
          :key="i"
        >
          <td v-if="similar_comments.length>0"></td>
          <td v-if="similar_comments.length>0">{{comment.title}} {{comment.text}}</td>
          <td v-if="similar_comments.length>0" class="text-right">{{ comment.timestamp | moment}}</td>

          <td v-for="(label, i) in selectedLabels" :key="comment.id+i">
            <UserCommentAnnotation
              v-if="comment.annotations !== undefined"
              :commentId="comment.id"
              :labelId="labels[label]"
              :personalLabel="getPeronalAnnotation(comment.annotations, labels[label])"
              :majority="getGroupAnnotation(comment.annotations, labels[label])"
              :confidence="getConfidence(comment.annotations, labels[label])"
            />
          </td>
        </tr>
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
import { mdiRobot } from "@mdi/js";

export default {
  name: "UserCommentList",
  data() {
    return {
      headerPrefix: "header.",
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
      ],
      svgPath: mdiRobot,
      similar_comments: [],
      MAX_COMMENTS: 3
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
      Getters.jwt,
      Getters.jwtLoggedIn,
      Getters.getSelectedSource
    ]),
    loggedIn() {
      return this[Getters.jwtLoggedIn];
    },
    commentsTableHeader() {
      const labelTableHeaders = this[Getters.selectedLabels].map(e => ({
        text: e,
        align: "center",
        sortable: false,
        value: "text",
        width: "15%",
        labelColumn: true
      }));

      return this.basicCommentsTableHeader.concat(labelTableHeaders);
    },
    countQueryString() {
      const getParams = [`${this[Getters.labelParameters]}`];

      // add source
      const selectedSource = this[Getters.getSelectedSource];
      if (selectedSource) getParams.push(`source_id=${selectedSource.id}`);

      // add keyword
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
    this.similar_comments = [];
    EventBus.$on(Events.loggedIn, this.fetchComments);
    EventBus.$on(Events.sourceLoaded, this.loadTable);
  },
  watch: {
    [Getters.selectedLabels]: function() {
      this.similar_comments = [];
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
    getHeaderSlotname(header) {
      return this.headerPrefix + header;
    },
    getPeronalAnnotation(annotations, label_id) {
      if (annotations === undefined) return undefined;
      const annotation = annotations.find(e => e.label_id === label_id);
      if (annotation === undefined) return undefined; // no annotation for this label found
      return !!annotation.user;
    },
    getGroupAnnotation(annotations, label_id) {
      if (annotations === undefined) return undefined;
      const annotation = annotations.find(e => e.label_id === label_id);
      if (annotation === undefined) return undefined;
      return [annotation.group_count_true, annotation.group_count_false];
    },
    getConfidence(annotations, label_id) {
      if (annotations === undefined) return undefined;
      const classification = annotations.find(e => e.label_id === label_id);
      if (classification === undefined) return undefined;
      return classification.ai_pred;
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
      this.similar_comments = [];
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
    async loadSimilarComments(comment) {
      const payload = {
        ids: [comment.comment_id],
        n: 3
      };
      try {
        const { data } = await Service.post(Endpoint.COMMENTS_SIMILAR, payload);
        let comment_ids = data[0];
        // comment_ids = [1, 2, 3]; // for test purposes
        if (comment_ids !== undefined) {
          const comments = await Promise.all(
            comment_ids.map(id =>
              Service.get(
                Endpoint.COMMENT_ID(id, this[Getters.labelParameters]),
                this[Getters.jwt]
              )
            )
          );
          this.similar_comments = comments.map(response => response["data"]);
        }
      } catch (e) {
        console.error(`Could not load similar comments: ${e}`);
      }
    }
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

.columnTitle {
  font-size: 12pt;
}

.tableColumn {
  min-width: 60px;
}
</style>
