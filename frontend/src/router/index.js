import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import MainLayout from '../views/MainLayout.vue'
import SettingsLayout from '../views/SettingsLayout.vue'
import SettingsRootLayout from '../views/SettingsRootLayout.vue'
import DataSourcesView from '../views/DataSourcesView.vue'
import TemplatesView from '../views/TemplatesView.vue'
import LLMConfigView from '../views/LLMConfigView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView
        }
      ]
    },
    {
      path: '/settings',
      component: SettingsRootLayout,
      redirect: '/settings/datasources',
      children: [
        {
          path: '',
          component: SettingsLayout,
          children: [
            {
              path: 'datasources',
              name: 'settings-datasources',
              component: DataSourcesView
            },
            {
              path: 'templates',
              name: 'settings-templates',
              component: TemplatesView
            },
            {
              path: 'llm',
              name: 'settings-llm',
              component: LLMConfigView
            }
          ]
        }
      ]
    }
  ]
})

export default router
