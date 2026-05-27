const { VIPConsultAPI } = require('../../utils/api');
const { showToast, showModal, formatTimestamp } = require('../../utils/util');

Page({
  data: {
    consults: [],
    filteredConsults: [],
    loading: true,
    searchQuery: '',
    currentFilter: 'all',
    showDetail: false,
    currentConsult: null,
    userTypeNames: {
      '1': '30-40岁转型',
      '2': '应届生',
      '3': '学生家长'
    },
    statusNames: {
      'pending': '待处理',
      'in_progress': '处理中',
      'completed': '已完成'
    }
  },

  onLoad: function(options) {
    this.loadConsults();
  },

  onPullDownRefresh: function() {
    this.loadConsults().then(() => {
      tt.stopPullDownRefresh();
    });
  },

  // 加载咨询列表
  loadConsults: async function() {
    this.setData({ loading: true });
    
    try {
      const result = await VIPConsultAPI.getList();
      
      if (result.success) {
        this.setData({
          consults: result.data || [],
          loading: false
        });
        this.applyFilters();
      } else {
        showToast('加载失败');
        this.setData({ loading: false });
      }
    } catch (error) {
      console.error('加载失败', error);
      showToast('加载失败');
      this.setData({ loading: false });
    }
  },

  // 计算统计数
  get pendingCount() {
    return this.data.consults.filter(c => c.status === 'pending').length;
  },

  get completedCount() {
    return this.data.consults.filter(c => c.status === 'completed').length;
  },

  // 搜索
  onSearchInput: function(e) {
    this.setData({ searchQuery: e.detail.value });
    this.applyFilters();
  },

  // 筛选
  setFilter: function(e) {
    const filter = e.currentTarget.dataset.filter;
    this.setData({ currentFilter: filter });
    this.applyFilters();
  },

  // 应用筛选
  applyFilters: function() {
    let filtered = [...this.data.consults];
    
    // 状态筛选
    if (this.data.currentFilter !== 'all') {
      filtered = filtered.filter(c => c.status === this.data.currentFilter);
    }
    
    // 搜索筛选
    if (this.data.searchQuery) {
      const q = this.data.searchQuery.toLowerCase();
      filtered = filtered.filter(c => 
        (c.name && c.name.toLowerCase().includes(q)) ||
        (c.email && c.email.toLowerCase().includes(q)) ||
        (c.consultText && c.consultText.toLowerCase().includes(q))
      );
    }
    
    this.setData({ filteredConsults: filtered });
  },

  // 查看详情
  viewDetail: async function(e) {
    const consultId = e.currentTarget.dataset.id;
    
    try {
      const result = await VIPConsultAPI.getDetail(consultId);
      
      if (result.success) {
        this.setData({
          currentConsult: result.data,
          showDetail: true
        });
      } else {
        showToast('获取详情失败');
      }
    } catch (error) {
      console.error('获取详情失败', error);
      showToast('获取详情失败');
    }
  },

  // 关闭详情
  closeDetail: function() {
    this.setData({
      showDetail: false,
      currentConsult: null
    });
  },

  // 阻止事件冒泡
  stopPropagation: function() {
    // 空函数，用于阻止事件冒泡
  },

  // 删除咨询
  deleteConsult: async function(e) {
    const consultId = e.currentTarget.dataset.id;
    
    const confirmed = await showModal(
      '确认删除',
      '删除后无法恢复，确定要删除吗？',
      { confirmText: '删除', confirmColor: '#dc2626' }
    );
    
    if (!confirmed) return;
    
    try {
      const result = await VIPConsultAPI.delete(consultId);
      
      if (result.success) {
        showToast('删除成功', 'success');
        this.loadConsults();
      } else {
        showToast('删除失败');
      }
    } catch (error) {
      console.error('删除失败', error);
      showToast('删除失败');
    }
  },

  // 确认删除（从详情页）
  confirmDelete: async function() {
    if (!this.data.currentConsult) return;
    
    const confirmed = await showModal(
      '确认删除',
      '删除后无法恢复，确定要删除吗？',
      { confirmText: '删除', confirmColor: '#dc2626' }
    );
    
    if (!confirmed) return;
    
    try {
      const result = await VIPConsultAPI.delete(this.data.currentConsult.consultId);
      
      if (result.success) {
        showToast('删除成功', 'success');
        this.closeDetail();
        this.loadConsults();
      } else {
        showToast('删除失败');
      }
    } catch (error) {
      console.error('删除失败', error);
      showToast('删除失败');
    }
  },

  // 格式化时间
  formatTime: function(timestamp) {
    if (!timestamp) return '';
    
    if (timestamp.$date) {
      return formatTimestamp(timestamp.$date / 1000);
    }
    
    if (timestamp instanceof Date) {
      return formatTimestamp(timestamp.getTime() / 1000);
    }
    
    if (typeof timestamp === 'number') {
      if (timestamp > 1000000000000) {
        timestamp = timestamp / 1000;
      }
      return formatTimestamp(timestamp);
    }
    
    return '';
  }
});
