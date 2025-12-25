<script setup>
import { RouterView } from 'vue-router'
import { Settings, User, ArrowLeft } from 'lucide-vue-next'
</script>

<template>
  <div class="layout">
    <header class="top-header">
      <div class="header-left">
        <RouterLink to="/" class="back-link" title="Back to Home">
          <ArrowLeft class="icon-sm" />
          <span>Back</span>
        </RouterLink>
        <div class="logo">
          <h2>AI Generator Settings</h2>
        </div>
      </div>
      <div class="header-spacer"></div>
      <div class="header-actions">
        <button class="header-btn user-btn" title="User Profile">
          <User class="icon-sm" />
        </button>
      </div>
    </header>

    <div class="main-wrapper">
      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
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

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #495057;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.back-link:hover {
  background-color: #f1f3f5;
  color: #212529;
}

.logo h2 {
  margin: 0;
  font-size: 1.1rem;
  color: #212529;
  font-weight: 600;
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

.user-btn {
  background-color: #e7f5ff;
  color: #1971c2;
}

.user-btn:hover {
  background-color: #d0ebff;
  color: #1864ab;
}

.icon-sm {
  width: 20px;
  height: 20px;
}

.main-wrapper {
  flex: 1;
  background-color: #f8f9fa;
}

.content {
  height: 100%;
}
</style>
