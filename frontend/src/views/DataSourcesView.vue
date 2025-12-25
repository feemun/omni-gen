<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Database, Plus, Trash2, Edit2, X, Save, Server, Search, ArrowLeft } from 'lucide-vue-next'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

const activeTab = ref('all') // 'all', 'database', 'redis', 'es'
const showModal = ref(false)
const modalStep = ref(1) // 1: Type Selection, 2: Configuration
const isEditing = ref(false)
const editingId = ref(null)

// Generic form data holder
const formData = ref({})
const selectedType = ref('') // 'mysql', 'postgresql', 'redis', etc.

// Define supported data source types with metadata
const dataSourceTypes = [
  { id: 'mysql', name: 'MySQL', category: 'database', color: '#00758f', icon: Database },
  { id: 'postgresql', name: 'PostgreSQL', category: 'database', color: '#336791', icon: Database },
  { id: 'sqlite', name: 'SQLite', category: 'database', color: '#003b57', icon: Database },
  { id: 'redis', name: 'Redis', category: 'redis', color: '#dc382d', icon: Server },
  { id: 'es', name: 'Elasticsearch', category: 'es', color: '#f08c00', icon: Search },
]

const openModal = (item = null, type = null) => {
  formData.value = {} // Reset form
  if (item) {
    // Edit Mode
    isEditing.value = true
    modalStep.value = 2
    editingId.value = item.id
    
    // Determine type based on item properties or passed type context
    // We need to know the type to render correct form. 
    // For DatabaseConfig, it has 'type' field. For Redis/ES, we imply type.
    if (item.type) { // DatabaseConfig
      selectedType.value = item.type
    } else if (item.host && item.db_index !== undefined) { // Redis
      selectedType.value = 'redis'
    } else if (item.hosts) { // ES
      selectedType.value = 'es'
    }
    
    formData.value = { ...item }
  } else {
    // Add New Mode
    isEditing.value = false
    editingId.value = null
    modalStep.value = 1
    selectedType.value = ''
  }
  showModal.value = true
}

const selectType = (typeId) => {
  selectedType.value = typeId
  modalStep.value = 2
  
  // Initialize default values based on type
  if (typeId === 'mysql') {
    formData.value = { name: '', type: 'mysql', host: 'localhost', port: 3306, username: '', password: '', database_name: '' }
  } else if (typeId === 'postgresql') {
    formData.value = { name: '', type: 'postgresql', host: 'localhost', port: 5432, username: '', password: '', database_name: '' }
  } else if (typeId === 'sqlite') {
    formData.value = { name: '', type: 'sqlite', database_name: '' }
  } else if (typeId === 'redis') {
    formData.value = { name: '', host: 'localhost', port: 6379, password: '', db_index: 0 }
  } else if (typeId === 'es') {
    formData.value = { name: '', hosts: 'http://localhost:9200', username: '', password: '' }
  }
}

const saveConfig = async () => {
  if (!formData.value.name) {
    alert('Please enter a name')
    return
  }
  
  // Determine endpoint based on selectedType
  let endpoint = ''
  if (['mysql', 'postgresql', 'sqlite'].includes(selectedType.value)) {
    endpoint = '/datasources/database'
  } else if (selectedType.value === 'redis') {
    endpoint = '/datasources/redis'
  } else if (selectedType.value === 'es') {
    endpoint = '/datasources/es'
  }
  
  try {
    if (isEditing.value) {
      await api.put(`${endpoint}/${editingId.value}`, formData.value)
    } else {
      await api.post(endpoint, formData.value)
    }
    
    showModal.value = false
    await store.fetchAll()
  } catch (err) {
    alert('Failed to save: ' + (err.response?.data?.detail || err.message))
  }
}

const deleteConfig = async (id, category) => {
  if (!confirm('Are you sure you want to delete this configuration?')) return
  
  const endpointMap = {
    database: '/datasources/database',
    redis: '/datasources/redis',
    es: '/datasources/es'
  }
  const endpoint = endpointMap[category]

  try {
    await api.delete(`${endpoint}/${id}`)
    await store.fetchAll()
  } catch (err) {
    alert('Failed to delete: ' + err.message)
  }
}

