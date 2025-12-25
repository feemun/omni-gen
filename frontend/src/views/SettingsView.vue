<script setup>
import { RouterLink } from 'vue-router'
import { Database, FileCode, ChevronRight } from 'lucide-vue-next'
</script>

<template>
  <div class="settings-container">
    <h1>Settings</h1>

    <div class="settings-grid">
      <RouterLink to="/datasources" class="setting-card">
        <div class="icon-wrapper bg-blue">
          <Database class="icon" />
        </div>
        <div class="content">
          <h3>Data Sources</h3>
          <p>Manage database connections and configurations</p>
        </div>
        <ChevronRight class="arrow" />
      </RouterLink>

      <RouterLink to="/templates" class="setting-card">
        <div class="icon-wrapper bg-green">
          <FileCode class="icon" />
        </div>
        <div class="content">
          <h3>Templates</h3>
          <p>Manage code generation templates</p>
        </div>
        <ChevronRight class="arrow" />
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.setting-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.2s;
  color: inherit;
}

.setting-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border-color: #dee2e6;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
}

.bg-blue {
  background-color: #e7f5ff;
  color: #1971c2;
}

.bg-green {
  background-color: #ebfbee;
  color: #2f9e44;
}

.icon {
  width: 24px;
  height: 24px;
}

.content {
  flex: 1;
}

.content h3 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  color: #212529;
}

.content p {
  margin: 0;
  color: #868e96;
  font-size: 0.9rem;
}

.arrow {
  color: #adb5bd;
  width: 20px;
  height: 20px;
}
</style>
