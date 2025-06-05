const state = {
  courses: []
}

const mutations = {
  SET_COURSES: (state, courses) => {
    state.courses = courses
  }
}

export default {
  namespaced: true, // 启用命名空间
  state,
  mutations
}