const allConfigs = computed(() => {
  const dbs = store.databaseConfigs.map(c => ({ ...c, category: 'database', icon: Database, color: '#00758f' }))
  const redis = store.redisConfigs.map(c => ({ ...c, category: 'redis', icon: Server, color: '#dc382d', type: 'redis' }))
  const es = store.esConfigs.map(c => ({ ...c, category: 'es', icon: Search, color: '#f08c00', type: 'elasticsearch' }))
  
  let all = [...dbs, ...redis, ...es]
  
  if (activeTab.value !== 'all') {
    all = all.filter(c => c.category === activeTab.value)
  }
  return all
})

onMounted(() => {
  store.fetchAll()
})
</script>

<template>
  <div class="ds-container">
    <div class="header">
      <div class="title">
        <h1>Data Sources</h1>
        <p class="subtitle">Manage your connection configurations.</p>
      </div>
      <button class="btn-primary" @click="openModal()">
        <Plus class="icon-sm" /> Add New
      </button>
    </div>

    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">All</button>
      <button class="tab-btn" :class="{ active: activeTab === 'database' }" @click="activeTab = 'database'">Database</button>
      <button class="tab-btn" :class="{ active: activeTab === 'redis' }" @click="activeTab = 'redis'">Redis</button>
      <button class="tab-btn" :class="{ active: activeTab === 'es' }" @click="activeTab = 'es'">Elasticsearch</button>
    </div>

    <div class="ds-list">
      <div v-if="allConfigs.length === 0" class="empty-state">
        No configurations found. Click "Add New" to get started.
      </div>
      
      <div v-for="item in allConfigs" :key="item.category + item.id" class="ds-item">
        <div class="ds-icon-wrapper" :style="{ backgroundColor: item.color + '20', color: item.color }">
          <component :is="item.icon" class="icon" />
        </div>
        
        <div class="ds-info">
          <span class="ds-name">{{ item.name }}</span>
          <span class="ds-meta">
            <span class="badge">{{ item.type }}</span>
            <span v-if="item.url" class="url">{{ item.url }}</span>
            <span v-else-if="item.host" class="url">{{ item.host }}:{{ item.port || '' }}</span>
            <span v-else-if="item.hosts" class="url">{{ item.hosts }}</span>
          </span>
        </div>

        <div class="ds-actions">
          <button class="btn-icon" @click="openModal(item)" title="Edit">
            <Edit2 class="icon-sm" />
          </button>
          <button class="btn-icon danger" @click="deleteConfig(item.id, item.category)" title="Delete">
            <Trash2 class="icon-sm" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal" :class="{ 'modal-lg': modalStep === 1 }">
        <div class="modal-header">
          <div class="header-left">
            <button v-if="modalStep === 2 && !isEditing" class="btn-icon back-btn" @click="modalStep = 1">
              <ArrowLeft class="icon-sm" />
            </button>
            <h3>
              <span v-if="modalStep === 1">Select Connection Type</span>
              <span v-else>{{ isEditing ? 'Edit' : 'New' }} {{ dataSourceTypes.find(t => t.id === selectedType)?.name }} Connection</span>
            </h3>
          </div>
          <button class="btn-icon" @click="showModal = false"><X class="icon-sm" /></button>
        </div>
        
        <div class="modal-body">
          <!-- Step 1: Type Selection Grid -->
          <div v-if="modalStep === 1" class="type-grid">
            <div 
              v-for="type in dataSourceTypes" 
              :key="type.id" 
              class="type-card"
              @click="selectType(type.id)"
            >
              <div class="type-icon" :style="{ backgroundColor: type.color }">
                <component :is="type.icon" class="icon-white" />
              </div>
              <span class="type-name">{{ type.name }}</span>
            </div>
          </div>

          <!-- Step 2: Configuration Form -->
          <div v-else class="config-form">
            <div class="form-group">
              <label>Name</label>
              <input v-model="formData.name" type="text" placeholder="e.g., Local Dev" autofocus />
            </div>

            <!-- MySQL / PostgreSQL / SQLite Fields -->
            <template v-if="['mysql', 'postgresql', 'sqlite'].includes(selectedType)">
              <template v-if="selectedType !== 'sqlite'">
                <div class="form-row">
                  <div class="form-group flex-2">
                    <label>Host</label>
                    <input v-model="formData.host" type="text" />
                  </div>
                  <div class="form-group flex-1">
                    <label>Port</label>
                    <input v-model="formData.port" type="number" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group half">
                    <label>Username</label>
                    <input v-model="formData.username" type="text" />
                  </div>
                  <div class="form-group half">
                    <label>Password</label>
                    <input v-model="formData.password" type="password" />
                  </div>
                </div>
              </template>

              <div class="form-group">
                <label>{{ selectedType === 'sqlite' ? 'File Path' : 'Database Name' }}</label>
                <input v-model="formData.database_name" type="text" :placeholder="selectedType === 'sqlite' ? 'data.db' : 'my_db'" />
                <small v-if="selectedType === 'sqlite'" class="hint">Relative path from backend</small>
              </div>
            </template>

            <!-- Redis Fields -->
            <template v-if="selectedType === 'redis'">
              <div class="form-row">
                <div class="form-group flex-2">
                  <label>Host</label>
                  <input v-model="formData.host" type="text" />
                </div>
                <div class="form-group flex-1">
                  <label>Port</label>
                  <input v-model="formData.port" type="number" />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group half">
                  <label>Password (Optional)</label>
                  <input v-model="formData.password" type="password" />
                </div>
                <div class="form-group half">
                  <label>DB Index</label>
                  <input v-model="formData.db_index" type="number" />
                </div>
              </div>
            </template>

            <!-- ES Fields -->
            <template v-if="selectedType === 'es'">
              <div class="form-group">
                <label>Hosts (comma separated)</label>
                <input v-model="formData.hosts" type="text" placeholder="http://localhost:9200" />
              </div>
              <div class="form-row">
                <div class="form-group half">
                  <label>Username</label>
                  <input v-model="formData.username" type="text" />
                </div>
                <div class="form-group half">
                  <label>Password</label>
                  <input v-model="formData.password" type="password" />
                </div>
              </div>
            </template>
          </div>
        </div>
        
        <div class="modal-footer" v-if="modalStep === 2">
          <button class="btn-text" @click="showModal = false">Cancel</button>
          <button class="btn-primary" @click="saveConfig">
            <Save class="icon-sm" /> Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ds-container {
  max-width: 900px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.title h1 {
  margin: 0 0 4px 0;
  font-size: 1.5rem;
  color: #212529;
}

.subtitle {
  margin: 0;
  color: #868e96;
  font-size: 0.95rem;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 1px;
}

.tab-btn {
  background: none;
  border: none;
  padding: 8px 16px;
  font-size: 0.95rem;
  font-weight: 500;
  color: #868e96;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #495057;
}

.tab-btn.active {
  color: #228be6;
  border-bottom-color: #228be6;
}

.ds-list {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  min-height: 200px;
}

.ds-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f1f3f5;
  transition: background-color 0.2s;
}

