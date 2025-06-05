<template>
  <d2-container>
    <template slot="header">
      <el-row class="toolbar">
        <span style="margin-right: 15px">{{ academicYear }}学年第{{ semesterTerm }}学期</span>
        <span style="margin-right: 15px">{{ formattedSemesterWeek }}</span>
        <el-select
          v-model="selectedWeek"
          placeholder="选择学期周"
          @change="handleWeekChange"
          style="width: 200px; margin-right: 15px"
        >
          <el-option
            v-for="week in semesterWeeks"
            :key="week.value"
            :label="`第 ${week.value} 周`"
            :value="week.date"
          />
        </el-select>
        <el-select
          v-model="selectedLocation"
          placeholder="选择地点"
          clearable
          style="width: 180px; margin-left: 15px"
          @change="handleFilterChange"
        >
          <el-option
            v-for="loc in locationOptions"
            :key="loc"
            :label="loc"
            :value="loc"
          />
        </el-select>

        <el-select
          v-model="selectedClass"
          placeholder="选择班级"
          clearable
          style="width: 180px; margin-left: 15px"
          @change="handleFilterChange"
        >
          <el-option
            v-for="cls in classOptions"
            :key="cls"
            :label="cls"
            :value="cls"
          />
        </el-select>
        <el-button-group class="ml-10">
          <el-button @click="shiftWeek(-1)">
            <d2-icon name="arrow-left" /> 上一周
          </el-button>
          <el-button @click="shiftWeek(1)">
            下一周 <d2-icon name="arrow-right" />
          </el-button>
          <el-upload
            action="/api/upload"
            :http-request="handleFakeUpload"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleUpload"
            accept=".xlsx, .xls"
          >
            <el-button type="primary" icon="el-icon-upload">导入课表</el-button>
          </el-upload>
        </el-button-group>
      </el-row>
    </template>

    <el-table :data="processedData" v-loading="loading" style="width: 100%">
      <el-table-column label="时间/日期" width="180">
        <template v-slot="{ row }">
          <div class="time-slot">
            {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
          </div>
        </template>
      </el-table-column>

      <!-- 动态生成7天列 -->
      <el-table-column
        v-for="day in 7"
        :key="day"
        :label="getWeekdayLabel(day)"
      >
        <template v-slot="{ $index }">
          <div
            v-for="course in getDayCourses(day, $index)"
            :key="course.id"
            class="course-card"
            @click.stop="handleCourseClick(course)"
          >
            <h4>{{ course.name }}</h4>
            <div class="course-meta">
              <el-tag size="mini">{{ course.teacher }}</el-tag>
              <el-tag size="mini" type="info">{{ course.location }}</el-tag>
              <el-tag size="mini" type="success">{{ course.class_name }}</el-tag>
            </div>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-alert v-if="importResult" :title="importResult.title" :type="importResult.type" :closable="false" class="mb-20">
      <div v-if="importResult.errors.length">
        <p>失败记录（共 {{ importResult.errors.length }} 条）：</p>
        <ul>
          <li v-for="(error, index) in importResult.errors" :key="index">
            第 {{ error.row }} 行：{{ error.message }}
          </li>
        </ul>
      </div>
    </el-alert>
  </d2-container>
</template>

<script>
import { mapState } from 'vuex'
import dayjs from 'dayjs'
import courseApi from '@/api/course'
import weekOfYear from 'dayjs/plugin/weekOfYear'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import * as XLSX from 'xlsx/xlsx.mjs'
import isoWeek from 'dayjs/plugin/isoWeek'
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter'

dayjs.extend(weekOfYear)
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(isoWeek)
dayjs.extend(isSameOrAfter)

export default {
  name: 'Course',
  data () {
    return {
      academicYear: '', // 新增：学期年份
      semesterTerm: '', // 新增：学期（1或2）
      selectedLocation: '',
      selectedClass: '',
      locationOptions: [],
      classOptions: [],
      semesterStart: '2025-03-03', // 学期开始日期
      semesterWeeks: [], // 生成的学期周数列表
      selectedWeek: '', // 当前选中周
      totalWeeks: 0,
      importResult: null,
      weekdayMap: {
        monday: { value: 1, label: '星期一' },
        tuesday: { value: 2, label: '星期二' },
        wednesday: { value: 3, label: '星期三' },
        thursday: { value: 4, label: '星期四' },
        friday: { value: 5, label: '星期五' },
        saturday: { value: 6, label: '星期六' },
        sunday: { value: 7, label: '星期日' }
      },
      loading: false,
      currentWeek: dayjs().format('YYYY-MM-DD'),
      weekOptions: {
        firstDayOfWeek: 1,
        disabledDate: (date) => date > dayjs().add(3, 'month')
      }
    }
  },
  computed: {
    ...mapState('d2admin/course', {
      rawCourses: state => state.courses || []
    }),
    processedData () {
      return this.generateTimeSlots().map(timeSlot => ({
        ...timeSlot,
        // 为每个时间段添加过滤后的课程数据
        filteredCourses: this.getFilteredCourses(timeSlot)
      }))
    },
    formattedSemesterWeek () {
      const weekNum = this.calculateSemesterWeek(this.currentWeek)
      return weekNum > 22 ? '假期' : `第 ${weekNum} 周`
    }
  },
  methods: {
    handleFilterChange () {
      // 这里可以留空，因为计算属性会自动响应变化
      // 如果需要进行其他操作（比如日志记录）可以在此添加
    },
    getFilteredCourses (timeSlot) {
      return this.rawCourses.filter(course => {
        // 时间槽匹配
        const isTimeMatch = course.timeSlot === timeSlot.time_slot
        // 地点过滤
        const isLocationMatch = this.selectedLocation
          ? course.location === this.selectedLocation
          : true

        // 班级过滤（假设班级信息存储在class_name字段）
        const isClassMatch = this.selectedClass
          ? course.class_name === this.selectedClass
          : true

        return isTimeMatch && isLocationMatch && isClassMatch
      })
    },
    initFilterOptions () {
      // 获取所有唯一地点
      this.locationOptions = [...new Set(
        this.rawCourses.map(c => c.location).filter(Boolean)
      )].sort()

      // 获取所有唯一班级
      this.classOptions = [...new Set(
        this.rawCourses.map(c => c.class_name).filter(Boolean)
      )].sort()
    },
    generateSemesterWeeks () {
      // 学期开始日期的周一（重要基准）
      const semesterStartMonday = dayjs(this.semesterStart)
        .startOf('isoWeek')
        .tz('Asia/Shanghai')

      // 按周递增生成周列表
      this.semesterWeeks = Array.from({ length: this.totalWeeks }, (_, i) => ({
        value: i + 1,
        date: semesterStartMonday.add(i, 'week').format('YYYY-MM-DD')
      }))
    },
    calculateSemesterWeek (targetDate) {
      const semesterStartMonday = dayjs(this.semesterStart)
        .startOf('week')
        .add(1, 'day')
        .tz('Asia/Shanghai')

      const currentMonday = dayjs(targetDate)
        .startOf('week')
        .add(1, 'day')
        .tz('Asia/Shanghai')

      return currentMonday.diff(semesterStartMonday, 'week') + 1
    },
    async loadCourses () {
      this.loading = true
      try {
        const semesterWeek = this.calculateSemesterWeek(this.currentWeek)
        const startDate = dayjs(this.currentWeek).startOf('isoWeek').format('YYYY-MM-DD')
        const res = await courseApi.getWeeklyCourses(semesterWeek, startDate)
        // 数据校验层
        const rawCourses = res?.courses || []
        if (!Array.isArray(rawCourses)) {
          throw new Error('接口返回数据格式异常')
        }

        // 安全处理层
        const processed = rawCourses.map(c => ({
          ...c,
          start_time: this.safeConvertTime(c.start_time),
          end_time: this.safeConvertTime(c.end_time),
          timeSlot: this.calculateTimeSlot(c.start_time),
          class_name: c.class_name || '',
          class_size: c.class_size || 0
        }))
        // 提交数据
        this.$store.commit('d2admin/course/SET_COURSES', processed)
        console.log('加载数据时course', this.rawCourses)
      } catch (error) {
        this.handleLoadError(error)
      } finally {
        this.loading = false
      }
    },
    handleLoadError (error) {
      const status = error.response?.status
      const messageMap = {
        400: '请求参数错误',
        404: '未找到相关课程',
        500: '服务器内部错误'
      }
      this.$notify.error({
        title: `数据加载失败 (${status || '未知错误'})`,
        message: messageMap[status] || error.message
      })
    },
    // 安全时间转换
    safeConvertTime (time) {
      try {
        return dayjs.utc(time).tz('Asia/Shanghai').format()
      } catch {
        console.error('时间格式异常:', time)
        return dayjs().format() // 返回当前时间兜底
      }
    },
    // 新增时间槽计算逻辑
    calculateTimeSlot (start_time) {
      const hour = dayjs(start_time).hour()
      if (hour === 8) return 1
      if (hour === 9) return 2
      if (hour === 10) return 3
      if (hour === 11) return 4
      if (hour === 14) return 5
      if (hour === 15) return 6
      if (hour === 16) return 7
      if (hour === 17) return 8

      if (hour === 19) return 9
      if (hour === 20) return 10
    },

    // 重构后的时间段生成方法
    generateTimeSlots () {
      const timeSlots = [
        { start: '8:00', end: '9:00', label: '第1节' },
        { start: '9:00', end: '10:00', label: '第2节' },
        { start: '10:00', end: '11:00', label: '第3节' },
        { start: '11:00', end: '12:00', label: '第4节' },
        { start: '14:00', end: '15:00', label: '第5节' },
        { start: '15:00', end: '16:00', label: '第6节' },
        { start: '16:00', end: '17:00', label: '第7节' },
        { start: '17:00', end: '18:00', label: '第8节' },
        { start: '19:00', end: '20:00', label: '第9节(晚)' },
        { start: '20:00', end: '21:00', label: '第5节(晚)' }
      ]

      return timeSlots.map((slot, i) => ({
        time_slot: i + 1,
        start_time: `1970-01-01T${slot.start}:00`, // 保持ISO格式
        end_time: `1970-01-01T${slot.end}:00`,
        label: slot.label // 添加可读性标签
      }))
    },
    handleRowClick (row) {
      // 处理行点击事件的逻辑
      console.log('Row clicked:', row)
    },
    getWeekdayLabel (dayNumber) {
      const weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
      // 计算当前周的对应日期
      const currentDate = dayjs(this.currentWeek)
        .startOf('isoWeek') // 获取当前周的周一
        .add(dayNumber - 1, 'day') // 加上对应的天数
        .format('MM-DD') // 格式化为月-日

      return `${weekdays[dayNumber - 1]}(${currentDate})` || '未知'
    },

    // 获取当天课程
    getDayCourses (day, timeSlotIndex) {
      const currentTimeSlot = this.processedData[timeSlotIndex]
      return currentTimeSlot.filteredCourses.filter(
        course => course.weekday === day
      )
    },

    // 处理课程点击
    handleCourseClick (course) {
      this.$router.push({
        name: 'CourseDetail',
        params: { id: course.id },
        query: { week: this.currentWeek }
      })
    },

    // 时间格式化
    formatTime (datetime) {
    // 兼容两种格式：完整时间戳和纯时间字符串
      const timeObj = dayjs(datetime.includes('T') ? datetime : `1970-01-01T${datetime}`)
      return timeObj.isValid() ? timeObj.format('HH:mm') : '--:--'
    },

    // 周数切换
    shiftWeek (offset) {
      // 保持当前周切换但基于学期计算
      this.currentWeek = dayjs(this.currentWeek)
        .add(offset, 'week')
        .format('YYYY-MM-DD')
      // 添加学期周范围限制（示例限制1-20周）
      const currentSemesterWeek = this.calculateSemesterWeek(this.currentWeek)
      if (currentSemesterWeek < 1 || currentSemesterWeek > 20) {
        this.$message.warning('超出学期周范围')
        return
      }
      this.loadCourses()
    },
    handleFakeUpload () {
    // 空实现用于规避 Element 校验
      return Promise.resolve()
    },
    // 文件选择回调
    async handleUpload (file) {
      try {
        if (!XLSX?.read) throw new Error('Excel 解析库未加载')

        // 使用 XLSX 原生方法解析
        const reader = new FileReader()
        const workbook = await new Promise((resolve, reject) => {
          reader.onload = (e) => {
            try {
              const data = new Uint8Array(e.target.result)
              resolve(XLSX.read(data, { type: 'array' }))
            } catch (e) {
              reject(e)
            }
          }
          reader.onerror = reject
          reader.readAsArrayBuffer(file.raw) // 注意 Element Upload 的文件结构
        })

        const sheetName = workbook.SheetNames[0]
        const sheet = workbook.Sheets[sheetName]
        const results = XLSX.utils.sheet_to_json(sheet)
        // 空数据校验
        if (!results.length) throw new Error('Excel 文件无有效数据')

        // 使用优化后的日期解析方法
        const { validData, errors } = this.transformData(results)
        console.log('validData:', validData)
        console.log('errors:', errors)
        if (errors.length > 0) {
          this.$notify.error({
            title: '部分数据导入失败',
            message: errors.message
          })
        }
        if (validData.length === 0) {
          throw new Error('没有有效数据可导入')
        }
        // 提交数据
        const res = await courseApi.batchCreateCourses(validData)
        const responseData = res || {}
        const {
          success_count = 0,
          failed_count = 0,
          failed_items = []
        } = responseData
        // 处理导入结果
        this.importResult = {
          type: failed_count > 0 ? 'warning' : 'success',
          title: `导入完成（成功 ${success_count} 条，失败 ${failed_count} 条）`,
          errors: failed_items.map(item => ({
            row: (item?.row ?? 0),
            message: item?.message || '未知错误'
          }))
        }

        this.$emit('import-success', res)
        this.loadCourses()
      } catch (error) {
        this.$notify.error({
          title: '导入失败',
          message: error.message
        })
      }
      return false // 阻止默认上传
    },
    // 表头验证
    validateHeader (header) {
      const requiredHeaders = ['课程名称', '教师', '地点', '开始时间', '结束时间', '周数', '星期', '教学班', '人数']
      const missing = requiredHeaders.filter(h => !header.includes(h))
      if (missing.length > 0) {
        throw new Error(`缺少必要表头：${missing.join(', ')}`)
      }
    },

    // 数据转换
    transformData (rawData) {
      const errors = []
      const validData = []
      if (!XLSX || !XLSX.SSF) {
        throw new Error('xlsx 模块未正确加载')
      }
      rawData.forEach((row, index) => {
        try {
          // 数据校验
          const requiredFields = ['课程名称', '教师', '地点', '开始时间', '结束时间', '周数', '星期', '教学班', '人数']
          requiredFields.forEach(field => {
            if (!row[field]) throw new Error(`[${field}] 不能为空`)
          })

          // 时间格式处理（兼容Excel数字日期和字符串）
          const parseExcelDate = (timeValue, weekNum, weekday) => {
            console.log('timeValue:', this.semesterStart)
            // 获取学期第N周的周一
            const semesterStartMonday = dayjs(this.semesterStart)
              .startOf('isoWeek')
              .tz('Asia/Shanghai')

            // 计算目标周周一
            const targetMonday = semesterStartMonday.add((weekNum - 1) * 7, 'day')

            // 计算具体日期（周一=1，周二=2...）
            const courseDate = targetMonday.add(weekday - 1, 'day')

            // 解析时间部分（仅处理时分）
            let hours = 0
            let minutes = 0
            if (typeof timeValue === 'number') {
              // 仅取小数部分（忽略日期信息）
              const timeFraction = timeValue % 1
              const totalMinutes = Math.round(timeFraction * 1440)
              hours = Math.floor(totalMinutes / 60)
              minutes = totalMinutes % 60
            } else if (typeof timeValue === 'string') {
              const [h, m] = timeValue.split(':')
              hours = parseInt(h, 10) || 0
              minutes = parseInt(m, 10) || 0
            }

            // 生成完整北京时间
            return courseDate
              .hour(hours)
              .minute(minutes)
              .tz('Asia/Shanghai')
              .format('YYYY-MM-DDTHH:mm:ss+08:00')
          }

          // 周数验证
          const weekNum = Number(row['周数'])
          if (isNaN(weekNum)) throw new Error('周数必须为数字')

          const classSize = Number(row['人数'])
          if (isNaN(classSize)) throw new Error('班级人数必须为数字')
          // 星期验证
          const weekdayEntry = Object.values(this.weekdayMap).find(
            item => item.label === row['星期']
          )
          const weekday = weekdayEntry?.value
          if (!weekday) throw new Error('星期格式错误')

          // 解析时间
          const start = parseExcelDate(row['开始时间'], weekNum, weekday)
          const end = parseExcelDate(row['结束时间'], weekNum, weekday)

          // 空值校验
          if (!start || !end) throw new Error('时间格式错误')

          // 时间逻辑校验
          if (dayjs(start).isAfter(dayjs(end))) {
            throw new Error('开始时间不能晚于结束时间')
          }
          validData.push({
            name: row['课程名称'],
            teacher: row['教师'],
            location: row['地点'],
            start_time: start,
            end_time: end,
            week_num: weekNum,
            weekday: weekday,
            class_size: classSize,
            class_name: row['教学班']
          })
        } catch (error) {
          errors.push({
            row: index + 2, // 增加表头偏移
            message: error.message.replace('start_time', '开始时间').replace('end_time', '结束时间'),
            data: JSON.stringify(row)
          })
        }
      })

      return { validData, errors }
    },
    handleWeekChange (date) {
      this.currentWeek = date
      this.loadCourses()
    }
  },
  async mounted () {
    this.generateSemesterWeeks()
    // 默认选中当前周
    const now = dayjs().startOf('day') // 精确到天
    const currentWeek = this.semesterWeeks.find(w =>
      now.isSameOrAfter(w.date, 'day') &&
      now.isBefore(dayjs(w.date).add(1, 'week'), 'day')
    )
    if (currentWeek) {
      this.selectedWeek = currentWeek.date
      this.currentWeek = currentWeek.date // 同步 currentWeek
    }
    const res = await courseApi.getSemesterConfig()
    this.semesterStart = res.start_date
    this.totalWeeks = res.total_weeks
    const startDate = dayjs(this.semesterStart)
    const startYear = startDate.year()
    const startMonth = startDate.month() + 1 // 1-12
    // 判断学年（假设9月为新学年开始）
    if (startMonth >= 8) {
      this.academicYear = `${startYear}-${startYear + 1}`
      this.semesterTerm = 1 // 9月开始的为第一学期
    } else {
      this.academicYear = `${startYear - 1}-${startYear}`
      this.semesterTerm = startMonth >= 2 ? 2 : 1 // 3-8月为第二学期
    }
    this.generateSemesterWeeks()
    this.loadCourses()
  },
  watch: {
    rawCourses: {
      immediate: true,
      handler () {
        this.initFilterOptions()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
:root {
  --color-error: #f56c6c;
  --color-text-primary: #2c3e50;
  --color-text-regular: #606266;
  --color-text-secondary: #909399;
  --background-base: #f8f9fa;
}

.mb-20 {
  margin-bottom: 20px;
}

::v-deep(.el-upload) {
  display: inline-block;
}

.error-list {
  margin-top: 10px;
  padding-left: 20px;

  li {
    line-height: 1.8;
    color: var(--color-error);
  }
}

.course-card {
  padding: 10px;
  margin: 5px;
  background: var(--background-base);
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;

  &:hover {
    transform: translateX(3px);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }

  h4 {
    margin: 0 0 5px 0;
    color: var(--color-text-primary);
  }
}

.time-slot {
  font-weight: bold;
  color: var(--color-text-regular);
}

.week-info {
  font-size: 0.8em;
  color: var(--color-text-secondary);
}
/* 在 style 部分添加 */
::v-deep .el-upload {
  display: inline-block !important;  /* 强制行内显示 */
  margin-left: 10px;                /* 保持与其他按钮的间距一致 */
}

.el-button-group {
  display: inline-flex;
  align-items: center;
  gap: 10px;  /* 统一按钮间距 */
}
</style>
