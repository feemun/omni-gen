<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { FileCode, Plus, Trash2, Edit2, X, Save, Folder, FolderPlus, ArrowLeft, ChevronRight } from 'lucide-vue-next'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

// UI State
const activeGroup = ref(null) // Currently selected group object
const showGroupModal = ref(false)
const showTemplateModal = ref(false)

// Editing State (Group)
const isNewGroup = ref(false)
const editingGroup = ref({ id: null, name: '', description: '' })

// Editing State (Template)
const isNewTemplate = ref(false)
const editingTemplate = ref({ 
  id: null, 
  group_id: null,
  name: '', 
  display_name: '', 
  prompt: '', 
  content: '', 
  root_path: '',
  relative_path: ''
})

// --- Group Management ---

const openGroupModal = (group = null) => {
  if (group) {
    isNewGroup.value = false
    editingGroup.value = { ...group }
  } else {
    isNewGroup.value = true
    editingGroup.value = { id: null, name: '', description: '' }
  }
  showGroupModal.value = true
}

const saveGroup = async () => {
  if (!editingGroup.value.name) return alert('Name is required')
  
  try {
    if (isNewGroup.value) {
      await api.post('/template-groups', editingGroup.value)
    } else {
      await api.put(`/template-groups/${editingGroup.value.id}`, editingGroup.value)
    }
    showGroupModal.value = false
    await store.fetchAll()
    // If we were viewing this group, refresh activeGroup
    if (activeGroup.value && activeGroup.value.id === editingGroup.value.id) {
       activeGroup.value = store.templateGroups.find(g => g.id === editingGroup.value.id)
    }
  } catch (err) {
    alert('Failed to save group: ' + err.message)
  }
}

const deleteGroup = async (group) => {
  if (!confirm(`Delete group "${group.name}" and ALL its templates?`)) return
  try {
    await api.delete(`/template-groups/${group.id}`)
    if (activeGroup.value && activeGroup.value.id === group.id) {
      activeGroup.value = null
    }
    await store.fetchAll()
  } catch (err) {
    alert('Failed to delete: ' + err.message)
  }
}

const selectGroup = (group) => {
  activeGroup.value = group
}

// --- Template Management ---

const openTemplateModal = async (tmpl = null) => {
  if (tmpl) {
    isNewTemplate.value = false
    // Fetch full content
    try {
      const res = await api.get(`/templates/${tmpl.id}`)
      editingTemplate.value = { ...res.data }
    } catch (err) {
      return alert('Failed to load template: ' + err.message)
    }
  } else {
    isNewTemplate.value = true
    editingTemplate.value = {
      id: null,
      group_id: activeGroup.value.id,
      name: '',
      display_name: '',
      prompt: '',
      content: '',
      root_path: '',
      relative_path: ''
    }
  }
  showTemplateModal.value = true
}

const saveTemplate = async () => {
  if (!editingTemplate.value.name) return alert('Filename is required')
  if (!editingTemplate.value.name.endsWith('.jinja2')) {
    editingTemplate.value.name += '.jinja2'
  }
  
  try {
    if (isNewTemplate.value) {
      await api.post('/templates', editingTemplate.value)
    } else {
      await api.put(`/templates/${editingTemplate.value.id}`, editingTemplate.value)
    }
    showTemplateModal.value = false
    await store.fetchAll()
    // Refresh active group templates
    activeGroup.value = store.templateGroups.find(g => g.id === activeGroup.value.id)
  } catch (err) {
    alert('Failed to save template: ' + err.message)
  }
}

const deleteTemplate = async (tmpl) => {
  if (!confirm(`Delete template "${tmpl.name}"?`)) return
  try {
    await api.delete(`/templates/${tmpl.id}`)
    await store.fetchAll()
    activeGroup.value = store.templateGroups.find(g => g.id === activeGroup.value.id)
  } catch (err) {
    alert('Failed to delete: ' + err.message)
  }
}

