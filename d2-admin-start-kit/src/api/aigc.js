import { request } from '@/api/service'

export default {
  generalCourseRecoment (chartData) {
    return request({
      url: '/api/chat',
      method: 'post',
      data: {
        messages: [
          {
            role: 'system',
            content:
              '你是一位教育数据分析专家，请根据课程检测数据生成结构化分析报告'
          },
          {
            role: 'user',
            content: `分析要求：
  1. 课程效果评估（分优/良/中/差）
  2. 发现若干个主要问题
  3. 提出若干条改进建议
  4. 控制字数在500字以内
  课程数据：${JSON.stringify(chartData)}
  数据解释：lookup_count指当前时间戳抬头人数，other_count指当前时间戳其他状态人数`
          }
        ],
        stream: false // 明确关闭流式
      },
      timeout: 120000
    })
  }
}
