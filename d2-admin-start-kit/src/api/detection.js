import { request } from '@/api/service'

export default {
  upload (data, onUploadProgress) {
    return request({
      url: '/detection/upload',
      method: 'post',
      data,
      onUploadProgress
    })
  },

  getResults (params) {
    return request({
      url: '/detection/results',
      method: 'get',
      params
    })
  },

  getResultDetail (id) {
    return request({
      url: `/detection/results/${id}`,
      method: 'get'
    })
  }
}
