import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./styles.css";

const routes = [
  { path: "/", component: App },
  { path: "/about", component: App },
  { path: "/contact", component: App },
  { path: "/search", component: App },
  { path: "/category/:id", component: App },
  { path: "/post/:id", component: App },
  { path: "/page/:slug", component: App },
  { path: "/services/:slug", component: App },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

createApp(App).use(router).mount("#app");
