<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { Settings, Info, X, Check } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

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

const useLLM = ref(true)

// Streaming State
const showStreamModal = ref(false)
const streamProgress = ref(0)
const streamTotal = ref(0)
const streamCurrentFile = ref('')
const streamCurrentTable = ref('')
const streamCurrentContent = ref('')
const streamLogs = ref([]) // History of completed files
const selectedHistoryFile = ref(null)

const selectHistoryFile = (log) => {
  selectedHistoryFile.value = log
}

const getDisplayContent = () => {
  if (streamCurrentFile.value && 
      selectedHistoryFile.value?.file === streamCurrentFile.value && 
      selectedHistoryFile.value?.table === streamCurrentTable.value) {
    return streamCurrentContent.value
  }
  if (selectedHistoryFile.value) {
    const key = `${selectedHistoryFile.value.table}:${selectedHistoryFile.value.file}`
    return generatedContentMap.value.get(key) || ''
  }
  return ''
}

const getDisplayFilename = () => {
  return selectedHistoryFile.value?.file || ''
}

const generate = async () => {
  if (selectedTables.value.length === 0) {
    error.value = "Please select at least one table"
    return
  }
  
  loading.value = true
  error.value = ''
  results.value = []
  
  // Reset Stream State
  showStreamModal.value = true
  streamProgress.value = 0
  streamTotal.value = 0
  streamCurrentFile.value = ''
  streamCurrentTable.value = ''
  streamCurrentContent.value = ''
  streamLogs.value = []
  selectedHistoryFile.value = null

  try {
    const response = await fetch('http://localhost:8000/api/generate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        db_url: dbUrl.value,
        selected_tables: selectedTables.value,
        template_group_id: selectedTemplateGroupId.value,
        use_llm: true
      })
    })

    if (!response.ok) {
      throw new Error(response.statusText)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      
      // Process all complete lines
      buffer = lines.pop() // Keep the last incomplete line in buffer
      
      for (const line of lines) {
        if (!line.trim()) continue
        try {
          const event = JSON.parse(line)
          handleStreamEvent(event)
        } catch (e) {
          console.error('Error parsing JSON stream:', e)
        }
      }
    }
    
    // Refresh results list
    // results.value should be populated from logs or by re-fetching
    // But since we have the content in logs? No, logs only have metadata.
    // The stream doesn't persist to `results` variable in the same way the old API did.
    // However, the backend DOES write files to disk.
    // So we can reconstruct `results` from `streamLogs` if we had the content, but we don't store full content in logs.
    
    // Better approach: Since files are written to disk, maybe we can just let user know it's done.
    // OR, we can accumulate content in a map and then show it.
    
    // Let's populate `results` from the accumulated data if possible.
    // But wait, `streamLogs` only has file path.
    // We need to store content in a map during stream.
    
  } catch (err) {
    error.value = err.message
    // Close modal on error
    showStreamModal.value = false
  } finally {
    loading.value = false
  }
}

// Map to store full content of generated files for display
const generatedContentMap = ref(new Map())

