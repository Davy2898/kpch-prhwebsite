import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./styles.css";

const routes = [
  { path: "/", component: App },
  { path: "/news", component: App },
  { path: "/updates", component: App },
  { path: "/about", component: App },
  { path: "/contact", component: App },
  { path: "/search", component: App },
  { path: "/category/:id", component: App },
  { path: "/post/:id", component: App },
  { path: "/page/:slug", component: App },
  { path: "/services/:slug", component: App },
];

const routerBase =
  window.location.pathname === "/static/vue" || window.location.pathname.startsWith("/static/vue/")
    ? "/static/vue/"
    : "/";

const router = createRouter({
  history: createWebHistory(routerBase),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    if (to.hash) {
      return { el: to.hash, behavior: "smooth" };
    }
    return { top: 0, behavior: "smooth" };
  },
});

createApp(App).use(router).mount("#app");
