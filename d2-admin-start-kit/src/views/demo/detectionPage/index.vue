<template>
  <d2-container class="layout-container">
    <h1 class="d2-mt-0">文件检测系统</h1>
    <el-row :gutter="20" class="main-row">
      <!-- 左侧上传区域 -->
      <el-col :span="12" class="left-panel">
        <el-card class="upload-card">
          <div slot="header" class="card-header">
            <i class="el-icon-upload"></i>
            <span>文件上传区</span>
          </div>

          <el-upload
            class="uploader"
            drag
            action="/api/upload"
            :show-file-list="false"
            :tiemout="3000000"
            :on-success="handleSuccess"
            :before-upload="beforeUpload">
            <div class="upload-area">
              <i class="el-icon-upload" style="font-size: 40px; color: #409EFF;"></i>
              <div class="upload-text">
                <p>点击或拖拽文件到此区域</p>
                <p class="tip-text">支持格式：JPEG/PNG/MP4</p>
              </div>
            </div>
          </el-upload>
        </el-card>
      </el-col>

      <!-- 右侧结果区域 -->
      <el-col :span="12" class="right-panel">
        <el-card class="result-card">
          <div slot="header" class="card-header">
            <i class="el-icon-document"></i>
            <span>检测结果</span>
          </div>

          <div v-if="previewUrl" class="preview-container">
            <div class="preview-wrapper">
              <video
                v-if="isVideo"
                :src="previewUrl"
                controls
                class="preview-content"
                @loadedmetadata="handleVideoReady"/>
              <img
                v-else
                :src="previewUrl"
                class="preview-content"
                @load="handleImageReady"/>
            </div>
            <p v-if="!isVideo">总共检测到{{ result.total_people }}个同学，其中：{{ result.blow_head_count }}个低头,{{ result.raise_head_count }}个抬头，{{ result.other_objects }}个转头</p>
          </div>
          <div v-else class="empty-result">
            <el-empty description="等待上传检测文件"></el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </d2-container>
</template>

<script>
import uploadApi from '@/api/upload'
export default {

  data () {
    return {
      loadingInstance: null,
      previewUrl: '',
      isVideo: false,
      loadError: false,
      result: []
    }
  },
  methods: {
    async customUpload (file) {
      try {
        const response = await uploadApi.uploadFile(file)
        this.handleSuccess(response.data)
      } catch (error) {
        console.error('上传失败:', error)
        this.$message.error('上传失败，请重试')
        if (this.loadingInstance) {
          this.loadingInstance.close()
        }
      }
    },
    beforeUpload (file) {
      this.loadingInstance = this.$loading({
        lock: true,
        text: '文件处理中，请稍候...',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      const isAllowed = ['image/jpeg', 'image/png', 'video/mp4'].includes(file.type)
      if (!isAllowed) {
        this.$message.error('不支持的文件格式!')
        return false
      }
      return true
    },
    handleSuccess (res) {
      // 构建完整文件URL
      if (this.loadingInstance) {
        this.loadingInstance.close()
      }
      const baseURL = process.env.VUE_APP_API || window.location.origin
      this.previewUrl = `${baseURL}/${res.result_path}`
      this.isVideo = res.file_type === 'video/mp4'
      this.result = res.stats
      // 处理加载错误
      console.log(this.previewUrl)
      this.loadError = false
    },
    handleImageReady () {
      console.log('图片加载完成')
    },
    handleVideoReady () {
      console.log('视频元数据加载完成')
    }
  },
  mounted () {
    document.addEventListener('error', (e) => {
      if (this.loadingInstance) {
        this.loadingInstance.close()
      }
      if (e.target.tagName === 'IMG' || e.target.tagName === 'VIDEO') {
        if (e.target.src === this.previewUrl) {
          this.loadError = true
          e.target.setAttribute('data-error', 'true')
          this.$message.error('文件加载失败，请检查网络连接')
        }
      }
    }, true)
  }
}
</script>

<style lang="scss" scoped>
.preview-content[data-error] {
  border: 2px solid #F56C6C;
  padding: 10px;
}
.layout-container {
  height: calc(100vh - 90px);
}

.main-row {
  height: 90%;

  .left-panel, .right-panel {
    height: 90%;
    display: flex;
    flex-direction: column;
  }
}

.upload-card, .result-card {
  flex: 1;
  display: flex;
  flex-direction: column;

  ::v-deep .el-card__body {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
}

.uploader {
  flex: 1;

  ::v-deep .el-upload {
    width: 100%;
    height: 100%;

    .el-upload-dragger {
      width: 100%;
      height: 100%;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      border: 2px dashed #409EFF;
      background-color: #f8faff;

      &:hover {
        border-color: #66b1ff;
      }
    }
  }
}

.preview-container {
  margin-top: 20px;
  flex-shrink: 0;

  .preview-wrapper {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 10px;

    .preview-content {
      max-width: 100%;
      max-height: 300px;
      display: block;
      margin: 0 auto;
      border-radius: 4px;
    }
  }
}

.result-content {
  flex: 1;
  display: flex;
  flex-direction: column;

  .result-table {
    flex: 1;

    .coord-box {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      div {
        display: flex;
        align-items: center;
        background: #f5f7fa;
        padding: 4px 8px;
        border-radius: 4px;

        .coord-label {
          color: #909399;
          margin-right: 4px;
        }

        .coord-value {
          color: #606266;
          font-weight: 500;
        }
      }
    }
  }

  .statistics {
    margin-top: 10px;
    text-align: right;
    padding: 10px 0;
    border-top: 1px solid #ebeef5;
  }
}

.empty-result {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-header {
  display: flex;
  align-items: center;

  i {
    margin-right: 8px;
    font-size: 18px;
  }

  span {
    font-size: 16px;
    font-weight: 500;
  }
}
</style>
