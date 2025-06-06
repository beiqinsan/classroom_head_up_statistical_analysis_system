import { uniqueId } from 'lodash'
// import { path } from 'node_modules/zrender/lib/export'

/**
 * @description 给菜单数据补充上 path 字段
 * @description https://github.com/d2-projects/d2-admin/issues/209
 * @param {Array} menu 原始的菜单数据
 */
function supplementPath (menu) {
  return menu.map(e => ({
    ...e,
    path: e.path || uniqueId('d2-menu-empty-'),
    ...e.children ? {
      children: supplementPath(e.children)
    } : {}
  }))
}

export const menuHeader = supplementPath([
  { path: '/index', title: '首页', icon: 'home' },
  { path: '/course', title: '课程表查询', icon: 'book' },
  { path: '/course/list', title: '课程搜索与管理', icon: 'list' },
  { path: '/detectionPage', title: '模型检测', icon: 'dashboard' }
])

export const menuAside = supplementPath([
  { path: '/index', title: '首页', icon: 'home' },
  {
    path: '/course',
    title: '课程表查询',
    icon: 'book'
  },
  { path: '/course/list', title: '课程搜索与管理', icon: 'list' },
  { path: '/detectionPage', title: '模型检测', icon: 'dashboard' }
])
