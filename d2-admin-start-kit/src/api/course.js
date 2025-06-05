import { request } from '@/api/service' // 替换原生的 axios 引入

export default {
  getVideoPath (id) {
    return request({
      url: `/courses/video/${id}`,
      method: 'get'
    })
  },
  getLocations () {
    return request({
      url: '/courses/locations',
      method: 'get'
    })
  },
  getSemesterConfig () {
    return request({
      url: '/semester/config',
      method: 'get'
    })
  },
  UpdateSuggestCourse (id, data) {
    return request({
      url: `/courses/suggestion/${id}`,
      method: 'put',
      params: {
        suggestion: data
      }
    })
  },
  /**
   * 获取周课表数据
   * @param {number} weekNum - 开学周数
   * @param {string} startDate - 周起始日期 (YYYY-MM-DD)
   * @returns {Promise<{week_num: number, courses: Array}>}
   */
  getWeeklyCourses (weekNum, startDate) {
    return request({
      url: '/courses/weekly',
      method: 'get',
      params: {
        week_num: weekNum,
        start_date: startDate
      }
    })
  },

  /**
   * 分页获取课程列表
   * @param {number} page - 页码
   * @param {number} size - 每页数量
   * @returns {Promise<{total: number, items: Array}>}
   */
  getCoursesList (params) {
    return request({
      url: '/courses/list',
      method: 'get',
      params
    })
  },
  /**
   * 获取课程详情
   * @param {number} id - 课程ID
   * @param {number} [weekNum] - 指定周数
   * @returns {Promise}
   */
  getCourseDetail (id) {
    return request({
      url: `/courses/detail/${id}`,
      method: 'get'
    })
  },
  getDetectionData (courseId) {
    return request({
      url: '/detection',
      method: 'get',
      params: {
        // 可扩展其他参数
        course_id: courseId
      }
    })
  },
  /**
   * 创建课程
   * @param {Object} data - 课程数据
   * @returns {Promise}
   */
  createCourse (data) {
    return request({
      url: '/courses',
      method: 'post',
      data
    })
  },

  /**
   * 批量创建课程（Excel导入使用）
   * @param {FormData} formData - 包含文件数据的表单数据
   * @returns {Promise<{success_count: number, failed_items: Array}>}
   */
  batchCreateCourses (formData) {
    return request({
      url: '/courses/batch',
      method: 'post',
      headers: {
        'Content-Type': 'application/json' // 重要：文件上传需要指定类型
      },
      data: formData
    })
  },

  /**
   * 更新课程
   * @param {number} id - 课程ID
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  updateCourse (id, data) {
    return request({
      url: `/courses/${id}`,
      method: 'patch', // 使用 patch 方法进行部分更新
      data
    })
  },

  /**
   * 删除课程
   * @param {number} id - 课程ID
   * @returns {Promise}
   */
  deleteCourse (id) {
    return request({
      url: `/courses/${id}`,
      method: 'delete'
    })
  },

  /**
   * 检测时间冲突
   * @param {Object} params - 检测参数
   * @param {string} params.location - 地点
   * @param {string} params.start_time - 开始时间 (ISO)
   * @param {string} params.end_time - 结束时间 (ISO)
   * @returns {Promise<{conflict: boolean, existing: Object|null}>}
   */
  checkConflict (params) {
    return request({
      url: '/courses/check-conflict',
      method: 'post',
      data: params
    })
  }
}
