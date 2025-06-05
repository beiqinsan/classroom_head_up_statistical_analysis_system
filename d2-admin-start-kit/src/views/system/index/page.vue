<template>
  <d2-container class="page">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="logo-container">
        <img src="./image/all.png" class="logo" alt="Logo">
        <h1 class="title">课堂抬头率统计分析系统</h1>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 欢迎横幅 -->
      <el-card class="welcome-banner">
        <div class="banner-content">
          <h2>欢迎使用课堂抬头率统计分析系统</h2>
        </div>
      </el-card>

      <!-- 功能卡片区 -->
      <div class="feature-cards">
        <el-row :gutter="20">
          <el-col :span="8" v-for="(feature, index) in features" :key="index">
            <el-card class="feature-card" shadow="hover" @click.native="$router.push(feature.path)">
              <div class="card-icon">
                <i :class="feature.icon" :style="{color: feature.color}"></i>
              </div>
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.description }}</p>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
    <!-- 页脚 -->
    <div class="footer">
      <p>© 2025 基于YOLO算法的课堂抬头率统计分析系统</p>
    </div>
  </d2-container>
</template>

<script>
export default {
  data () {
    return {
      features: [
        {
          title: '课程表查询',
          description: '使用课程表查看课堂学生抬头率统计',
          icon: 'el-icon-video-camera',
          color: '#409EFF',
          path: '/course'
        },
        {
          title: '课程搜索与管理',
          description: '管理与搜索课程详细信息',
          icon: 'el-icon-picture',
          color: '#67C23A',
          path: '/course/list'
        },
        {
          title: '模型调用',
          description: '调用模型检测图片和视频',
          icon: 'el-icon-film',
          color: '#E6A23C',
          path: '/detectionPage'
        }
      ]
    }
  }
}
</script>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    background: rgba(0, 0, 0, 0.7);
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    .logo-container {
      display: flex;
      align-items: center;

      .logo {
        width: 50px;
        height: 50px;
        margin-right: 15px;
      }

      .title {
        color: #fff;
        margin: 0;
        font-size: 22px;
      }
    }

  }
  .main-content {
    flex: 1;
    padding: 20px;

    .welcome-banner {
      margin-bottom: 20px;
      background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
      color: #fff;

      .banner-content {
        padding: 40px;
        text-align: center;

        h2 {
          font-size: 28px;
          margin-bottom: 15px;
        }

        p {
          font-size: 16px;
          margin-bottom: 25px;
        }
      }
    }

    .feature-cards {
      margin-bottom: 20px;

      .feature-card {
        cursor: pointer;
        transition: all 0.3s;
        height: 220px;
        text-align: center;

        &:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }

        .card-icon {
          font-size: 50px;
          margin: 20px 0;
        }

        h3 {
          color: #333;
          margin-bottom: 15px;
        }

        p {
          color: #666;
          font-size: 14px;
        }
      }
    }

    .quick-start {
      margin-bottom: 20px;
    }
  }

  .footer {
    padding: 20px;
    text-align: center;
    background: rgba(0, 0, 0, 0.7);
    color: #fff;

    .social-links {
      margin-top: 10px;

      a {
        color: #fff;
        margin: 0 10px;
        font-size: 18px;

        &:hover {
          color: #ffd04b;
        }
      }
    }
  }
}
</style>
