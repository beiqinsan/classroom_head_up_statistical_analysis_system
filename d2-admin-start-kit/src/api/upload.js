import { request } from '@/api/service'

export default {
  uploadFile (data) {
    return request({
      url: '/upload',
      method: 'post',
      data,
      timeout: 100000
    })
  }
}
