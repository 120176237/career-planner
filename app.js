App({
  globalData: {
    userInfo: null,
    hasLogin: false,
    apiBaseUrl: '', // 抖音云部署使用相对路径
    userType: null, // 1:30-40岁, 2:应届生, 3:家长
    answers: {},
    questions: [],
    currentVersion: 'light' // light/deep/vip
  },

  onLaunch: function(options) {
    console.log('职路星途小程序启动', options);
    
    // 初始化云开发
    if (tt.canIUse('cloud')) {
      tt.cloud.init({
        env: 'your-env-id', // 请替换为实际云环境ID
        traceUser: true
      });
    }

    // 检查登录状态
    this.checkLoginStatus();
  },

  onShow: function(options) {
    console.log('小程序显示', options);
  },

  onHide: function() {
    console.log('小程序隐藏');
  },

  onError: function(msg) {
    console.error('小程序错误:', msg);
  },

  checkLoginStatus: function() {
    const userInfo = tt.getStorageSync('userInfo');
    if (userInfo) {
      this.globalData.userInfo = userInfo;
      this.globalData.hasLogin = true;
    }
  },

  login: function(callback) {
    const that = this;
    tt.getUserProfile({
      desc: '用于完善用户资料',
      success: function(res) {
        console.log('获取用户信息成功', res);
        that.globalData.userInfo = res.userInfo;
        that.globalData.hasLogin = true;
        tt.setStorageSync('userInfo', res.userInfo);
        
        // 获取用户手机号（可选）
        that.getPhoneNumber();
        
        if (callback) {
          callback(res);
        }
      },
      fail: function(err) {
        console.error('获取用户信息失败', err);
        if (callback) {
          callback(null, err);
        }
      }
    });
  },

  getPhoneNumber: function() {
    // 需要先通过 button open-type="getPhoneNumber" 获取
  }
});
