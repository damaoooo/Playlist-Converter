app.component('playlist-list', {
    props: {
        isLoggedIn: {
            type: Boolean,
            required: true
        },
        isConverting: {
            type: Boolean,
            required: true
        },
        playlists: {
            type: Array,
            required: true
        },
        appleMusicPlaylists: {
            type: Array,
            default: () => []
        }
    },
    emits: ['convert-playlist', 'fetch-apple-playlists'],
    template: `
        <div v-if="isLoggedIn && !isConverting" class="playlist-list">
            <h2>选择要转换的歌单</h2>
            <el-table :data="playlists" style="width: 100%" max-height="400">
                <el-table-column prop="name" label="歌单名称" min-width="180" show-overflow-tooltip />
                <el-table-column prop="trackCount" label="歌曲数量" width="100" />
                <el-table-column fixed="right" label="操作" width="120">
                    <template #default="scope">
                        <el-button type="primary" @click="showPlaylistDialog(scope.row)">
                            转换
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 歌单选择对话框 -->
            <el-dialog
                v-model="dialogVisible"
                title="选择目标歌单"
                width="500px"
            >
                <el-form :model="form" label-width="120px">
                    <el-form-item label="目标歌单">
                        <el-radio-group v-model="form.targetType">
                            <el-radio label="existing">使用已有歌单</el-radio>
                            <el-radio label="new">创建新歌单</el-radio>
                        </el-radio-group>
                    </el-form-item>

                    <!-- 已有歌单选择 -->
                    <el-form-item v-if="form.targetType === 'existing'" label="选择歌单">
                        <el-select v-model="form.existingPlaylistId" placeholder="请选择歌单">
                            <el-option
                                v-for="playlist in appleMusicPlaylists"
                                :key="playlist.id"
                                :label="playlist.name"
                                :value="playlist.id"
                            />
                        </el-select>
                    </el-form-item>

                    <!-- 新歌单名称输入 -->
                    <el-form-item v-if="form.targetType === 'new'" label="歌单名称">
                        <el-input v-model="form.newPlaylistName" placeholder="请输入新歌单名称" />
                    </el-form-item>

                    <!-- 转换模式选择（仅在选择已有歌单时显示） -->
                    <el-form-item v-if="form.targetType === 'existing'" label="转换模式">
                        <el-radio-group v-model="form.mode">
                            <el-radio label="append">追加模式</el-radio>
                            <el-radio label="override">覆盖模式</el-radio>
                        </el-radio-group>
                    </el-form-item>
                </el-form>

                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="dialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="handleConvert">
                            确认
                        </el-button>
                    </span>
                </template>
            </el-dialog>
        </div>
    `,
    data() {
        return {
            dialogVisible: false,
            selectedPlaylist: null,
            form: {
                targetType: 'new',
                existingPlaylistId: '',
                newPlaylistName: '',
                mode: 'append'
            }
        }
    },
    methods: {
        showPlaylistDialog(playlist) {
            this.selectedPlaylist = playlist;
            this.dialogVisible = true;
            // 获取 Apple Music 歌单列表
            this.$emit('fetch-apple-playlists');
        },
        handleConvert() {
            if (this.form.targetType === 'existing' && !this.form.existingPlaylistId) {
                ElMessage.warning('请选择目标歌单');
                return;
            }
            if (this.form.targetType === 'new' && !this.form.newPlaylistName.trim()) {
                ElMessage.warning('请输入新歌单名称');
                return;
            }

            // 准备转换参数
            const conversionParams = {
                ...this.selectedPlaylist,
                mode: this.form.targetType === 'existing' ? this.form.mode : 'new'
            };

            // 根据用户选择的模式添加不同的参数
            if (this.form.targetType === 'existing') {
                // 选择已有歌单，同时传递ID和名称
                const selectedPlaylist = this.appleMusicPlaylists.find(p => p.id === this.form.existingPlaylistId);
                if (selectedPlaylist) {
                    conversionParams.target_playlist_id = selectedPlaylist.id;
                    conversionParams.target_playlist_name = selectedPlaylist.name;
                }
            } else {
                // 新建歌单，只传递名称
                conversionParams.target_playlist_name = this.form.newPlaylistName.trim();
                conversionParams.target_playlist_id = null;
            }

            console.log('转换参数:', conversionParams);  // 添加日志
            this.$emit('convert-playlist', conversionParams);
            this.dialogVisible = false;
        }
    }
}); 