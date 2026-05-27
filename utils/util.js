// 工具函数

// 格式化时间戳
function formatTimestamp(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp * 1000);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

// 防抖函数
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 节流函数
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// 深拷贝
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  const clone = Array.isArray(obj) ? [] : {};
  for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
      clone[key] = deepClone(obj[key]);
    }
  }
  return clone;
}

// 生成唯一ID
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Toast提示
function showToast(title, icon = 'none', duration = 2000) {
  tt.showToast({
    title: title,
    icon: icon,
    duration: duration
  });
}

// Loading提示
function showLoading(title = '加载中...') {
  tt.showLoading({
    title: title,
    mask: true
  });
}

// 隐藏Loading
function hideLoading() {
  tt.hideLoading();
}

// 确认弹窗
function showModal(title, content, options = {}) {
  return new Promise((resolve, reject) => {
    tt.showModal({
      title: title,
      content: content,
      confirmText: options.confirmText || '确定',
      confirmColor: options.confirmColor || '#6366f1',
      cancelText: options.cancelText || '取消',
      cancelColor: options.cancelColor || '#64748b',
      success: function(res) {
        if (res.confirm) {
          resolve(true);
        } else {
          resolve(false);
        }
      },
      fail: function(err) {
        reject(err);
      }
    });
  });
}

// 跳转到页面
function navigateTo(url) {
  tt.navigateTo({
    url: url,
    fail: function(err) {
      console.error('跳转失败', err);
    }
  });
}

// 跳转并关闭当前页面
function redirectTo(url) {
  tt.redirectTo({
    url: url,
    fail: function(err) {
      console.error('跳转失败', err);
    }
  });
}

// 返回上一页
function navigateBack(delta = 1) {
  tt.navigateBack({
    delta: delta
  });
}

// 切换Tab
function switchTab(url) {
  tt.switchTab({
    url: url
  });
}

// 设置本地存储
function setStorage(key, value) {
  try {
    tt.setStorageSync(key, value);
  } catch (e) {
    console.error('存储失败', e);
  }
}

// 获取本地存储
function getStorage(key, defaultValue = null) {
  try {
    return tt.getStorageSync(key) || defaultValue;
  } catch (e) {
    console.error('获取存储失败', e);
    return defaultValue;
  }
}

// 移除本地存储
function removeStorage(key) {
  try {
    tt.removeStorageSync(key);
  } catch (e) {
    console.error('移除存储失败', e);
  }
}

// 分享功能
function shareAppMessage(options = {}) {
  return {
    title: options.title || '职路星途 - AI职业规划',
    imageUrl: options.imageUrl || '',
    path: options.path || '/pages/index/index'
  };
}

// 获取系统信息
function getSystemInfo() {
  return new Promise((resolve) => {
    tt.getSystemInfo({
      success: function(res) {
        resolve(res);
      },
      fail: function() {
        resolve(null);
      }
    });
  });
}

module.exports = {
  formatTimestamp,
  debounce,
  throttle,
  deepClone,
  generateId,
  showToast,
  showLoading,
  hideLoading,
  showModal,
  navigateTo,
  redirectTo,
  navigateBack,
  switchTab,
  setStorage,
  getStorage,
  removeStorage,
  shareAppMessage,
  getSystemInfo
};
