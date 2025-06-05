<template>
  <d2-container>
    <template slot="header">
      <el-button
        type="primary"
        icon="el-icon-back"
        @click="goBack">
        返回
      </el-button>
      <el-upload
        v-if="!chartData.rows.length"
        class="upload-btn"
        action="/api/upload-video"
        :show-file-list="false"
        :data="{ course_id: courseId }"
        :before-upload="beforeVideoUpload"
        :on-success="handleVideoSuccess"
        :on-error="handleVideoError">
        <el-button
          type="primary"
          icon="el-icon-upload"
          style="margin-left: 10px;">
          上传课堂视频
        </el-button>
      </el-upload>
      <el-button
        v-if="videoPath"
        type="primary"
        @click="handleDownload"
        style="margin-left: 10px;"
        icon="el-icon-upload">
        下载课堂视频
      </el-button>
    </template>
    <!-- 课程基础信息 -->
    <div v-if="courseInfo" class="course-header">
      <div class="header-top">
        <h2>{{ courseInfo.name }}</h2>
        <el-button
          type="primary"
          icon="el-icon-refresh"
          circle
          @click="refreshData"
          :loading="refreshing">
        </el-button>
      </div>
      <p>教师：{{ courseInfo.teacher }} | 地点：{{ courseInfo.location }} | 教学班: {{ courseInfo.class_name }} | 开始时间：{{ formatDate(courseInfo.start_time) }} | 结束时间：{{ formatDate(courseInfo.end_time) }} | 教学周：第{{ courseInfo.week_num }}周 | {{ formatWeekday(courseInfo.weekday) }} | 日期：{{ calculateDate(courseInfo.week_num, courseInfo.weekday) }}</p>
      <div v-if="chartData.rows.length">
        <p>
          应到人数：{{ courseInfo.class_size || 0 }} |
          实到人数：{{ (chartData.rows[chartData.rows.length - 1].lookup_count || 0) + (chartData.rows[chartData.rows.length - 1].other_count || 0) }} |
          平均抬头率：{{ averageLookupCount }}%
        </p>
      </div>
    </div>

    <!-- 图表展示区域 -->
    <div class="chart-wrapper">
      <!-- 空状态提示 -->
      <div v-if="!chartData.rows.length" class="empty-state">
        <el-empty description="暂无检测数据"></el-empty>
      </div>

      <!-- 双图表容器 -->
      <div v-else class="chart-group">
        <!-- 折线图 - 时间趋势分析 -->
        <ve-line
          :data="chartData"
          :settings="lineSettings"
          :extend="chartExtend"
          height="400px"
          :loading="loading"
          class="chart-item"
        ></ve-line>
        <ve-pie
          :data="pieData"
          :settings="pieSettings"
          height="400px"
          class="chart-item"
        ></ve-pie>
      </div>
    </div>
    <div class="analysis-section">
      <el-button v-if="courseInfo && !courseInfo.suggestion && chartData.rows.length"
        type="primary"
        @click="analyzeData"
        :loading="analyzeLoading"
        class="analyze-btn">
        <i class="el-icon-search"></i>
        生成课程分析报告
      </el-button>
      <el-alert
        v-if="analyzeLoading && courseInfo && !courseInfo.suggestion"
        title="AI正在生成分析报告，请稍候..."
        type="info"
        :closable="false"
        show-icon
        class="generating-alert">
      </el-alert>
      <!-- 分析结果展示 -->
      <div v-if="courseInfo && courseInfo.suggestion" class="analysis-result">
        <el-card class="box-card">
          <div slot="header" class="clearfix">
            <span class="report-title">AI分析报告</span>
          </div>
          <div class="result-content">
            {{ courseInfo.suggestion }}
          </div>
        </el-card>
      </div>
    </div>
  </d2-container>
</template>

<script>
import moment from 'moment'
import courseApi from '@/api/course'
import aigcApi from '@/api/aigc'

