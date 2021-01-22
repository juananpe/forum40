<template>
  <v-progress-circular v-if="document === null" :indeterminate="true" />

  <div v-else>
    <h1>{{document.title}}</h1>
    <v-btn v-if="!showCompleteArticle" @click="showCompleteArticle = true">{{$t('comment_details.document_position.show_complete')}}</v-btn>
    
    <div class="content">
      <p v-for="paragraph of visibleParagraphs" :key="paragraph.index" :class="paragraphClass(paragraph.index)">
        {{paragraph.content}}
      </p>
    </div>
  </div>
</template>

<script>
import { Getters } from "../../store/const";
import { mapGetters } from "vuex";
import Service, { Endpoint } from "../../api/db";

export default {
  props: ['comment'],
  computed: {
    ...mapGetters([Getters.jwt])
  },
  data() {
    return {
      document: null,
      showCompleteArticle: false,
    }
  },
  computed: {
    visibleParagraphs() {
      if (!this.document) {
        return null;
      }

      return this.document.paragraphs.slice(
        this.firstVisiblePragraphIndex,
        this.lastVisibleParagraphIndex + 1,
      )
    },
    firstVisiblePragraphIndex() {
      if (this.showCompleteArticle) {
        return 0;
      } else {
        return Math.max(0, this.maxLinkScoreParagraphIndex - 1);
      }
    },
    lastVisibleParagraphIndex() {
      if (this.showCompleteArticle) {
        return this.document.paragraphs.length - 1;
      } else {
        return Math.min(this.document.paragraphs.length - 1, this.maxLinkScoreParagraphIndex + 1);
      }
    },
    maxLinkScoreParagraphIndex() {
      if (!this.document) {
        return -1;
      }

      const [maxIdx] = this.document.paragraphs
          .map(par => par.link_score)
          .reduce(([prevIdx, prevMax], curVal, curIdx) => 
            (curVal > prevMax ? [curIdx, curVal] : [prevIdx, prevMax]), [-1, Number.MIN_VALUE]);
      
      return maxIdx;
    },
  },

  watch: {
    comment: {
      immediate: true,
      async handler(comment) {
        this.document = null;
        const { data: doc } = await Service.get(
          Endpoint.COMMENT_DOCUMENT(this.comment.id),
          this[Getters.jwt],
        );
        this.document = {
          ...doc,
          paragraphs: doc.paragraphs.map((par, i) => ({...par, index: i})),
        };
      },
    },
  },
  methods: {
    paragraphClass(index) {
      return {
        paragraph: true,
        'linked-paragraph': index === this.maxLinkScoreParagraphIndex,
      }
    }
  },
}
</script>

<style scoped>
  .content {
    padding: 2rem 0;
  }

  .paragraph {
    margin: 0 0 0.2rem;
    padding: 0.4rem 0.8rem;
    border-radius: 0.2rem;
  }

  .paragraph:last-child {
    margin-bottom: 0;
  }

  .linked-paragraph {
    background-color: #f8df75;
  }
</style>