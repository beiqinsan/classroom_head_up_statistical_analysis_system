<!-- src/views/course/List.vue -->
<template>
    <d2-container>
      <template slot="header">
        <el-button type="primary" @click="handleCreate">新增课程</el-button>
        <el-input
          v-model="searchQuery.keyword"
          placeholder="搜索课程"
          style="width: 300px; margin-right: 15px"
          @keyup.enter.native="fetchData"
          clearable
          @clear="handleSearchClear"
        ></el-input>
        <el-select
          v-model="searchQuery.location"
          placeholder="全部地点"
          clearable
          style="width: 150px; margin-right: 15px"
          @change="fetchData"
        >
          <el-option
            v-for="loc in locationOptions"
            :key="loc"
            :label="loc"
            :value="loc"
          ></el-option>
        </el-select>
        <el-select
          v-model="searchQuery.weekday"
          placeholder="全部星期"
          clearable
          style="width: 150px; margin-right: 15px"
          @change="fetchData"
        >
          <el-option
            v-for="day in 7"
            :key="day"
            :label="'周' + ['日','一','二','三','四','五','六'][day-1]"
            :value="day"
          ></el-option>
        </el-select>
        <el-button type="primary" @click="fetchData">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </template>
      <el-table :data="list.data" v-loading="loading">
        <el-table-column prop="name" label="课程名称"></el-table-column>
        <el-table-column prop="teacher" label="教师"></el-table-column>
        <el-table-column prop="location" label="地点"></el-table-column>
        <el-table-column prop="class_name" label="班级"></el-table-column>
        <el-table-column prop="class_size" label="应到人数"></el-table-column>
        <el-table-column label="分析报告" width="120">
          <template v-slot="{row}">
            <el-button
              v-if="row.suggestion"
              type="text"
              @click="showSuggestion(row)"
            >查看报告</el-button>
            <span v-else style="color: #909399">无报告</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="220">
          <template v-slot="{row}">
            {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template v-slot="{row}">
            <el-button size="mini" @click="handleEdit(row)">编辑</el-button>
            <el-button size="mini" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <!-- 编辑弹窗 -->
      <el-dialog :title="dialogTitle" :visible.sync="dialogVisible">
        <el-form :model="form" :rules="rules" ref="form">
          <el-form-item label="课程名称" prop="name">
            <el-input v-model="form.name"></el-input>
          </el-form-item>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="开始时间" prop="start_time">
                <el-date-picker
                  v-model="form.start_time"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  placeholder="选择日期时间">
                </el-date-picker>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="结束时间" prop="end_time">
                <el-date-picker
                  v-model="form.end_time"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  placeholder="选择日期时间">
                </el-date-picker>
              </el-form-item>
            </el-col>
          </el-row>
            <el-form-item label="授课教师" prop="teacher">
              <el-input v-model="form.teacher" placeholder="请输入教师姓名"></el-input>
            </el-form-item>

            <el-form-item label="上课地点" prop="location">
              <el-input v-model="form.location" placeholder="请输入教室编号"></el-input>
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="班级名称" prop="class_name">
                  <el-input v-model="form.class_name" placeholder="例如：计算机1班"></el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="应到人数" prop="class_size">
                  <el-input-number
                    v-model="form.class_size"
                    :min="0"
                    :max="200"
                    controls-position="right"
                  ></el-input-number>
                </el-form-item>
              </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="教学周数" prop="week_num">
                <el-input-number
                  v-model="form.week_num"
                  :min="1"
                  :max="20"
                  label="请输入1-20之间的周数"
                ></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="星期几" prop="weekday">
                <el-select v-model="form.weekday" placeholder="请选择">
                  <el-option
                    v-for="item in 7"
                    :key="item"
                    :label="'周' + ['日','一','二','三','四','五','六'][item-1]"
                    :value="item"
                  ></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <!-- 其他字段... -->
        </el-form>
        <span slot="footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确认</el-button>
        </span>
      </el-dialog>
      <el-dialog
        title="课程AI报告"
        :visible.sync="suggestionDialogVisible"
        width="50%"
      >
        <div class="suggestion-content">
          {{ currentSuggestion || '暂无报告内容' }}
        </div>
        <span slot="footer">
          <el-button @click="suggestionDialogVisible = false">关闭</el-button>
        </span>
      </el-dialog>
    </d2-container>
  </template>

<script>
import courseApi from '@/api/course'
import dayjs from 'dayjs'
export default {
  data () {
    return {
      searchQuery: {
        keyword: '',
        location: '',
        weekday: ''
      },
      locationOptions: [], // 将从API获取的地点选项
      suggestionDialogVisible: false,
      currentSuggestion: '',
      list: {
        data: [],
        total: 0
      },
      pagination: {
        current: 1,
        size: 10
      },
      loading: false,
      dialogVisible: false,
      dialogTitle: '新增课程',
      form: {
        name: '',
        teacher: '',
        location: '',
        start_time: '',
        end_time: '',
        week_num: '',
        weekday: 1,
        class_name: '',
        class_size: 0
      },
      rules: {
        name: [{ required: true, message: '请输入课程名称', trigger: 'blur' }],
        start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
        end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
      }
    }
  },
  mounted () {
    this.fetchLocationOptions()
    this.fetchData()
  },
  methods: {
    async showSuggestion (row) {
      try {
      // 如果列表数据中已有建议内容
        if (row.suggestion) {
          this.currentSuggestion = row.suggestion
          this.suggestionDialogVisible = true
        }
      } catch (error) {
        console.error('获取报告失败:', error)
        this.$message.error('获取报告内容失败')
      }
    },
    async fetchLocationOptions () {
      try {
        const res = await courseApi.getLocations()
        this.locationOptions = res.data
      } catch (error) {
        console.error('获取地点选项失败:', error)
      }
    },
    handleSearchClear () {
      this.searchQuery.keyword = ''
      this.fetchData()
    },
    resetSearch () {
      this.searchQuery = {
        keyword: '',
        location: '',
        weekday: ''
      }
      this.fetchData()
    },
    async fetchData () {
      this.loading = true
      try {
        const params = {
          page: this.pagination.current,
          page_size: this.pagination.size,
          ...this.searchQuery
        }
        // 移除空值参数
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null) {
            delete params[key]
          }
        })
        const res = await courseApi.getCoursesList(params)
        this.list = {
          data: res.data,
          total: res.meta.total
        }
      } finally {
        this.loading = false
      }
    },
    handleSizeChange (val) {
      this.pagination.size = val
      this.fetchData()
    },
    handleCurrentChange (val) {
      this.pagination.current = val
      this.fetchData()
    },
    handleCreate () {
      this.dialogTitle = '新增课程'
      this.form = this.$options.data().form
      this.dialogVisible = true
    },
    handleEdit (row) {
      this.dialogTitle = '编辑课程'
      this.form = { ...row }
      this.dialogVisible = true
    },
    async submitForm () {
      this.$refs.form.validate(async valid => {
        if (!valid) return
        try {
          if (this.form.id) {
            await courseApi.updateCourse(this.form.id, this.form)
          } else {
            await courseApi.createCourse(this.form)
          }
          this.$message.success('操作成功')
          this.dialogVisible = false
          this.pagination.current = 1 // 新增后回到第一页
          this.fetchData()
        } catch (error) {
          console.error(error)
        }
      })
    },
    async handleDelete (row) {
      try {
        await this.$confirm('确认删除该课程？', '提示', { type: 'warning' })
        await courseApi.deleteCourse(row.id)
        this.$message.success('删除成功')
        // 如果当前页最后一条被删除，且不是第一页，则返回上一页
        if (this.list.data.length === 1 && this.pagination.current > 1) {
          this.pagination.current -= 1
        }
        this.fetchData()
      } catch (error) {
        console.error(error)
      }
    },
    formatTime (time) {
      return dayjs(time).format('MM-DD HH:mm')
    }
  }
}
</script>

<style scoped>
.header-search {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.suggestion-content {
  max-height: 60vh;
  overflow: auto;
  line-height: 1.8;
  white-space: pre-wrap;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.el-form-item {
  margin-bottom: 22px;
}
.el-select {
  width: 100%;
}
.el-input-number {
  width: 100%;
}
</style>
