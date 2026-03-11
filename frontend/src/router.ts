import { createRouter, createWebHistory } from "vue-router";
import SetupView from "./views/SetupView.vue";
import OverviewView from "./views/OverviewView.vue";
import RunsView from "./views/RunsView.vue";
import ExplorerView from "./views/ExplorerView.vue";
import ThemesView from "./views/ThemesView.vue";
import RecommendationsView from "./views/RecommendationsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/overview" },
    { path: "/setup", component: SetupView },
    { path: "/overview", component: OverviewView },
    { path: "/runs", component: RunsView },
    { path: "/explorer", component: ExplorerView },
    { path: "/themes", component: ThemesView },
    { path: "/recommendations", component: RecommendationsView }
  ]
});

export default router;