export default {
  name: 'CourseDetection',
  data () {
    return {
      videoPath: '',
      startDateStr: '',
      refreshing: false,
      analyzeLoading: false,
      analysisResult: '',
      eventSource: null,
      loading: true,
      courseInfo: null,
      chartData: {
        columns: ['timestamp', 'lookup_count', 'other_count'],
        rows: [],
        empty: {
          text: '暂无数据',
          subtext: '等待数据加载中...'
        }
      },
      // 折线图特殊配置
      lineSettings: {
        labelMap: {
          lookup_count: '抬头次数',
          other_count: '其他状态'
        },
        area: true
      },
      // 热力图配置
      pieData: {
        columns: ['status', 'average'],
        rows: []
      },
      pieSettings: {
        radius: 100,
        label: {
          formatter: '{b}：{d}%'
        }
      },
      // 通用图表扩展配置
      chartExtend: {
        title: {
          text: '课堂专注度分析',
          left: 'center',
          top: 'bottom',
          textStyle: {
            color: '#333',
            fontSize: 18
          }
        },
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            if (!params || !params.length) return '无数据'
            return params.map(item => {
              // 从折线图的数据中提取数值（如果是数组格式）
              const value = Array.isArray(item.data) ? item.data[1] : item.data
              return `${item.marker} ${item.seriesName}: ${value}次`
            }).join('<br/>')
          }
        },
        xAxis: {
          type: 'time',
          axisLabel: {
            formatter: value => moment(value).format('MM/DD HH:mm')
          }
        },
        yAxis: {
          axisLabel: {
            formatter: '{value} 次'
          }
        },
        grid: {
          containLabel: true
        }
      }
    }
  },
  created () {
    this.loadData()
  },
  computed: {
    courseId () {
      return this.$route.params.id
    },
    averageData () {
      if (!this.chartData.rows.length) {
        return { lookup: 0, other: 0 }
      }
      const total = this.chartData.rows.reduce((acc, cur) => {
        return {
          lookup: acc.lookup + cur.lookup_count,
          other: acc.other + cur.other_count
        }
      }, { lookup: 0, other: 0 })

      return {
        lookup: total.lookup / this.chartData.rows.length,
        other: total.other / this.chartData.rows.length
      }
    },
    averageLookupCount () {
      if (!this.chartData.rows.length) return 0
      const sum = this.chartData.rows.reduce((acc, row) => {
        return acc + row.lookup_count + row.other_count
      }, 0)
      const lookupSum = this.chartData.rows.reduce((acc, row) => {
        return acc + row.lookup_count
      }, 0)
      return ((lookupSum / sum) * 100).toFixed(2)
    },
    formattedResult () {
      return this.analysisResult.replace(/\n/g, '<br/>')
    }
  },
  methods: {
    handleDownload () {
      // 创建隐藏的a标签触发下载
      const link = document.createElement('a')
      link.href = process.env.VUE_APP_API + this.videoPath
      link.download = this.videoPath.split('/').pop() // 自动获取文件名
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    calculateDate (weekNum, targetWeekday) {
      // 解析开学日期
      const startDate = new Date(this.startDateStr)
      // 计算开学日期所在周的周一（JS中getDay()周日=0，周一=1）
      const dayOffset = startDate.getDay() === 0 ? 6 : startDate.getDay() - 1 // 转为周一基准
      const startMonday = new Date(startDate)
      startMonday.setDate(startDate.getDate() - dayOffset)
      // 计算目标周的周一
      const targetMonday = new Date(startMonday)
      targetMonday.setDate(startMonday.getDate() + (weekNum - 1) * 7)
      // 调整至目标星期（targetWeekday为1=周一，7=周日）
      const targetDate = new Date(targetMonday)
      targetDate.setDate(targetMonday.getDate() + targetWeekday - 1)
      return targetDate.toISOString().split('T')[0] // 返回YYYY-MM-DD
    },
    formatWeekday (weekday) {
      const weekdayMap = {
        1: '星期一',
        2: '星期二',
        3: '星期三',
        4: '星期四',
        5: '星期五',
        6: '星期六',
        7: '星期日'
      }
      return weekdayMap[weekday] || ''
    },
    formatDate (date) {
      const dt = new Date(date)
      const hours = dt.getHours().toString().padStart(2, '0')
      const minutes = dt.getMinutes().toString().padStart(2, '0')
      return `${hours}:${minutes}`
    },
    goBack () {
      this.$router.go(-1) // 返回上一页
    },
    async analyzeData () {
      if (this.analyzeLoading) return

      try {
        this.analyzeLoading = true
        this.analysisResult = ''

        // 构建请求数据
        const response = await aigcApi.generalCourseRecoment(this.chartData)
        await courseApi.UpdateSuggestCourse(this.courseInfo.id, response.content)
        this.refreshData()
      } catch (error) {
        this.handleError(error)
      } finally {
        this.analyzeLoading = false
      }
    },
    handleError (error) {
      const defaultMsg = '分析失败，请稍后重试'
      console.error('分析失败:', error)
      if (error.response) {
        const apiError = error.response?.detail || defaultMsg
        this.analysisResult = `错误代码 ${error.response.status}: ${apiError}`
      } else {
        this.analysisResult = defaultMsg
      }
    },
    beforeDestroy () {
      // 组件销毁时关闭连接
      if (this.eventSource) {
        this.eventSource.close()
      }
    },
    beforeVideoUpload (file) {
      const isMP4 = file.type === 'video/mp4'
      if (!isMP4) {
        this.$message.error('仅支持MP4格式视频')
        return false
      }
      this.$message.info('视频上传处理中，请稍候...')
      return true
    },

    handleVideoSuccess (response) {
      this.$message.success('视频处理完成')
      this.refreshData() // 自动刷新数据
    },

    handleVideoError (err) {
      console.error('视频上传失败:', err)
      const msg = err.message || '视频处理失败，请检查文件格式'
      this.$message.error(msg)
    },
    async loadData () {
      try {
        this.loading = true
        const courseId = this.$route.params.id
        const [detailRes, detectionRes, semesterRes, videoPath] = await Promise.all([
          courseApi.getCourseDetail(courseId),
          courseApi.getDetectionData(courseId),
          courseApi.getSemesterConfig(),
          courseApi.getVideoPath(courseId) || ''
        ])
        this.videoPath = videoPath || ''
        this.courseInfo = detailRes
        this.startDateStr = semesterRes.start_date
        console.log('课程详情:', this.courseInfo)
        // 添加更严格的数据验证
        if (Array.isArray(detectionRes)) {
          this.processChartData(detectionRes)
        } else {
          console.error('检测数据格式不正确:', detectionRes)
          this.chartData.rows = []
        }
      } catch (error) {
        console.error('数据加载失败:', error)
        this.$message.error('数据加载失败，请稍后重试')
      } finally {
        // 确保 loading 状态正确更新
        this.$nextTick(() => {
          this.loading = false
        })
      }
    },
    processChartData (rawData) {
      if (!rawData || !Array.isArray(rawData)) {
        this.chartData.rows = []
        return
      }

      // 转换数据格式以适应 ve-charts
      this.chartData.rows = rawData.map(item => ({
        timestamp: new Date(item.timestamp), // 转换为日期对象
        lookup_count: item.lookup_count || 0,
        other_count: item.other_count || 0
      }))

      // 确保时间戳排序正确（从早到晚）
      this.chartData.rows.sort((a, b) =>
        a.timestamp - b.timestamp
      )
    },
    async refreshData () {
      this.refreshing = true
      try {
        await this.loadData() // 调用已有的加载数据方法
        this.$message.success('数据刷新成功')
      } catch (error) {
        console.error('刷新数据失败:', error)
        this.$message.error('刷新数据失败，请稍后重试')
      } finally {
        this.refreshing = false
      }
    }
  },
  watch: {
    averageData: {
      handler (newVal) {
        this.pieData.rows = [
          {
            status: '平均抬头人数',
            average: Number(newVal.lookup.toFixed(2))
          },
          {
            status: '平均其他状态人数',
            average: Number(newVal.other.toFixed(2))
          }
        ]
      },
      immediate: true,
      deep: true
    }
  }
}
</script>

<style scoped>
.analyze-btn {
  width: 100%;
  margin: 20px 0;
}

.analysis-result {
  margin-top: 20px;
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.report-title {
  font-size: 18px;
  font-weight: bold;
}

.usage-tag {
  float: right;
}

.result-content {
  line-height: 1.8;
  white-space: pre-wrap;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.button-container {
  text-align: right;
}
.box-card {
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
.analysis-section {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.analyze-btn {
  width: 100%;
  margin-bottom: 20px;
}

.analysis-result {
  margin-top: 15px;
}

.result-content {
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
}

.course-detection-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.course-header .header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.course-header h2 {
  margin: 0;
}

.chart-wrapper {
  position: relative;
  min-height: 400px;
}

.chart-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 30px;
}

.chart-item {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,.1);
}
.upload-btn {
  display: inline-block;
  margin-left: 10px;
}
.empty-state {
  padding: 50px 0;
  text-align: center;
  background: #fff;
  border-radius: 8px;
}
</style>
