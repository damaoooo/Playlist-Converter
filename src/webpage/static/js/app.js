const { createApp, ref, reactive } = Vue

const app = createApp({
    setup() {
        const form = reactive({
            neteaseToken: '',
            appleToken: ''
        })
        const isLoading = ref(false)
        const isLoggedIn = ref(false)
        const isConverting = ref(false)
        const isCompleted = ref(false)
        const playlists = ref([])
        const conversionProgress = ref(0)
        const currentSong = ref(null)
        const manualSelection = ref(null)
        const playlistSelection = ref(null)
        const successSongs = ref([])
        const failedSongs = ref([])
        const skippedSongs = ref([])
        const ws = ref(null)
        const sessionId = ref(null)
        const manualSearchVisible = ref(false)
        const searchKeyword = ref('')
        const searchResults = ref([])

        const login = async () => {
            if (isLoading.value) return
            isLoading.value = true
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(form)
                })
                
                if (!response.ok) {
                    const error = await response.json()
                    throw new Error(error.detail || '登录失败')
                }
                
                const data = await response.json()
                sessionId.value = data.session_id
                playlists.value = data.playlists
                isLoggedIn.value = true
                setupWebSocket()
            } catch (error) {
                ElMessage.error(error.message)
            } finally {
                isLoading.value = false
            }
        }

        const setupWebSocket = () => {
            ws.value = new WebSocket(`ws://${window.location.host}/ws/${sessionId.value}`)
            ws.value.onmessage = (event) => {
                const data = JSON.parse(event.data)
                handleWebSocketMessage(data)
            }
            ws.value.onclose = () => {
                setTimeout(setupWebSocket, 1000)
            }
        }

        const handleWebSocketMessage = async (data) => {
            switch (data.type) {
                case 'progress':
                    conversionProgress.value = data.progress
                    currentSong.value = data.current_song
                    break
                case 'playlist_selection':
                    playlistSelection.value = data
                    break
                case 'song_selection':
                    manualSelection.value = data
                    break
                case 'completed':
                    isConverting.value = false
                    isCompleted.value = true
                    successSongs.value = data.successSongs
                    failedSongs.value = data.failedSongs
                    skippedSongs.value = data.skippedSongs
                    break
            }
        }

        const convertPlaylist = async (playlist) => {
            isConverting.value = true
            try {
                const response = await fetch('/api/convert_playlist', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        session_id: sessionId.value,
                        playlist_id: playlist.id,
                        playlist_name: playlist.name,
                        target_playlist_id: playlist.target_playlist_id,
                        target_playlist_name: playlist.target_playlist_name,
                        mode: playlist.mode
                    })
                })
                
                if (!response.ok) {
                    const error = await response.json()
                    throw new Error(error.detail || '转换失败')
                }
            } catch (error) {
                ElMessage.error(error.message)
                isConverting.value = false
            }
        }

        const selectSong = async (song) => {
            try {
                const response = await fetch('/api/select_song', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        song_id: song.id,
                        session_id: sessionId.value
                    })
                })
                
                if (!response.ok) {
                    const error = await response.json()
                    throw new Error(error.detail || '选择失败')
                }
                
                manualSelection.value = null
            } catch (error) {
                ElMessage.error(error.message)
            }
        }

        const skipSong = async () => {
            try {
                const response = await fetch('/api/skip_song', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        session_id: sessionId.value
                    })
                })
                
                if (!response.ok) {
                    const error = await response.json()
                    throw new Error(error.detail || '跳过失败')
                }
                
                manualSelection.value = null
            } catch (error) {
                ElMessage.error(error.message)
            }
        }

        const showManualSearch = () => {
            manualSearchVisible.value = true
            searchKeyword.value = ''
            searchResults.value = []
        }

        const performManualSearch = async () => {
            if (!searchKeyword.value) return
            
            try {
                const response = await fetch('/api/manual_search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        keyword: searchKeyword.value,
                        session_id: sessionId.value
                    })
                })
                
                if (!response.ok) {
                    const error = await response.json()
                    throw new Error(error.detail || '搜索失败')
                }
                
                const data = await response.json()
                searchResults.value = data.matches
            } catch (error) {
                ElMessage.error(error.message)
            }
        }

        const selectSearchResult = (song) => {
            selectSong(song)
            manualSearchVisible.value = false
        }

        return {
            form,
            isLoading,
            isLoggedIn,
            isConverting,
            isCompleted,
            playlists,
            conversionProgress,
            currentSong,
            manualSelection,
            playlistSelection,
            successCount,
            skipCount,
            errorCount,
            successSongs,
            failedSongs,
            skippedSongs,
            manualSearchVisible,
            searchKeyword,
            searchResults,
            login,
            convertPlaylist,
            selectSong,
            skipSong,
            showManualSearch,
            performManualSearch,
            selectSearchResult
        }
    }
})

app.use(ElementPlus)
app.mount('#app') 