const handleStreamEvent = (event) => {
  switch (event.type) {
    case 'start':
      streamTotal.value = event.total
      generatedContentMap.value.clear()
      break
    case 'file_start':
      streamCurrentFile.value = event.file
      streamCurrentTable.value = event.table
      streamCurrentContent.value = '' // Clear content for new file
      selectedHistoryFile.value = { file: event.file, table: event.table }
      break
    case 'chunk':
      streamCurrentContent.value += event.content
      // Auto scroll to bottom of code block if needed
      break
    case 'file_end':
      streamProgress.value++
      // Store completed content
      const key = `${streamCurrentTable.value}:${streamCurrentFile.value}`
      generatedContentMap.value.set(key, streamCurrentContent.value)
      
      // Add to logs only if not already there (deduplication check)
      const existingIndex = streamLogs.value.findIndex(log => log.file === streamCurrentFile.value && log.table === streamCurrentTable.value)
      if (existingIndex === -1) {
        streamLogs.value.unshift({
          file: streamCurrentFile.value,
          table: streamCurrentTable.value
        })
      }
      
      // Update main results view progressively
      let tableResult = results.value.find(r => r.table === streamCurrentTable.value)
      if (!tableResult) {
        tableResult = { table: streamCurrentTable.value, files: [] }
        results.value.push(tableResult)
      }
      
      // Check if file already exists in results
      const existingFileIndex = tableResult.files.findIndex(f => f.relative_path === streamCurrentFile.value)
      const fileData = {
        template_name: 'Generated File', // We might want to pass this in event
        path: '', // Full path not critical for display
        root_path: '',
        relative_path: streamCurrentFile.value,
        code: streamCurrentContent.value
      }
      
      if (existingFileIndex !== -1) {
        tableResult.files[existingFileIndex] = fileData
      } else {
        tableResult.files.push(fileData)
      }

      // Reset current file state to prevent ghosting
      streamCurrentFile.value = ''
      streamCurrentTable.value = ''
      streamCurrentContent.value = ''
      break
    case 'done':
      // Maybe show a success message or button
      break
    case 'error':
      alert('Stream Error: ' + event.message)
      break
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

const highlightCode = (code, filename = '') => {
  if (!code) return ''
  
  // Try to guess language from filename
  let lang = ''
  if (filename) {
    const ext = filename.split('.').pop().toLowerCase()
    const map = {
      'java': 'java',
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'vue': 'xml', 
      'html': 'xml',
      'xml': 'xml',
      'sql': 'sql',
      'json': 'json',
      'md': 'markdown',
      'css': 'css',
      'scss': 'scss',
      'sh': 'bash',
      'yml': 'yaml',
      'yaml': 'yaml'
    }
    lang = map[ext]
  }

  try {
    if (lang && hljs.getLanguage(lang)) {
       return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
    }
    return hljs.highlightAuto(code).value
  } catch (e) {
    return code
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

      <div class="form-group" style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px; display: none;">
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
            <pre><code class="hljs" v-html="highlightCode(file.code)"></code></pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Stream Progress Modal -->
    <div v-if="showStreamModal" class="modal-overlay" @click.self="showStreamModal = false">
      <div class="modal stream-modal">
        <div class="modal-header">
          <div class="stream-header-info">
            <h3>Generating Code...</h3>
            <span class="progress-badge">{{ streamProgress }} / {{ streamTotal }}</span>
          </div>
          <button class="btn-icon" @click="showStreamModal = false"><X class="icon-sm" /></button>
        </div>
        
        <div class="modal-body stream-body">
          <!-- Left: History/List -->
          <div class="stream-sidebar">
            <h4>Generated Files</h4>
            <div class="file-list">
              <div v-if="streamCurrentFile" 
                   class="file-item"
                   :class="{ selected: selectedHistoryFile && selectedHistoryFile.file === streamCurrentFile }"
                   @click="selectHistoryFile({ file: streamCurrentFile, table: streamCurrentTable })">
                <div class="status-indicator loading"></div>
                <span class="name">{{ streamCurrentFile }}</span>
              </div>
              <div v-for="log in streamLogs" :key="log.file" 
                   class="file-item done"
                   :class="{ selected: selectedHistoryFile && selectedHistoryFile.file === log.file && selectedHistoryFile.table === log.table }"
                   @click="selectHistoryFile(log)">
                <div class="status-indicator success">
                  <Check class="icon-check" />
                </div>
                <span class="name">{{ log.file }}</span>
              </div>
            </div>
          </div>

          <!-- Right: Live Code -->
          <div class="stream-content">
            <div class="stream-content-header">
              <span v-if="streamCurrentFile"><strong>Generating:</strong> {{ streamCurrentFile }} ({{ streamCurrentTable }})</span>
              <span v-else-if="selectedHistoryFile"><strong>Viewing:</strong> {{ selectedHistoryFile.file }} ({{ selectedHistoryFile.table }})</span>
              <span v-else>Generation Complete</span>
            </div>
            <pre class="stream-code-block"><code class="hljs" style="background:transparent; padding:0;" v-html="highlightCode(getDisplayContent(), getDisplayFilename())"></code><span class="cursor" v-if="streamCurrentFile && selectedHistoryFile?.file === streamCurrentFile"></span></pre>
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

.stream-modal {
  width: 90vw;
  height: 90vh;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
}

.stream-header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-badge {
  background-color: #e7f5ff;
  color: #1c7ed6;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
}

.stream-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.stream-sidebar {
  flex: 1;
  border-right: 1px solid #e9ecef;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
  min-width: 200px; /* Ensure it doesn't get too small */
}

.stream-sidebar h4 {
  padding: 16px;
  margin: 0;
  border-bottom: 1px solid #e9ecef;
  font-size: 1rem;
  color: #495057;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.file-item.selected {
  background-color: #e7f5ff;
  border: 1px solid #74c0fc;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  font-weight: 600;
  color: #1971c2;
}

.status-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.status-indicator.loading {
  background-color: #40c057; /* Green for processing */
  box-shadow: 0 0 0 0 rgba(64, 192, 87, 0.7);
  animation: pulse-green-loading 1.5s infinite;
}

.status-indicator.success {
  background-color: #2f9e44; /* Darker green for done */
  color: white;
}

.icon-check {
  width: 14px;
  height: 14px;
  stroke-width: 3;
}

@keyframes pulse-green-loading {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(64, 192, 87, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 8px rgba(64, 192, 87, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(64, 192, 87, 0);
  }
}

@keyframes pulse-border {
  0% { border-color: #dee2e6; }
  50% { border-color: #74c0fc; }
  100% { border-color: #dee2e6; }
}

.file-item.done {
  color: #2f9e44;
}

.stream-content {
  flex: 3;
  display: flex;
  flex-direction: column;
  background-color: #1e1e1e;
  color: #d4d4d4;
  overflow: hidden;
}

.stream-content-header {
  padding: 10px 20px;
  background-color: #252526;
  border-bottom: 1px solid #333;
  color: #cccccc;
  font-size: 0.9rem;
}

.stream-code-block {
  flex: 1;
  margin: 0;
  padding: 20px;
  overflow: auto;
  font-family: 'Fira Code', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background-color: #d4d4d4;
  margin-left: 2px;
  animation: blink 1s step-end infinite;
  vertical-align: middle;
}

@keyframes blink {
  50% { opacity: 0; }
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
