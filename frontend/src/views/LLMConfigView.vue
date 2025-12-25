<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Cpu, Plus, Trash2, Edit2, X, Save, Check, CheckCircle2 } from 'lucide-vue-next'

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

const configs = ref([])
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const formData = ref({
  name: '',
  provider: 'ollama',
  base_url: 'http://localhost:11434/v1',
  api_key: '',
  model_name: '',
  is_active: false
})

const fetchConfigs = async () => {
  try {
    const res = await api.get('/llm')
    configs.value = res.data
  } catch (err) {
    alert('Failed to fetch LLM configs: ' + err.message)
  }
}

const openModal = (config = null) => {
  if (config) {
    isEditing.value = true
    editingId.value = config.id
    formData.value = { ...config }
  } else {
    isEditing.value = false
    editingId.value = null
    formData.value = {
      name: '',
      provider: 'ollama',
      base_url: 'http://localhost:11434/v1',
      api_key: '',
      model_name: '',
      is_active: false
    }
  }
  showModal.value = true
}

const saveConfig = async () => {
  if (!formData.value.name || !formData.value.base_url || !formData.value.model_name) {
    alert('Please fill in required fields (Name, Base URL, Model Name)')
    return
  }
  
  try {
    if (isEditing.value) {
      await api.put(`/llm/${editingId.value}`, formData.value)
    } else {
      await api.post('/llm', formData.value)
    }
    showModal.value = false
    await fetchConfigs()
  } catch (err) {
    alert('Failed to save config: ' + (err.response?.data?.detail || err.message))
  }
}

const deleteConfig = async (id) => {
  if (!confirm('Are you sure you want to delete this configuration?')) return
  try {
    await api.delete(`/llm/${id}`)
    await fetchConfigs()
  } catch (err) {
    alert('Failed to delete: ' + err.message)
  }
}

const activateConfig = async (config) => {
  if (config.is_active) return
  try {
    // We update it to be active. The backend handles deactivating others.
    const updated = { ...config, is_active: true }
    await api.put(`/llm/${config.id}`, updated)
    await fetchConfigs()
  } catch (err) {
    alert('Failed to activate config: ' + err.message)
  }
}

// Watch provider change to set default base_url
const onProviderChange = () => {
  if (formData.value.provider === 'ollama') {
    formData.value.base_url = 'http://localhost:11434/v1'
  } else if (formData.value.provider === 'openai_compatible') {
    formData.value.base_url = 'https://api.openai.com/v1'
  }
}

onMounted(() => {
  fetchConfigs()
})
</script>

<template>
  <div class="llm-container">
    <div class="header">
      <div class="title">
        <h1>LLM Configuration</h1>
        <p class="subtitle">Manage Large Language Model connections (Ollama, OpenAI, etc).</p>
      </div>
      <button class="btn-primary" @click="openModal()">
        <Plus class="icon-sm" /> Add New
      </button>
    </div>

    <div class="config-list">
      <div v-if="configs.length === 0" class="empty-state">
        No LLM configurations found. Click "Add New" to get started.
      </div>
      
      <div v-for="conf in configs" :key="conf.id" class="config-item" :class="{ active: conf.is_active }">
        <div class="status-indicator" @click="activateConfig(conf)" :title="conf.is_active ? 'Active' : 'Click to Activate'">
          <CheckCircle2 v-if="conf.is_active" class="icon-status active" />
          <div v-else class="icon-status inactive"></div>
        </div>
        
        <div class="config-icon-wrapper">
          <Cpu class="icon" />
        </div>
        
        <div class="config-info">
          <div class="info-header">
            <span class="config-name">{{ conf.name }}</span>
            <span v-if="conf.is_active" class="badge-active">Active</span>
          </div>
          <span class="config-meta">
            <span class="badge">{{ conf.provider }}</span>
            <span class="model">{{ conf.model_name }}</span>
            <span class="url">{{ conf.base_url }}</span>
          </span>
        </div>
        
        <div class="config-actions">
          <button class="btn-icon" @click="openModal(conf)" title="Edit">
            <Edit2 class="icon-sm" />
          </button>
          <button class="btn-icon danger" @click="deleteConfig(conf.id)" title="Delete">
            <Trash2 class="icon-sm" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ isEditing ? 'Edit LLM Config' : 'Add LLM Config' }}</h3>
          <button class="btn-icon" @click="showModal = false"><X class="icon-sm" /></button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Config Name</label>
            <input v-model="formData.name" type="text" placeholder="e.g., My Local Ollama" />
          </div>
          
          <div class="form-group">
            <label>Provider</label>
            <select v-model="formData.provider" @change="onProviderChange">
              <option value="ollama">Ollama (Local)</option>
              <option value="openai_compatible">OpenAI Compatible / API</option>
            </select>
          </div>

          <div class="form-group">
            <label>Base URL</label>
            <input v-model="formData.base_url" type="text" placeholder="http://localhost:11434/v1" />
          </div>

          <div class="form-group">
            <label>Model Name</label>
            <input v-model="formData.model_name" type="text" placeholder="e.g., llama3, gpt-4o" />
          </div>

          <div class="form-group">
            <label>API Key (Optional for Ollama)</label>
            <input v-model="formData.api_key" type="password" placeholder="sk-..." />
          </div>

          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="formData.is_active">
              Set as Active Model
            </label>
          </div>
        </div>
        
        <div class="modal-actions">
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
.llm-container {
  max-width: 800px;
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

.config-list {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
}

.config-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f1f3f5;
  transition: background-color 0.2s;
}

.config-item:last-child {
  border-bottom: none;
}

.config-item:hover {
  background-color: #f8f9fa;
}

.config-item.active {
  background-color: #f0fff4;
}

.status-indicator {
  padding: 0 12px 0 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.icon-status {
  width: 20px;
  height: 20px;
}

.icon-status.active {
  color: #2f9e44;
}

.icon-status.inactive {
  width: 18px;
  height: 18px;
  border: 2px solid #dee2e6;
  border-radius: 50%;
}

.icon-status.inactive:hover {
  border-color: #adb5bd;
}

.config-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: #f3f0ff;
  color: #7950f2;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.config-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-name {
  font-weight: 600;
  color: #343a40;
}

.badge-active {
  background-color: #d3f9d8;
  color: #2b8a3e;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.config-meta {
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

.model {
  font-weight: 500;
  color: #495057;
}

.url {
  color: #adb5bd;
  font-family: monospace;
}

.config-actions {
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
  max-width: 450px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  padding: 20px;
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
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
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

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #212529;
}

.modal-actions {
  padding: 20px;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
