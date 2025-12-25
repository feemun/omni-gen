import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useAppStore = defineStore('app', () => {
  const api = axios.create({
    baseURL: 'http://localhost:8000/api'
  })

  const databaseConfigs = ref([])
  const redisConfigs = ref([])
  const esConfigs = ref([])
  const templateGroups = ref([])
  const loading = ref(false)
  const error = ref('')

  const fetchAll = async () => {
    loading.value = true
    try {
      const [dbRes, redisRes, esRes, groupsRes] = await Promise.all([
        api.get('/datasources/database'),
        api.get('/datasources/redis'),
        api.get('/datasources/es'),
        api.get('/template-groups')
      ])
      databaseConfigs.value = dbRes.data
      redisConfigs.value = redisRes.data
      esConfigs.value = esRes.data
      templateGroups.value = groupsRes.data
    } catch (err) {
      console.error(err)
      error.value = 'Failed to load data'
    } finally {
      loading.value = false
    }
  }

  return {
    api,
    databaseConfigs,
    redisConfigs,
    esConfigs,
    templateGroups,
    loading,
    error,
    fetchAll
  }
})
