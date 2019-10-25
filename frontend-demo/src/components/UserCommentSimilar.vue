<template>
  <td colspan="100%" class="elevation-1">
    <v-btn
      v-if="!similar_texts.length"
      outlined
      small
      color="primary"
      text
      @click="loadSimilarComments()"
    >Ähnliche Kommentare anzeigen</v-btn>

    <v-container fluid>
      <v-row dense>
        <v-card
          v-for="(comment, i) in similar_texts.slice(0,MAX_COMMENTS)"
          :key="i"
          max-width="'100%'"
          outlined
        >
          <v-list-item three-line>
            <v-list-item-content>{{i+1}}. {{comment}}</v-list-item-content>
          </v-list-item>
        </v-card>
      </v-row>
    </v-container>
  </td>
</template>
  

<script>
import Service, { Endpoint } from "../api/db";

export default {
  props: {
    comment: Object
  },
  data() {
    return {
      similar_texts: [],
      MAX_COMMENTS: 3
    };
  },
  methods: {
    async loadSimilarComments() {
      const payload = {
        comments: [this.comment.text],
        n: 3
      };
      try {
        const { data } = await Service.post(Endpoint.COMMENTS_SIMILAR, payload);
        this.similar_texts = data[0];
        this.similar_texts = [
          "halb off-topic: israelische doku \u00fcber kurdische soldatinnen, deren stellung in der kurdischen gesellschaft und deren rolle im kampf gegen daesh.\r\n\r\nf\u00fcr mich war es ber\u00fchrend.\r\n\r\n\r\n\r\nich bin mir bewusst, dass im internet ein propaganda- und informationskrieg herrscht. falls einer betrachterin versteckte propaganda auff\u00e4llt oder sie sonst interessante infos zu dem thema hat, bitte hier posten. danke und viel spass",
          "sox!!!! ich bin stolz und gl\u00fccklich als pensionierte socke der ersten stunde das hier zu lesen. so cool dass es euch noch immer gibt. \r\nauf viele weitere meisterinnentitel!\r\nliz",
          "da sich zu diesem artikel einige  braune stinker outen, hab ich mal eine mit-poster verfolgung gestartet, sehr ergibieg f\u00fcr das ignore-konto. \u00fcbrigens, was sind das f\u00fcr userkonten, die nix posten aber >50 follower/mitposter haben. leuchtturmkonten?",
          "tja - ende 2016 wird der liebe herr golob einige tolle abenteuer erlebt haben und um einige sehr interessante erfahrungen reicher sein. und war auch noch teil einer coolen fernsehshow.\r\n\r\nbin gespannt, was der durchschnittliche n\u00f6rgler bis ende 2016 erreicht haben wird. 5 postings pro tag in einem forum, die dann eh keiner liest?",
          "ich h\u00e4tte jetzt nat\u00fcrlich ein paar screenshots machen sollen, aber es waren gerade bei dem ergebnis der gemeinderatswahl nach bezirken einige sehr komische zahlenfehler dabei\r\n\r\nbtw. diese grafik ist jetzt ja gar nicht mehr da....\r\naber zumindest das vorhandene funktioniert, danke",
          'mein lieber schwan - \u00e4h - standard! bei bild 7 von new york (weil\'s halt der "big apple" ist) auf das computerunternehmen zu verlinken ist schon etwas... naja. ich habe auch einiges an elektronischem obst zuhause rumstehen, aber gleich \u00fcberall eine verbindung zu sehen... ;-)',
          "richtig so wie ja auch produkte aus nordzypern, der krim oder tibet ausgezeichnet sind\r\n\r\nah... sind sie nicht?\r\n\r\nhmn, dann handelt sich es leider bei dieser auszeichnung um antisemitismus.\r\n\r\nad redaktion. bin neugierig, ob dieses posting mal freigeschalten wird.",
          "ich hab gar nix erfasst. ich wieder-verwende nur. das ist das sch\u00f6ne an open data. die datenbank stellt der tennis-guru jeff sackmann hier zur verf\u00fcgung: https://github.com/JeffSackmann/tennis_atp\r\n\r\nlaut aktuellem stand sind 45000 spieler in der datenbank ;)",
          "OT, gelber rand.. wei\u00df ejmand warum meine und auch andere postings so einen gelben rand links haben?\r\n\r\nanscheinend wird der von der css klasse 'posting.is-topposting' ausgel\u00f6st.\r\nwie komm ich zu der ehr'?",
          "ok, tats\u00e4chlich interessant. als gro\u00dfer fan der fr\u00fcheren zombie modi bin ich gespannt, und auch die l\u00e4ngere kampagne klingt nicht schlecht. auch wenn 15 stunden jetzt nicht unbedingt jubelstr\u00f6me ausl\u00f6sen, ist es bei weitem besser, als die 6 stunden zuvor. mal schaun, was die rezensionen sagen. \r\n\r\nund bitte geb uns offline coop. wir wollen das!",
          "wie weit betreibt hr. r\u00fcbig lobbying f\u00fcr telekomunternehmen? der herr r\u00fcbig ist ja ein nicht ganz unbekannter. interessant w\u00e4re, bei welchen telekomunternehmen er auf der gehaltsliste steht?\r\n\r\nhttp://www.profil.at/home/eu-die-geschaefte-oevp-abgeordneten-paul-ruebig-299667\r\n\r\nw\u00e4re doch eine interessante rechere, oder lieber standard?"
        ];
        console.log(data[0]);
      } catch (e) {
        console.error("Could not load similar comments!");
      }
    }
  }
};
</script>

<style>
</style>