<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { Database, FileCode, Cpu } from 'lucide-vue-next'

const route = useRoute()

const isActive = (path) => route.path.startsWith(path)
</script>

<template>
  <div class="settings-layout">
    <aside class="settings-sidebar">
      <nav>
        <RouterLink to="/settings/datasources" class="nav-item" :class="{ active: isActive('/settings/datasources') }">
          <Database class="icon" />
          <span>Data Sources</span>
        </RouterLink>
        <RouterLink to="/settings/templates" class="nav-item" :class="{ active: isActive('/settings/templates') }">
          <FileCode class="icon" />
          <span>Templates</span>
        </RouterLink>
        <RouterLink to="/settings/llm" class="nav-item" :class="{ active: isActive('/settings/llm') }">
          <Cpu class="icon" />
          <span>LLM Config</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="settings-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.settings-layout {
  display: flex;
  height: calc(100vh - 60px); /* Subtract top header height */
}

.settings-sidebar {
  width: 240px;
  background-color: white;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
}

nav {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  color: #495057;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.nav-item:hover {
  background-color: #f8f9fa;
  color: #212529;
}

.nav-item.active {
  background-color: #e7f5ff;
  color: #1971c2;
  font-weight: 500;
}

.icon {
  width: 18px;
  height: 18px;
}

.settings-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  background-color: #fff;
}
</style>
