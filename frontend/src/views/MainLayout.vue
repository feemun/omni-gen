<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Settings, Home, Database, FileCode, User } from 'lucide-vue-next'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const route = useRoute()

onMounted(() => {
  store.fetchAll()
})
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <RouterLink to="/" class="logo-link">
          <h2>AI Generator</h2>
        </RouterLink>
      </div>
      
      <div class="sidebar-content">
        <!-- Home -->
        <div class="nav-section">
          <RouterLink to="/" class="nav-item main-link">
            <Home class="icon" />
            <span>Home</span>
          </RouterLink>
        </div>

        <!-- Data Sources -->
        <div class="nav-section">
          <div class="section-title">
            <div class="title-left">
              <Database class="icon-xs" />
              <span>Data Sources</span>
            </div>
          </div>
          <div class="nav-list">
            <div v-if="store.databaseConfigs.length === 0" class="empty-msg">No data sources</div>
            <RouterLink 
              v-for="ds in store.databaseConfigs" 
              :key="ds.id"
              :to="{ name: 'home', query: { ...route.query, dsId: ds.id } }"
              class="sub-item"
              :class="{ active: route.name === 'home' && String(route.query.dsId) === String(ds.id) }"
            >
              {{ ds.name }}
            </RouterLink>
          </div>
        </div>

        <!-- Template Groups -->
        <div class="nav-section">
          <div class="section-title">
            <div class="title-left">
              <FileCode class="icon-xs" />
              <span>Templates</span>
            </div>
          </div>
          <div class="nav-list">
            <RouterLink to="/settings/templates" class="sub-item" :class="{ active: route.path === '/settings/templates' }">
              Manage Templates
            </RouterLink>
            <div class="divider-h"></div>
            <div v-if="store.templateGroups.length === 0" class="empty-msg">No groups</div>
            <RouterLink 
              v-for="group in store.templateGroups" 
              :key="group.id"
              :to="{ name: 'home', query: { ...route.query, templateGroup: group.id } }"
              class="sub-item"
              :class="{ active: route.name === 'home' && String(route.query.templateGroup) === String(group.id) }"
            >
              {{ group.name }}
            </RouterLink>
          </div>
        </div>
      </div>
    </aside>

    <div class="main-wrapper">
      <header class="top-header">
        <div class="header-spacer"></div>
        <div class="header-actions">
          <div class="divider"></div>
          <RouterLink to="/settings" class="header-btn" title="Settings">
            <Settings class="icon-sm" />
          </RouterLink>
          <button class="header-btn user-btn" title="User Profile">
            <User class="icon-sm" />
          </button>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  background-color: #f8f9fa;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  z-index: 100;
}

.logo {
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
  background: white;
  height: 60px;
  display: flex;
  align-items: center;
}

.logo-link {
  text-decoration: none;
}

.logo h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #212529;
  font-weight: 700;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.nav-section {
  margin-bottom: 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  color: #495057;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-item:hover {
  background-color: #e9ecef;
  color: #212529;
}

.nav-item.router-link-active {
  color: #1971c2;
  background-color: #e7f5ff;
}

.section-title {
  padding: 8px 20px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #868e96;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-list {
  display: flex;
  flex-direction: column;
}

.divider-h {
  height: 1px;
  background-color: #e9ecef;
  margin: 4px 20px;
}

.sub-item {
  padding: 8px 20px 8px 48px;
  color: #495057;
  text-decoration: none;
  font-size: 0.95rem;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.sub-item:hover {
  color: #212529;
  background-color: #f1f3f5;
}

.sub-item.active {
  color: #1971c2;
  background-color: #e7f5ff;
  border-left-color: #1971c2;
  font-weight: 500;
}

.empty-msg {
  padding: 8px 20px 8px 48px;
  font-size: 0.85rem;
  color: #adb5bd;
  font-style: italic;
}

.main-wrapper {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
}

.top-header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  padding: 0 2rem;
  position: sticky;
  top: 0;
  z-index: 90;
}

.header-spacer {
  flex: 1;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: #495057;
  text-decoration: none;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.header-btn:hover {
  background-color: #f1f3f5;
  color: #212529;
}

.divider {
  width: 1px;
  height: 24px;
  background-color: #dee2e6;
  margin: 0 8px;
}

.user-btn {
  background-color: #e7f5ff;
  color: #1971c2;
}

.user-btn:hover {
  background-color: #d0ebff;
  color: #1864ab;
}

.icon {
  width: 20px;
  height: 20px;
}

.icon-xs {
  width: 16px;
  height: 16px;
}

.icon-sm {
  width: 20px;
  height: 20px;
}

.content {
  padding: 2rem;
  max-width: 1200px;
}
</style>
