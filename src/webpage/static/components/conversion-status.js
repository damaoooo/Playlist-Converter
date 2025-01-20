app.component('conversion-status', {
    props: {
        isConverting: Boolean,
        conversionProgress: {
            type: Number,
            default: 0
        },
        currentSong: {
            type: Object,
            default: () => null
        },
        playlistSelection: {
            type: Object,
            default: () => null
        },
        manualSelection: {
            type: Object,
            default: () => null
        },
        manualSearchVisible: Boolean,
        searchKeyword: String,
        searchResults: {
            type: Array,
            default: () => []
        }
    },
    template: `
        <div v-if="isConverting" class="conversion-status">
            <el-progress :percentage="conversionProgress || 0" />
            
            <div v-if="currentSong && currentSong.name" class="current-song">
                <h3>正在处理</h3>
                <p>歌曲名称：{{ currentSong.name }}</p>
                <p>艺术家：{{ currentSong.artist }}</p>
                <p>专辑：{{ currentSong.album }}</p>
            </div>

            <!-- 播放列表选择对话框 -->
            <el-dialog
                v-if="playlistSelection"
                v-model="dialogVisible"
                title="选择目标播放列表"
                width="50%"
                :close-on-click-modal="false"
                :close-on-press-escape="false"
                :show-close="false">
                <div class="playlist-selection">
                    <el-radio-group v-model="selectedPlaylist">
                        <el-radio 
                            v-for="playlist in (playlistSelection?.playlists || [])" 
                            :key="playlist.id"
                            :label="playlist.id">
                            {{ playlist.name }}
                        </el-radio>
                    </el-radio-group>
                </div>
                <template #footer>
                    <el-button type="primary" @click="confirmPlaylistSelection">
                        确认选择
                    </el-button>
                </template>
            </el-dialog>

            <!-- 手动选择歌曲对话框 -->
            <el-dialog
                v-if="manualSelection"
                v-model="manualDialogVisible"
                title="选择匹配的歌曲"
                width="70%"
                :close-on-click-modal="false"
                :close-on-press-escape="false"
                :show-close="false">
                <div class="manual-selection">
                    <div v-if="manualSelection?.song_info" class="original-song">
                        <h4>原始歌曲</h4>
                        <p>歌曲名称：{{ manualSelection.song_info.name }}</p>
                        <p>艺术家：{{ manualSelection.song_info.artist }}</p>
                        <p>专辑：{{ manualSelection.song_info.album }}</p>
                    </div>
                    
                    <div class="matches">
                        <h4>匹配结果</h4>
                        <el-table :data="manualSelection?.matches || []" style="width: 100%">
                            <el-table-column prop="name" label="歌曲名称" />
                            <el-table-column prop="artist" label="艺术家" />
                            <el-table-column prop="album" label="专辑" />
                            <el-table-column fixed="right" label="操作" width="120">
                                <template #default="scope">
                                    <el-button type="primary" @click="selectMatch(scope.row)">
                                        选择
                                    </el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </div>

                    <div class="manual-selection-actions">
                        <el-button @click="skipCurrentSong">跳过这首歌</el-button>
                        <el-button type="primary" @click="showManualSearch">手动搜索</el-button>
                    </div>
                </div>
            </el-dialog>

            <!-- 手动搜索对话框 -->
            <el-dialog
                v-model="manualSearchVisible"
                title="手动搜索"
                width="70%">
                <div class="manual-search">
                    <el-input
                        v-model="searchKeyword"
                        placeholder="请输入搜索关键词"
                        @keyup.enter="performSearch">
                        <template #append>
                            <el-button @click="performSearch">搜索</el-button>
                        </template>
                    </el-input>

                    <el-table v-if="searchResults.length > 0" :data="searchResults" style="width: 100%; margin-top: 20px;">
                        <el-table-column prop="name" label="歌曲名称" />
                        <el-table-column prop="artist" label="艺术家" />
                        <el-table-column prop="album" label="专辑" />
                        <el-table-column fixed="right" label="操作" width="120">
                            <template #default="scope">
                                <el-button type="primary" @click="selectSearchResult(scope.row)">
                                    选择
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </el-dialog>
        </div>
    `,
    data() {
        return {
            selectedPlaylist: null,
            dialogVisible: false,
            manualDialogVisible: false
        }
    },
    watch: {
        playlistSelection(val) {
            this.dialogVisible = !!val
        },
        manualSelection(val) {
            this.manualDialogVisible = !!val
        }
    },
    methods: {
        confirmPlaylistSelection() {
            if (!this.selectedPlaylist || !this.playlistSelection) return
            const playlist = this.playlistSelection.playlists.find(p => p.id === this.selectedPlaylist)
            if (playlist) {
                this.$emit('select-playlist', playlist)
                this.dialogVisible = false
            }
        },
        selectMatch(song) {
            this.$emit('select-song', song)
            this.manualDialogVisible = false
        },
        skipCurrentSong() {
            this.$emit('skip-song')
            this.manualDialogVisible = false
        },
        showManualSearch() {
            this.$emit('show-manual-search')
        },
        performSearch() {
            if (!this.searchKeyword.trim()) {
                ElMessage.warning('请输入搜索关键词')
                return
            }
            this.$emit('perform-manual-search', this.searchKeyword.trim())
        },
        selectSearchResult(song) {
            this.$emit('select-search-result', song)
        }
    }
}) 