onMounted(() => {
  store.fetchAll()
})
</script>

<template>
  <div class="templates-container">
    <!-- Breadcrumb Header -->
    <div class="header">
      <div class="title">
        <h1 v-if="!activeGroup">Template Groups</h1>
        <div v-else class="breadcrumb">
          <h1 class="clickable" @click="activeGroup = null">Template Groups</h1>
          <ChevronRight class="icon-sm" />
          <h1>{{ activeGroup.name }}</h1>
        </div>
        <p class="subtitle" v-if="!activeGroup">Organize your generation templates into groups.</p>
        <p class="subtitle" v-else>{{ activeGroup.description || 'Manage templates in this group.' }}</p>
      </div>
      
      <button v-if="!activeGroup" class="btn-primary" @click="openGroupModal()">
        <FolderPlus class="icon-sm" /> New Group
      </button>
      <button v-else class="btn-primary" @click="openTemplateModal()">
        <Plus class="icon-sm" /> New Template
      </button>
    </div>

    <!-- Group List View -->
    <div v-if="!activeGroup" class="grid-view">
      <div v-if="store.templateGroups.length === 0" class="empty-state">
        No template groups found. Click "New Group" to start.
      </div>
      
      <div v-for="group in store.templateGroups" :key="group.id" class="card group-card" @click="selectGroup(group)">
        <div class="card-icon group-icon">
          <Folder class="icon" />
        </div>
        <div class="card-content">
          <h3>{{ group.name }}</h3>
          <p class="count">{{ group.templates.length }} templates</p>
        </div>
        <div class="card-actions">
          <button class="btn-icon" @click.stop="openGroupModal(group)" title="Edit Group">
            <Edit2 class="icon-sm" />
          </button>
          <button class="btn-icon danger" @click.stop="deleteGroup(group)" title="Delete Group">
            <Trash2 class="icon-sm" />
          </button>
        </div>
      </div>
    </div>

    <!-- Template List View -->
    <div v-else class="grid-view">
      <div v-if="activeGroup.templates.length === 0" class="empty-state">
        No templates in this group. Click "New Template" to add one.
      </div>

      <div v-for="tmpl in activeGroup.templates" :key="tmpl.id" class="card template-card">
        <div class="card-icon tmpl-icon">
          <FileCode class="icon" />
        </div>
        <div class="card-content">
          <h3>{{ tmpl.display_name || tmpl.name }}</h3>
          <p class="filename">{{ tmpl.name }}</p>
        </div>
        <div class="card-actions">
          <button class="btn-icon" @click="openTemplateModal(tmpl)" title="Edit Template">
            <Edit2 class="icon-sm" />
          </button>
          <button class="btn-icon danger" @click="deleteTemplate(tmpl)" title="Delete Template">
            <Trash2 class="icon-sm" />
          </button>
        </div>
      </div>
    </div>

    <!-- Group Modal -->
    <div v-if="showGroupModal" class="modal-overlay">
      <div class="modal sm-modal">
        <div class="modal-header">
          <h3>{{ isNewGroup ? 'New Group' : 'Edit Group' }}</h3>
          <button class="btn-icon" @click="showGroupModal = false"><X class="icon-sm" /></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Group Name</label>
            <input v-model="editingGroup.name" type="text" placeholder="e.g. Spring Boot CRUD" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <input v-model="editingGroup.description" type="text" placeholder="Optional description" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-text" @click="showGroupModal = false">Cancel</button>
          <button class="btn-primary" @click="saveGroup">Save</button>
        </div>
      </div>
    </div>

    <!-- Template Editor Modal -->
    <div v-if="showTemplateModal" class="modal-overlay">
      <div class="modal editor-modal">
        <div class="modal-header">
          <h3>{{ isNewTemplate ? 'New Template' : 'Edit Template' }}</h3>
          <button class="btn-icon" @click="showTemplateModal = false"><X class="icon-sm" /></button>
        </div>
        
        <div class="editor-body">
          <div class="form-row">
            <div class="form-group half">
              <label>Display Name</label>
              <input v-model="editingTemplate.display_name" type="text" placeholder="e.g., Java Entity" />
            </div>
            <div class="form-group half">
              <label>Filename (ID)</label>
              <input v-model="editingTemplate.name" type="text" placeholder="entity.java.jinja2" />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group half">
              <label>Root Path</label>
              <input v-model="editingTemplate.root_path" type="text" placeholder="e.g. src/main/java" />
            </div>
            <div class="form-group half">
              <label>Relative Path Pattern</label>
              <input v-model="editingTemplate.relative_path" type="text" placeholder="e.g. com/example/entity/{{ TableName }}.java" />
            </div>
          </div>
          <small class="hint" style="margin-top: -12px; margin-bottom: 16px;">
             Final path = Root Path + Relative Path. Use &#123;&#123; TableName &#125;&#125; in Relative Path.
          </small>

          <div class="form-group">
            <label>LLM Prompt (System Instruction)</label>
            <textarea v-model="editingTemplate.prompt" class="prompt-editor" placeholder="Enter instructions for LLM generation..."></textarea>
          </div>

          <div class="form-group flex-1" style="display:none;">
            <label>Template Content (Jinja2)</label>
            <textarea v-model="editingTemplate.content" class="code-editor" spellcheck="false"></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-text" @click="showTemplateModal = false">Cancel</button>
          <button class="btn-primary" @click="saveTemplate">Save Template</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.templates-container {
  max-width: 1000px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clickable {
  cursor: pointer;
  color: #868e96;
}

.clickable:hover {
  color: #228be6;
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

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.card-icon {
  padding: 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.group-icon {
  background-color: #e7f5ff;
  color: #1c7ed6;
}

.tmpl-icon {
  background-color: #ebfbee;
  color: #2f9e44;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-content h3 {
  margin: 0 0 4px 0;
  font-size: 1rem;
  color: #212529;
  font-weight: 600;
}

.count, .filename {
  margin: 0;
  font-size: 0.85rem;
  color: #868e96;
}

.card-actions {
  display: flex;
  gap: 4px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #adb5bd;
}

/* Icons */
.icon { width: 24px; height: 24px; }
.icon-sm { width: 18px; height: 18px; }

/* Buttons & Forms (Reuse existing styles or define) */
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
}

.btn-text {
  background: none;
  border: none;
  color: #495057;
  padding: 8px 16px;
  cursor: pointer;
  font-weight: 500;
}

.btn-icon {
  background: none;
  border: none;
  padding: 8px;
  color: #adb5bd;
  cursor: pointer;
  border-radius: 4px;
}

.btn-icon:hover { background-color: #f1f3f5; color: #495057; }
.btn-icon.danger:hover { background-color: #fff5f5; color: #fa5252; }

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
}

.sm-modal { width: 400px; }
.editor-modal { width: 90%; max-width: 900px; height: 85vh; }

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 { margin: 0; font-size: 1.1rem; }

.modal-body { padding: 24px; overflow-y: auto; }
.editor-body { padding: 24px; flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 500; color: #495057; font-size: 0.9rem; }
.form-group input { width: 100%; padding: 8px 12px; border: 1px solid #dee2e6; border-radius: 6px; }
.form-row { display: flex; gap: 16px; margin-bottom: 16px; }
.form-group.half { flex: 1; margin-bottom: 0; }
.form-group.flex-1 { flex: 1; display: flex; flex-direction: column; min-height: 0; }

.prompt-editor {
  width: 100%;
  padding: 10px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  min-height: 300px;
  resize: vertical;
}

.code-editor {
  flex: 1;
  width: 100%;
  padding: 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
  font-size: 14px;
  background: #f8f9fa;
  resize: none;
}
.code-editor:focus { background: white; border-color: #228be6; outline: none; }
.hint { font-size: 0.8rem; color: #868e96; margin-top: 4px; display: block; }
</style>
