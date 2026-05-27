// API请求封装
const app = getApp();

// 请求基础配置
const BASE_URL = app.globalData.apiBaseUrl || '';

// 通用请求封装
function request(url, data = {}, method = 'GET', options = {}) {
  return new Promise((resolve, reject) => {
    tt.request({
      url: BASE_URL + url,
      data: data,
      method: method,
      header: {
        'content-type': 'application/json',
        ...options.header
      },
      timeout: options.timeout || 30000,
      success: function(res) {
        console.log('请求成功:', url, res);
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject({
            message: '请求失败',
            statusCode: res.statusCode,
            data: res.data
          });
        }
      },
      fail: function(err) {
        console.error('请求失败:', url, err);
        reject(err);
      }
    });
  });
}

// 云函数调用封装
function callCloudFunction(name, data = {}) {
  return new Promise((resolve, reject) => {
    if (tt.cloud) {
      tt.cloud.callFunction({
        name: name,
        data: data,
        success: function(res) {
          console.log('云函数调用成功:', name, res);
          resolve(res.result);
        },
        fail: function(err) {
          console.error('云函数调用失败:', name, err);
          reject(err);
        }
      });
    } else {
      reject(new Error('云开发不可用'));
    }
  });
}

// 分析API
const AnalyzeAPI = {
  // 轻量版分析
  analyzeLight: function(data) {
    if (tt.cloud) {
      return callCloudFunction('analyze', { ...data, version: 'light' });
    }
    return request('/api/analyze', data, 'POST');
  },
  
  // 深度版分析
  analyzeDeep: function(data) {
    if (tt.cloud) {
      return callCloudFunction('analyze', { ...data, version: 'deep' });
    }
    return request('/api/analyze-deep', data, 'POST');
  },
  
  // VIP版分析
  analyzeVIP: function(data) {
    if (tt.cloud) {
      return callCloudFunction('analyze', { ...data, version: 'vip' });
    }
    return request('/api/analyze-vip', data, 'POST');
  },
  
  // 轮询结果
  pollResult: function(cacheKey, version) {
    const endpoints = {
      light: '/api/analyze/poll',
      deep: '/api/analyze-deep/poll',
      vip: '/api/analyze-vip/poll'
    };
    return request(endpoints[version] + '/' + cacheKey, {}, 'GET');
  }
};

// 支付API
const PaymentAPI = {
  // 创建支付订单
  createOrder: function(version, deviceId = '') {
    const data = { version, device_id: deviceId };
    if (tt.cloud) {
      return callCloudFunction('payment', { action: 'create', ...data });
    }
    return request('/api/payment/create', data, 'POST');
  },
  
  // 检查支付状态
  checkStatus: function(orderId) {
    if (tt.cloud) {
      return callCloudFunction('payment', { action: 'check', order_id: orderId });
    }
    return request('/api/payment/check/' + orderId, {}, 'GET');
  },
  
  // 模拟支付（测试用）
  simulatePayment: function(orderId) {
    if (tt.cloud) {
      return callCloudFunction('payment', { action: 'simulate', order_id: orderId });
    }
    return request('/api/payment/simulate', { order_id: orderId }, 'POST');
  },
  
  // 抖音支付
  douyinPay: function(orderInfo) {
    return new Promise((resolve, reject) => {
      tt.pay({
        orderInfo: orderInfo,
        service: 5, // 5: 抖音支付
        success: function(res) {
          console.log('支付成功', res);
          resolve(res);
        },
        fail: function(err) {
          console.error('支付失败', err);
          reject(err);
        }
      });
    });
  }
};

// VIP咨询API
const VIPConsultAPI = {
  // 获取咨询列表
  getList: function() {
    if (tt.cloud) {
      return callCloudFunction('vip-consult', { action: 'list' });
    }
    return request('/api/vip/consults', {}, 'GET');
  },
  
  // 提交咨询
  submit: function(data) {
    if (tt.cloud) {
      return callCloudFunction('vip-consult', { action: 'submit', ...data });
    }
    return request('/api/vip/consult', data, 'POST');
  },
  
  // 获取咨询详情
  getDetail: function(consultId) {
    if (tt.cloud) {
      return callCloudFunction('vip-consult', { action: 'detail', id: consultId });
    }
    return request('/api/vip/consult/' + consultId, {}, 'GET');
  },
  
  // 删除咨询
  delete: function(consultId) {
    if (tt.cloud) {
      return callCloudFunction('vip-consult', { action: 'delete', id: consultId });
    }
    return request('/api/vip/consult/' + consultId, {}, 'DELETE');
  },
  
  // 保存报告
  saveReport: function(consultId, reportData) {
    if (tt.cloud) {
      return callCloudFunction('vip-consult', { 
        action: 'save-report', 
        id: consultId, 
        reportData: reportData 
      });
    }
    return request('/api/vip/consult/' + consultId + '/report', { reportData }, 'PUT');
  }
};

// 系统API
const SystemAPI = {
  // 健康检查
  health: function() {
    return request('/api/health', {}, 'GET');
  },
  
  // 获取版本信息
  version: function() {
    return request('/api/version', {}, 'GET');
  }
};

module.exports = {
  request,
  callCloudFunction,
  AnalyzeAPI,
  PaymentAPI,
  VIPConsultAPI,
  SystemAPI
};
