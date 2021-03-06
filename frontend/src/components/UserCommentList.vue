<template>
  <div>
    <h3>{{ $t("comment_list.title") }}</h3>

    <v-layout>
      <v-flex xs12>
        <v-text-field
          v-model="enteredKeyword"
          :label="$t('comment_list.search')"
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
            <v-icon v-if="loggedIn" :title="$t('comment_list.annotation.human.header.user')">person</v-icon>
            <v-icon v-if="!loggedIn" :title="$t('comment_list.annotation.human.header.majority')">people</v-icon>
            <v-btn icon @click="sortClickListener({header})" :title="$t('comment_list.annotation.classifier.header.title')" class="d-inline-block">
              <v-icon>{{svgPath}}</v-icon>
            </v-btn>
            <div v-if="showSortArrow(header)" @click="sortClickListener({header})">
              <v-icon v-if="order===2" :title="$t('comment_list.annotation.classifier.header.order.positive')">arrow_downward</v-icon>
              <v-icon v-else-if="order===1" :title="$t('comment_list.annotation.classifier.header.order.negative')">arrow_upward</v-icon>
              <v-icon v-else :title="$t('comment_list.annotation.classifier.header.order.uncertain')">check_circle_outline</v-icon>
            </div>
          </div>
        </div>
      </template>

      <template
        v-slot:footer.page-text="{pageStart, pageStop}"
      >{{ $t("comment_list.page", {number: Math.floor(pageStart/rowsPerPage)+1})}}</template>

      <template v-slot:item="props">
        <tr :class="{'mb-2': true, 'similarComment': props.item.isSimilar}" v-if="props.item.title || props.item.text">
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
          <td class="text-center actionsCell">
            <div class="actionsContainer">
              <v-btn icon @click="toggleSimilar(props.item)">
                <Similar />
              </v-btn>
              <UserCommentDetailsDialog :comment="props.item">
                <template #activator="{ on, attrs}">
                  <v-btn icon v-on="on" v-bind="attrs">
                    <v-icon>chevron_right</v-icon>
                  </v-btn>
                </template>
              </UserCommentDetailsDialog>
            </div>
          </td>
        </tr>
      </template>
      <template #expanded-item />
    </v-data-table>
  </div>
</template>

<script>
import Service from "../api/db";
import { State, Getters, Mutations } from "../store/const";
import { mapState, mapGetters, mapMutations } from "vuex";
import moment from "moment";
import { EventBus, Events } from "../event-bus";
import UserCommentAnnotation from "./UserCommentAnnotation";
import { mdiRobot } from "@mdi/js";
import Similar from './icons/Similar.vue';
import UserCommentDetailsDialog from './commentdetails/UserCommentDetailsDialog.vue';

export default {
  name: "UserCommentList",
  data() {
    return {
      enteredKeyword: "",
      headerPrefix: "header.",
      pageComments: [],
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
      svgPath: mdiRobot,
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
    ...mapState([State.labels, State.selectedCategory]),
    ...mapGetters([
      Getters.selectedLabelIds,
      Getters.keywordfilter,
      Getters.selectedLabels,
      Getters.jwtLoggedIn,
      Getters.getSelectedSource,
    ]),
    loggedIn() {
      return this[Getters.jwtLoggedIn];
    },
    comments() {
      const expandSimilar = (val) =>
        Array.isArray(val)
        ? val.flatMap(val => expandSimilar(val))
        : [val, ...(val.similar || []).flatMap(expandSimilar)];
      
      return expandSimilar(this.pageComments);
    },
    commentsTableHeader() {
      return [
        {
          text: this.$i18n.t("comment_list.headers.comment_text"),
          align: "left",
          sortable: false,
          value: "text",
          width: "80%"
        },
        {
          text: this.$i18n.t("comment_list.headers.date"),
          align: "right",
          sortable: false,
          value: "timestamp",
          width: "15%"
        },
        ...this[Getters.selectedLabels].map(e => ({
          text: e,
          align: "center",
          sortable: false,
          value: "text",
          width: "15%",
          labelColumn: true
        })),
        {
          text: this.$i18n.t("comment_list.headers.actions"),
          align: "left",
          sortable: false,
          value: "actions",
          width: "15%",
        }
      ]
    }
  },
  async mounted() {
    EventBus.$on(Events.loggedIn, this.fetchComments);
    EventBus.$on(Events.sourceLoaded, this.loadTable);
  },
  watch: {
    [Getters.selectedLabels]: function() {
      this.loadTable();
    },
    [State.selectedCategory]: async function() {
      this.loading = true;
      await this.fetchComments();
      this.loading = false;
    },
    async page() {
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
    ...mapMutations([Mutations.setKeywordfilter]),
    async loadTable() {
      this.loading = true;
      this.page = 1;
      await this.fetchComments();
      this.loading = false;
    },
    async toggleSimilar(comment) {
      if (comment.similar) {
        this.$set(comment, 'similar', null);
      } else {
        const { data } = await Service.getSimilarComments(comment.id, {
          n: 5,
          labelIds: this[Getters.selectedLabelIds],
        });
        this.$set(comment, 'similar', data.slice(1).map(similarComment => ({...similarComment, isSimilar: true})));
      }
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
      const { data } = await Service.getComments(this[Getters.getSelectedSource].id, {
        labelIds: this[Getters.selectedLabelIds],
        keywords: this[Getters.keywordfilter].split(' ').filter(kw => kw.length >= 1),
        limit: this.rowsPerPage,
        skip: (this.page - 1) * this.rowsPerPage,
        labelSortId: this.label_sort_id,
        order: this.label_sort_id ? this.order : null,
        category: this[State.selectedCategory] || null,
      })

      this.pageComments = data;
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
      props.expand(!props.isExpanded);
    },
    /*eslint no-unused-vars: ["error", { "args": "none" }]*/
    keywordChanged(e) {
      this[Mutations.setKeywordfilter](this.enteredKeyword);
      this.loadTable();
    }
  },
  components: {
    UserCommentAnnotation,
    Similar,
    UserCommentDetailsDialog,
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

.actionsCell {
  vertical-align: middle;
}

.actionsContainer {
  display: flex;
  align-items: center;
  justify-content: center;
}

.similarComment {
  animation: highlight-similar 750ms 200ms forwards ease-out;
}

@keyframes highlight-similar {
  0% { background-color: transparent; }
  30% { background-color: #c0c6f1; }
  100% { background-color: #f2f3fb; }
}

</style>
