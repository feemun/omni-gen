<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { Settings, Info, X } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const route = useRoute()
const router = useRouter()

const dbUrl = ref('')
const tables = ref([])
const selectedTables = ref([])
const selectedTemplateGroupId = ref('')
const results = ref([])
const error = ref('')
const loading = ref(false)

// Table Metadata Modal State
const showTableModal = ref(false)
const currentTableName = ref('')
const currentTableSchema = ref(null)
const loadingSchema = ref(false)

const selectedDsId = computed({
  get: () => route.query.dsId || '',
  set: (val) => router.push({ query: { ...route.query, dsId: val } })
})

const selectedDs = computed(() => store.databaseConfigs.find(d => String(d.id) === String(selectedDsId.value)))

// Watch for route query changes to update template selection
watch(() => route.query.template, (newVal) => {
  // If template is passed in query, we might need logic to find which group it belongs to
  // For now, let's just default to first group if available
  if (store.templateGroups.length > 0 && !selectedTemplateGroupId.value) {
    selectedTemplateGroupId.value = store.templateGroups[0].id
  }
}, { immediate: true })

// Watch for DS selection change to auto-connect
watch(selectedDs, (newDs) => {
  if (newDs) {
    dbUrl.value = newDs.url
    // Optional: Auto-connect when DS is selected
    // connect() 
  }
}, { immediate: true })

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

// Initialize
onMounted(async () => {
  await store.fetchAll()
  if (store.templateGroups.length > 0 && !selectedTemplateGroupId.value) {
    selectedTemplateGroupId.value = store.templateGroups[0].id
  }
})

const connect = async () => {
  loading.value = true
  error.value = ''
  tables.value = []
  try {
    const res = await api.post('/connect', { db_url: dbUrl.value })
    tables.value = res.data.tables
  } catch (err) {
    error.value = err.response?.data?.detail || err.message
  } finally {
    loading.value = false
  }
}

const useLLM = ref(false)

const generate = async () => {
  if (selectedTables.value.length === 0) {
    error.value = "Please select at least one table"
    return
  }
  
  loading.value = true
  error.value = ''
  results.value = []
  
  try {
    const res = await api.post('/generate', {
      db_url: dbUrl.value,
      selected_tables: selectedTables.value,
      template_group_id: selectedTemplateGroupId.value,
      use_llm: useLLM.value
    })
    results.value = res.data.results
  } catch (err) {
    error.value = err.response?.data?.detail || err.message
  } finally {
    loading.value = false
  }
}

const viewTableDetails = async (tableName) => {
  currentTableName.value = tableName
  currentTableSchema.value = null
  showTableModal.value = true
  loadingSchema.value = true
  
  try {
    const res = await api.post('/table-metadata', {
      db_url: dbUrl.value,
      table_name: tableName
    })
    currentTableSchema.value = res.data
  } catch (err) {
    alert('Failed to load table details: ' + (err.response?.data?.detail || err.message))
    showTableModal.value = false
  } finally {
    loadingSchema.value = false
  }
}
</script>

<template>
  <div class="home-container">
    <h1>Code Generator</h1>
    
    <div class="card">
      <h2>1. Database Connection</h2>
      <div class="form-group">
        <div class="ds-header">
          <label>Select Data Source:</label>
          <router-link to="/settings/datasources" class="config-link" title="Manage Data Sources">
            <Settings class="icon-sm" />
          </router-link>
        </div>
        <div class="ds-select-row">
          <select v-model="selectedDsId">
            <option value="" disabled>Select a data source...</option>
            <option v-for="ds in store.databaseConfigs" :key="ds.id" :value="ds.id">
              {{ ds.name }}
            </option>
            <option value="" disabled v-if="store.databaseConfigs.length === 0">No data sources available (Go to Settings)</option>
          </select>
          <button @click="connect" :disabled="loading || !dbUrl" class="btn btn-primary">Connect</button>
        </div>
        <div v-if="selectedDs" class="ds-info-box">
          <p><strong>Type:</strong> {{ selectedDs.type }}</p>
          <p><strong>URL:</strong> {{ selectedDs.url }}</p>
        </div>
      </div>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="tables.length > 0" class="card">
      <h2>2. Select Tables</h2>
      <div class="checkbox-grid">
        <div v-for="table in tables" :key="table.name" class="checkbox-item">
          <label class="checkbox-label">
            <input type="checkbox" :value="table.name" v-model="selectedTables">
            <div class="table-info">
              <span class="table-name">{{ table.name }}</span>
              <span v-if="table.comment" class="table-comment">{{ table.comment }}</span>
            </div>
          </label>
          <button class="btn-icon-sm" @click.stop="viewTableDetails(table.name)" title="View Table Details">
            <Info class="icon-xs" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="tables.length > 0" class="card">
      <h2>3. Select Template Group</h2>
      <div class="form-group">
        <select v-model="selectedTemplateGroupId">
          <option v-for="g in store.templateGroups" :key="g.id" :value="g.id">
            {{ g.name }} ({{ g.templates.length }} files)
          </option>
        </select>
        <p class="hint" v-if="selectedTemplateGroupId">
          {{ store.templateGroups.find(g => g.id === selectedTemplateGroupId)?.description }}
        </p>
      </div>

      <div class="form-group" style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
        <input type="checkbox" id="useLLM" v-model="useLLM">
        <label for="useLLM" style="margin:0; cursor: pointer;">Enable AI Generation (Using configured LLM)</label>
      </div>

      <button class="btn btn-success full-width" @click="generate" :disabled="loading">Generate Code</button>
    </div>

    <div v-if="results.length > 0" class="results-section">
      <h2>Generated Code</h2>
      <div v-for="res in results" :key="res.table" class="result-group">
        <h3 class="table-title">Table: {{ res.table }}</h3>
        
        <div class="file-tabs">
          <div v-for="file in res.files" :key="file.path" class="file-tab">
            <div class="file-header">
              <span class="file-name">{{ file.template_name }}</span>
              <div class="path-container">
                <span class="path-root" v-if="file.root_path">{{ file.root_path }}/</span>
                <span class="path-relative">{{ file.relative_path }}</span>
              </div>
            </div>
            <pre><code>{{ file.code }}</code></pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Metadata Modal -->
    <div v-if="showTableModal" class="modal-overlay" @click.self="showTableModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Table: {{ currentTableName }}</h3>
          <button class="btn-icon" @click="showTableModal = false"><X class="icon-sm" /></button>
        </div>
        <div class="modal-body">
          <div v-if="loadingSchema" class="loading-state">Loading schema...</div>
          <div v-else-if="currentTableSchema" class="schema-content">
            <table class="schema-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Nullable</th>
                  <th>PK</th>
                  <th>Default</th>
                  <th>Comment</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="col in currentTableSchema.columns" :key="col.name">
                  <td class="col-name">{{ col.name }}</td>
                  <td><span class="type-badge">{{ col.type }}</span></td>
                  <td>{{ col.nullable ? 'Yes' : 'No' }}</td>
                  <td><span v-if="col.primary_key" class="pk-badge">PK</span></td>
                  <td class="col-default">{{ col.default || '-' }}</td>
                  <td class="col-comment">{{ col.comment || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 2rem;
}

.card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  margin-bottom: 20px;
  border: 1px solid #e9ecef;
}

