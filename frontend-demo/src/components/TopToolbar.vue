<template>
  <div>
    <v-navigation-drawer app v-model="drawer" absolute temporary>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title class="title">Kommentaranalyse</v-list-item-title>
          <v-list-item-subtitle>Navigation</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <v-divider></v-divider>

      <v-list dense nav>
        <v-list-item v-for="item in items" :key="item.title" link>
          <v-list-item-icon>
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-icon>

          <v-list-item-content>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar flat color="indigo" max-height="60" dark>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>Analyse von Online-Nutzerkommentaren</v-toolbar-title>
      <v-spacer></v-spacer>
      <UserLogin />
    </v-app-bar>
  </div>
</template>

<script>
import UserLogin from "./UserLogin";
export default {
  data() {
    return {
      drawer: false,
      items: [
        { title: "Analyse", icon: "bar_chart" },
        { title: "Annotation", icon: "check" }
      ]
    };
  },
  components: {
    UserLogin
  }
};
</script>

<style>
</style>