.ds-item:last-child {
  border-bottom: none;
}

.ds-item:hover {
  background-color: #f8f9fa;
}

.ds-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.ds-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ds-name {
  font-weight: 600;
  color: #343a40;
}

.ds-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.badge {
  background-color: #f1f3f5;
  color: #495057;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.url {
  color: #adb5bd;
  font-family: monospace;
}

.ds-actions {
  display: flex;
  gap: 4px;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #adb5bd;
  background-color: #f8f9fa;
}

.icon {
  width: 20px;
  height: 20px;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

.icon-white {
  width: 24px;
  height: 24px;
  color: white;
}

/* Buttons */
.btn-primary {
  background-color: #228be6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #1c7ed6;
}

.btn-text {
  background: none;
  border: none;
  color: #495057;
  cursor: pointer;
  padding: 8px 16px;
  font-weight: 500;
}

.btn-text:hover {
  color: #212529;
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

.btn-icon.danger:hover {
  background-color: #fff5f5;
  color: #fa5252;
}

/* Modal */
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
  max-width: 500px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  transition: max-width 0.3s;
}

.modal-lg {
  max-width: 800px;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #212529;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Type Grid */
.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px;
}

.type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 20px;
  border: 1px solid transparent;
  border-radius: 8px;
  transition: all 0.2s;
}

.type-card:hover {
  background-color: #f8f9fa;
  border-color: #e9ecef;
  transform: translateY(-2px);
}

.type-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.type-name {
  font-weight: 500;
  color: #495057;
  text-align: center;
}

/* Form Styles */
.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group.half {
  flex: 1;
  margin-bottom: 0;
}

.form-group.flex-2 {
  flex: 2;
  margin-bottom: 0;
}

.form-group.flex-1 {
  flex: 1;
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  color: #495057;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #228be6;
}

.hint {
  display: block;
  margin-top: 6px;
  font-size: 0.8rem;
  color: #868e96;
}
</style>
