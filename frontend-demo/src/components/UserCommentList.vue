<template>
  <div>
    <h3>Kommentarliste</h3>

    <v-layout>
      <v-flex xs12>
        <v-text-field
          v-model="enteredKeyword"
          label="Textsuche"
          append-icon="search"
          @keydown.enter="keywordChanged"
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
      :server-items-length="Number.MAX_VALUE"
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
            <v-icon @click="sortClickListener({header})" class="ml-1">{{svgPath}}</v-icon>
            <div v-if="showSortArrow(header)" @click="sortClickListener({header})">
              <v-icon v-if="order===2">arrow_downward</v-icon>
              <v-icon v-else-if="order===1">arrow_upward</v-icon>
              <v-icon v-else>check_circle_outline</v-icon>
            </div>
          </div>
        </div>
      </template>

      <template
        v-slot:footer.page-text="{pageStart, pageStop}"
      >Seite {{Math.floor(pageStart/rowsPerPage)+1}}</template>

      <template v-slot:item="props">
        <tr class="mb-2" v-if="props.item.title || props.item.text">
          <td @click="commentClicked(props)">
            <v-icon v-if="!props.isExpanded">expand_more</v-icon>

            <v-icon v-else>expand_less</v-icon>
          </td>
          <td @click="commentClicked(props)" class="text-left commenttext">
            <div>
              <div v-if="props.item.title">
                <b v-html="highlight(props.item.title, enteredKeyword)"></b>
                <br />
              </div>
              <span
                v-if="!props.isExpanded"
                v-html="highlight(shortText(props.item.text), enteredKeyword)"
              ></span>
              <span v-else v-html="highlight(props.item.text, enteredKeyword)"></span>
            </div>
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
          <td v-for="(label, i) in selectedLabels" :key="item.id+i"></td>
        </tr>
        <tr
          class="elevation-1 sim-comments"
          v-for="(comment, i) in similar_comments.slice(1,MAX_COMMENTS)"
          :key="i"
        >
          <td v-if="similar_comments.length>0"></td>
          <td v-if="similar_comments.length>0">
            <b>{{comment.title}}</b>
            <br />
            {{comment.text}}
          </td>
          <td v-if="similar_comments.length>0" class="text-right">{{ comment.timestamp | moment}}</td>

          <td v-for="(label, i) in selectedLabels" :key="comment.id+i">
            <UserCommentAnnotation
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
      enteredKeyword: "",
      headerPrefix: "header.",
      comments: [],
      order: 2,
      label_sort_id: null,
      expanded: [],
      loading: false,
      selected: [],
      expand: false,
      footerprops: {
        "items-per-page-options": [10, 25, 50, 100]
      },
      teaserTextLength: 200,
      page: 1,
      rowsPerPage: 25,
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
      MAX_COMMENTS: 11
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
    pageQueryString() {
      const parameters = [];

      // add source
      const selectedSource = this[Getters.getSelectedSource];
      if (selectedSource) parameters.push(`source_id=${selectedSource.id}`);

      // add labels
      const labelParameters = this[Getters.labelParameters];
      if (labelParameters) parameters.push(labelParameters);

      // add keyword
      if (this.enteredKeyword) {
        const keywords = this.enteredKeyword.split(" ");
        keywords.forEach(kw => parameters.push(`keyword=${kw}`));
      }

      // add skip
      const skip = (this.page - 1) * this.rowsPerPage;
      parameters.push(`skip=${skip}`);

      // add limit
      parameters.push(`limit=${this.rowsPerPage}`);

      // add sorting
      if (this.label_sort_id) {
        parameters.push(`order=${this.order}`);
        parameters.push(`label_sort_id=${this.label_sort_id}`);
      }

      const queryString = parameters.join("&");

      return queryString;
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
      await this.fetchComments();
      this.loading = false;
    },
    getHeaderSlotname(header) {
      return this.headerPrefix + header;
    },
    getPeronalAnnotation(annotations, label_id) {
      if (annotations === undefined) return undefined;
      const annotation = annotations.find(e => e.label_id === label_id);
      if (annotation === undefined) return undefined; // no annotation for this label found
      if (annotation.user === null) return undefined;
      return !!annotation.user;
    },
    getGroupAnnotation(annotations, label_id) {
      if (annotations === undefined) return undefined;
      const annotation = annotations.find(e => e.label_id === label_id);
      if (annotation === undefined) return undefined;
      if (
        annotation.group_count_true === null ||
        annotation.group_count_false === null
      )
        return undefined;
      return [annotation.group_count_true, annotation.group_count_false];
    },
    getConfidence(annotations, label_id) {
      if (annotations === undefined) return undefined;
      const classification = annotations.find(e => e.label_id === label_id);
      if (classification === undefined) return undefined;
      return classification.ai_pred;
    },
    shortText(text) {
      if (!text) return "";
      return this.$options.filters.truncate(text, this.teaserTextLength);
    },
    highlight: function(words, query) {
      if (query) {
        const keywords = query.split(" ");
        let highlightedText = words;
        keywords.forEach(kw => {
          if (kw) {
            const regEx = new RegExp("(" + kw + ")", "ig");
            highlightedText = highlightedText.replace(
              regEx,
              '<span class="highlight">' + "$1" + "</span>"
            );
          }
        });
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
    sortClickListener({ header }) {
      const label = header.text;
      const label_sort_id = this[State.labels][label];
      if (this.label_sort_id != label_sort_id) this.order = 2;
      else this.order = ++this.order % 3;
      this.label_sort_id = label_sort_id;
      this.fetchComments();
    },
    showSortArrow(header) {
      const label_sort_id = this[State.labels][header.text];
      return label_sort_id === this.label_sort_id;
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
    async loadSimilarComments(comment) {
      const selectedSource = this[Getters.getSelectedSource];
      const payload = {
        ids: [comment.id],
        n: this.MAX_COMMENTS,
        source_id: selectedSource.id
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
        console.error('Could not load similar comments: ${e}');
      }
    },
    /*eslint no-unused-vars: ["error", { "args": "none" }]*/
    keywordChanged(e) { 
      this[Mutations.setKeywordfilter](this.enteredKeyword);
      this.loadTable();
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
  color: black;
}

.tableColumn {
  min-width: 60px;
}

.sim-comments {
  background-color: #eeeeff;
}
</style>
