app.component('completion-status', {
    props: {
        isCompleted: Boolean,
        successCount: Number,
        skipCount: Number,
        errorCount: Number,
        successSongs: {
            type: Array,
            default: () => []
        },
        failedSongs: {
            type: Array,
            default: () => []
        },
        skippedSongs: {
            type: Array,
            default: () => []
        }
    },
    template: `
        <div v-if="isCompleted" class="completion-status">
            <el-result
                icon="success"
                title="转换完成"
                :sub-title="'成功添加 ' + successSongs.length + ' 首歌曲，跳过 ' + failedSongs.length + ' 首，失败 ' + skippedSongs.length + ' 首'">
            </el-result>

            <div class="conversion-details">
                <el-tabs type="border-card">
                    <el-tab-pane :label="'成功转换 (' + successSongs.length + ')'">
                        <el-table
                            :data="successSongs"
                            style="width: 100%"
                            max-height="400"
                            stripe>
                            <el-table-column prop="originalName" label="原歌曲名称" min-width="180" show-overflow-tooltip />
                            <el-table-column prop="originalArtist" label="原艺术家" min-width="120" show-overflow-tooltip />
                            <el-table-column prop="matchedName" label="匹配歌曲名称" min-width="180" show-overflow-tooltip />
                            <el-table-column prop="matchedArtist" label="匹配艺术家" min-width="120" show-overflow-tooltip />
                            <el-table-column prop="matchedAlbum" label="专辑" min-width="150" show-overflow-tooltip />
                        </el-table>
                    </el-tab-pane>
                    
                    <el-tab-pane :label="'未找到匹配 (' + failedSongs.length + ')'">
                        <el-table
                            :data="failedSongs"
                            style="width: 100%"
                            max-height="400"
                            stripe>
                            <el-table-column prop="name" label="歌曲名称" min-width="180" show-overflow-tooltip />
                            <el-table-column prop="artist" label="艺术家" min-width="120" show-overflow-tooltip />
                            <el-table-column prop="album" label="专辑" min-width="150" show-overflow-tooltip />
                            <el-table-column prop="reason" label="失败原因" min-width="150" show-overflow-tooltip />
                        </el-table>
                    </el-tab-pane>

                    <el-tab-pane :label="'用户跳过 (' + skippedSongs.length + ')'">
                        <el-table
                            :data="skippedSongs"
                            style="width: 100%"
                            max-height="400"
                            stripe>
                            <el-table-column prop="name" label="歌曲名称" min-width="180" show-overflow-tooltip />
                            <el-table-column prop="artist" label="艺术家" min-width="120" show-overflow-tooltip />
                            <el-table-column prop="album" label="专辑" min-width="150" show-overflow-tooltip />
                        </el-table>
                    </el-tab-pane>
                </el-tabs>

                <div class="statistics" style="margin-top: 20px; text-align: right; color: #606266;">
                    <p>总计: {{ successSongs.length + failedSongs.length + skippedSongs.length }} 首歌曲</p>
                    <p>成功: {{ successSongs.length }} 首</p>
                    <p>失败: {{ failedSongs.length }} 首</p>
                    <p>跳过: {{ skippedSongs.length }} 首</p>
                </div>
            </div>
        </div>
    `,
    computed: {
        totalSongs() {
            return this.successCount + this.skipCount + this.errorCount
        }
    }
}) 