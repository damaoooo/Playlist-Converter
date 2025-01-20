app.component('login-form', {
    template: `
        <div class="token-form fade-in" v-if="!isLoggedIn">
            <el-form :model="form" label-width="140px">
                <el-form-item label="网易云音乐ID">
                    <el-input
                        v-model="form.neteaseToken"
                        type="textarea"
                        :rows="3"
                        class="token-input"
                        :placeholder="defaultNeteaseToken"></el-input>
                </el-form-item>
                <el-form-item label="Apple Music Token">
                    <el-input
                        v-model="form.appleToken"
                        type="textarea"
                        :rows="3"
                        class="token-input"
                        :placeholder="defaultAppleToken"></el-input>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleLogin" :loading="isLoading" size="large">
                        {{ isLoading ? '登录中...' : '登录' }}
                    </el-button>
                </el-form-item>
            </el-form>
        </div>
    `,
    props: {
        isLoggedIn: {
            type: Boolean,
            required: true
        },
        isLoading: {
            type: Boolean,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            defaultNeteaseToken: process.env.VUE_APP_DEFAULT_NETEASE_TOKEN || '',
            defaultAppleToken: process.env.VUE_APP_DEFAULT_APPLE_TOKEN || ''
        }
    },
    emits: ['login'],
    methods: {
        handleLogin() {
            // 如果用户没有输入，使用默认值
            if (!this.form.neteaseToken) {
                this.form.neteaseToken = this.defaultNeteaseToken;
            }
            if (!this.form.appleToken) {
                this.form.appleToken = this.defaultAppleToken;
            }
            this.$emit('login')
        }
    }
}) 