.form-group {
  margin-bottom: 15px;
}

.ds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.config-link {
  color: #adb5bd;
  transition: color 0.2s;
  display: flex;
  align-items: center;
}

.config-link:hover {
  color: #495057;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

.input-group {
  display: flex;
  gap: 10px;
}

input[type="text"] {
  flex: 1;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.ds-select-row {
  display: flex;
  gap: 10px;
}

select {
  flex: 1;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.btn {
  padding: 10px 20px;
  cursor: pointer;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  transition: background-color 0.2s;
}

.ds-info-box {
  margin-top: 15px;
  padding: 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #495057;
}

.ds-info-box p {
  margin: 4px 0;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #228be6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1c7ed6;
}

.btn-success {
  background-color: #40c057;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #37b24d;
}

.full-width {
  width: 100%;
}

.error {
  background-color: #fff5f5;
  color: #fa5252;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 20px;
  border: 1px solid #ffc9c9;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  background-color: #fff;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 6px 10px;
  transition: all 0.2s;
}

.checkbox-item:hover {
  border-color: #adb5bd;
  background-color: #f8f9fa;
}

.checkbox-label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  overflow: hidden;
}

.table-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.95rem;
}

.table-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-comment {
  font-size: 0.8rem;
  color: #868e96;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-icon-sm {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: #adb5bd;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
}

.btn-icon-sm:hover {
  background-color: #e9ecef;
  color: #228be6;
}

.icon-xs {
  width: 14px;
  height: 14px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #212529;
}

.modal-body {
  padding: 0;
  overflow-y: auto;
  flex: 1;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  color: #adb5bd;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon:hover {
  background-color: #f1f3f5;
  color: #495057;
}

.loading-state {
  padding: 40px;
  text-align: center;
  color: #adb5bd;
}

/* Schema Table */
.schema-table {
  width: 100%;
  border-collapse: collapse;
}

.schema-table th,
.schema-table td {
  padding: 12px 24px;
  text-align: left;
  border-bottom: 1px solid #f1f3f5;
}

.schema-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
  position: sticky;
  top: 0;
}

.schema-table tr:last-child td {
  border-bottom: none;
}

.col-name {
  font-family: 'Fira Code', monospace;
  font-weight: 500;
  color: #212529;
}

.type-badge {
  background-color: #e7f5ff;
  color: #1864ab;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
}

.pk-badge {
  background-color: #fff9db;
  color: #f08c00;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid #fcc419;
}

.col-default {
  color: #868e96;
  font-family: monospace;
  font-size: 0.9rem;
}

.col-comment {
  color: #868e96;
  font-style: italic;
  font-size: 0.9rem;
}

.results-section {
  margin-top: 30px;
}

.result-group {
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.table-title {
  background: #f8f9fa;
  margin: 0;
  padding: 12px 20px;
  font-size: 16px;
  color: #212529;
  border-bottom: 1px solid #e9ecef;
  font-weight: 600;
}

.file-tabs {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.file-tab {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
}

.file-header {
  background: #f1f3f5;
  padding: 8px 12px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
}

.path-container {
  display: flex;
  align-items: baseline;
  font-family: monospace;
  font-size: 0.8rem;
}

.path-root {
  color: #adb5bd;
}

.path-relative {
  color: #495057;
  font-weight: 600;
}

.hint {
  display: block;
  margin-top: 6px;
  font-size: 0.85rem;
  color: #868e96;
}

pre {
  margin: 0;
  padding: 20px;
  overflow-x: auto;
  background: #212529;
  color: #f8f9fa;
  font-family: 'Fira Code', monospace;
  font-size: 0.9rem;
}
</style>
