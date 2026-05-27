const app = getApp();
const { AnalyzeAPI } = require('../../utils/api');
const { 
  redirectTo, 
  switchTab, 
  showToast,
  showModal
} = require('../../utils/util');

Page({
  data: {
    loading: true,
    polling: false,
    analysis: null,
    version: 'light',
    cacheKey: null,
    progress: 0,
    statusText: '初始化...',
    pollTimer: null
  },

  onLoad: function(options) {
    console.log('结果页加载', options);
    
    const version = options.version || 'light';
    const cacheKey = options.cacheKey;
    const polling = options.polling === 'true';
    
    this.setData({
      version: version,
      cacheKey: cacheKey,
      polling: polling
    });
    
    if (polling && cacheKey) {
      // 轮询模式
      this.startPolling();
    } else {
      // 直接展示模式
      this.loadResult();
    }
  },

  onUnload: function() {
    // 清除定时器
    if (this.data.pollTimer) {
      clearInterval(this.data.pollTimer);
    }
  },

  // 加载结果
  loadResult: function() {
    const analysis = app.globalData.analysisResult;
    
    if (analysis) {
      this.setData({
        analysis: analysis,
        loading: false
      });
    } else {
      // 尝试从缓存获取
      const cachedResult = tt.getStorageSync('analysisResult_' + this.data.version);
      if (cachedResult) {
        this.setData({
          analysis: cachedResult,
          loading: false
        });
      } else {
        showToast('未找到分析结果');
        switchTab('/pages/index/index');
      }
    }
  },

  // 开始轮询
  startPolling: function() {
    let pollCount = 0;
    const maxPolls = 30; // 最多30次
    const statusTexts = [
      '正在分析您的数据...',
      '匹配行业数据库...',
      '生成个性化建议...',
      '优化推荐结果...',
      '即将完成...'
    ];
    
    this.setData({
      progress: 10,
      statusText: statusTexts[0]
    });
    
    const timer = setInterval(async () => {
      pollCount++;
      
      // 更新进度
      const progress = Math.min(10 + pollCount * 3, 95);
      const statusIndex = Math.min(Math.floor(pollCount / 6), statusTexts.length - 1);
      
      this.setData({
        progress: progress,
        statusText: statusTexts[statusIndex]
      });
      
      if (pollCount >= maxPolls) {
        clearInterval(timer);
        showToast('分析超时，请重试');
        switchTab('/pages/index/index');
        return;
      }
      
      // 尝试获取结果
      try {
        const result = await AnalyzeAPI.pollResult(this.data.cacheKey, this.data.version);
        
        if (result.status === 'completed' && result.analysis) {
          clearInterval(timer);
          
          // 保存结果
          app.globalData.analysisResult = result.analysis;
          tt.setStorageSync('analysisResult_' + this.data.version, result.analysis);
          
          this.setData({
            polling: false,
            loading: false,
            analysis: result.analysis,
            progress: 100
          });
        }
      } catch (error) {
        console.error('轮询失败', error);
      }
    }, 1500); // 每1.5秒轮询一次
    
    this.setData({
      pollTimer: timer
    });
  },

  // 分享结果
  shareResult: function() {
    tt.showShareMenu({
      withShareTicket: true
    });
    showToast('点击右上角分享');
  },

  // 重新测评
  startOver: function() {
    // 清除缓存
    const userType = app.globalData.userType;
    const version = this.data.version;
    tt.removeStorageSync('quizAnswers_' + userType + '_' + version);
    tt.removeStorageSync('analysisResult_' + version);
    app.globalData.answers = {};
    app.globalData.analysisResult = null;
    
    switchTab('/pages/index/index');
  },

  // 升级
  goUpgrade: function() {
    showModal('升级到深度版', '支付9.9元获取完整分析报告', {
      confirmText: '立即升级'
    }).then(confirmed => {
      if (confirmed) {
        app.globalData.currentVersion = 'deep';
        redirectTo('/pages/payment/payment?version=deep');
      }
    });
  },

  // 分享
  onShareAppMessage: function() {
    const title = this.data.analysis ? 
      '我在职路星途完成了职业测评！' : 
      '职路星途 - AI职业规划';
    
    return {
      title: title,
      path: '/pages/index/index'
    };
  }
});
