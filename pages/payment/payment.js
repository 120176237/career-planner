const app = getApp();
const { PaymentAPI } = require('../../utils/api');
const { 
  navigateTo, 
  redirectTo,
  showToast, 
  showLoading, 
  hideLoading 
} = require('../../utils/util');

Page({
  data: {
    version: 'deep',
    productName: '深度版',
    price: 9.9,
    selectedMethod: 'douyin',
    paying: false,
    orderId: null
  },

  onLoad: function(options) {
    console.log('支付页加载', options);
    
    const version = options.version || 'deep';
    let productName = '深度版';
    let price = 9.9;
    
    if (version === 'vip') {
      productName = 'VIP版';
      price = 19.9;
    }
    
    this.setData({
      version: version,
      productName: productName,
      price: price
    });
    
    // 创建订单
    this.createOrder();
  },

  // 创建订单
  createOrder: async function() {
    try {
      const result = await PaymentAPI.createOrder(this.data.version);
      
      if (result.orderId) {
        this.setData({
          orderId: result.orderId
        });
      }
    } catch (error) {
      console.error('创建订单失败', error);
    }
  },

  // 选择支付方式
  selectMethod: function(e) {
    const method = e.currentTarget.dataset.method;
    this.setData({
      selectedMethod: method
    });
  },

  // 确认支付
  confirmPayment: async function() {
    if (!this.data.orderId) {
      showToast('订单创建失败，请重试');
      return;
    }
    
    this.setData({
      paying: true
    });
    
    showLoading('处理中...');
    
    try {
      // 调用抖音支付
      if (this.data.selectedMethod === 'douyin') {
        // 这里调用抖音支付SDK
        // 实际项目中需要从服务端获取订单信息
        await this.douyinPay();
      } else {
        showToast('暂不支持此支付方式');
      }
    } catch (error) {
      console.error('支付失败', error);
      hideLoading();
      showToast('支付失败，请重试');
    } finally {
      this.setData({
        paying: false
      });
    }
  },

  // 抖音支付
  douyinPay: function() {
    return new Promise((resolve, reject) => {
      // 模拟支付过程
      // 实际项目中应该调用 tt.pay
      // 这里为了演示直接模拟成功
      
      setTimeout(() => {
        // 检查支付状态
        this.checkPaymentAndRedirect();
        resolve();
      }, 1500);
    });
  },

  // 模拟支付（测试用）
  simulatePayment: async function() {
    showLoading('模拟支付中...');
    
    // 直接模拟成功，不调用API
    setTimeout(() => {
      hideLoading();
      
      // 保存支付凭证
      tt.setStorageSync('paid_' + this.data.version, true);
      
      // 跳转到答题页
      showToast('支付成功', 'success');
      
      setTimeout(() => {
        navigateTo('/pages/quiz/quiz');
      }, 1500);
    }, 1000);
  },

  // 检查支付状态并跳转
  checkPaymentAndRedirect: async function() {
    showLoading('验证支付...');
    
    try {
      const result = await PaymentAPI.checkStatus(this.data.orderId);
      hideLoading();
      
      if (result.paid) {
        // 支付成功
        showToast('支付成功', 'success');
        
        // 保存支付凭证
        tt.setStorageSync('paid_' + this.data.version, true);
        
        // 跳转到答题页
        setTimeout(() => {
          navigateTo('/pages/quiz/quiz');
        }, 1500);
      } else {
        showToast('支付未完成');
      }
    } catch (error) {
      hideLoading();
      console.error('检查支付状态失败', error);
      // 即使检查失败也允许继续（演示用）
      showToast('支付成功（演示）', 'success');
      tt.setStorageSync('paid_' + this.data.version, true);
      
      setTimeout(() => {
        navigateTo('/pages/quiz/quiz');
      }, 1500);
    }
  }
});
