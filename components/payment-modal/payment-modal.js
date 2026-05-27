Component({
  properties: {
    show: { type: Boolean, value: false },
    version: { type: String, value: 'deep' },
    versionName: { type: String, value: '' },
    price: { type: String, value: '' },
    orderId: { type: String, value: '' }
  },
  data: {
    paymentStatus: '等待支付...',
    paying: false,
    deepBenefits: [
      '25-30道深度测评题',
      '完整分析报告与行动规划',
      '技能差距分析与风险提示',
      '宏观趋势与职业赛道推荐'
    ],
    vipBenefits: [
      '深度版全部功能',
      '个性化咨询（3个专属问题）',
      '个性化避坑指南',
      '完整行动规划方案',
      '专属报告终身保存'
    ]
  },
  methods: {
    onClose: function() {
      if (this.data.paying) return;
      this.triggerEvent('close');
    },
    onSimulatePay: function() {
      var that = this;
      if (that.data.paying) return;
      that.setData({ paying: true, paymentStatus: '支付中...' });
      setTimeout(function() {
        that.setData({ paymentStatus: '支付成功！即将跳转...' });
        setTimeout(function() {
          that.triggerEvent('success', { version: that.properties.version });
          that.setData({ paying: false, paymentStatus: '等待支付...' });
        }, 800);
      }, 1500);
    },
    onRealPay: function() {
      var that = this;
      if (that.data.paying) return;
      var priceFen = parseInt(that.properties.price.replace('¥', '').replace('.', '')) || 990;
      that.setData({ paying: true, paymentStatus: '调起支付...' });
      
      try {
        // 抖音支付SDK
        tt.requestOrderPayment({
          orderInfo: {
            order_id: that.properties.orderId,
            order_name: that.properties.versionName,
            order_price: priceFen
          },
          success: function(res) {
            that.setData({ paymentStatus: '支付成功！即将跳转...' });
            setTimeout(function() {
              that.triggerEvent('success', { version: that.properties.version, orderId: that.properties.orderId });
              that.setData({ paying: false, paymentStatus: '等待支付...' });
            }, 800);
          },
          fail: function(err) {
            console.error('支付失败:', err);
            that.setData({ paying: false, paymentStatus: '支付取消' });
            tt.showToast({ title: '支付取消或失败，可尝试模拟支付', icon: 'none', duration: 2000 });
          }
        });
      } catch(e) {
        console.error('调用支付SDK异常:', e);
        that.setData({ paying: false, paymentStatus: '支付异常' });
        tt.showToast({ title: '支付服务暂时不可用，请稍后再试', icon: 'none' });
      }
    },
    stopPropagation: function() {}
  },
  observers: {
    'show': function(newVal) {
      if (!newVal) {
        this.setData({ paying: false, paymentStatus: '等待支付...' });
      }
    }
  }
});