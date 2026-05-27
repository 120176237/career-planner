const app = getApp();
const { AnalyzeAPI } = require('../../utils/api');
const { 
  navigateTo, 
  redirectTo, 
  showToast, 
  showLoading, 
  hideLoading 
} = require('../../utils/util');

Page({
  data: {
    questions: [],
    currentIndex: 0,
    answers: {},
    showError: false,
    submitting: false,
    cacheKey: null
  },

  onLoad: function(options) {
    console.log('答题页加载', options);
    
    // 从全局获取题目
    let questions = app.globalData.questions;
    const userType = app.globalData.userType;
    const version = app.globalData.currentVersion || 'light';
    
    if (!questions || questions.length === 0) {
      // 如果没有题目，尝试从utils获取
      const { getQuestions } = require('../../utils/questions');
      questions = getQuestions(userType, version);
      app.globalData.questions = questions;
    }
    
    if (questions.length === 0) {
      showToast('题目加载失败，请重试');
      redirectTo('/pages/index/index');
      return;
    }
    
    // 检查是否有缓存的答案
    const cachedAnswers = tt.getStorageSync('quizAnswers_' + userType + '_' + version);
    if (cachedAnswers && Object.keys(cachedAnswers).length > 0) {
      this.setData({
        answers: cachedAnswers
      });
    }
    
    this.setData({
      questions: questions,
      currentQuestion: questions[0]
    });
  },

  onShow: function() {
    // 页面显示
  },

  onUnload: function() {
    // 页面卸载时保存答案
    this.saveAnswers();
  },

  onHide: function() {
    // 页面隐藏时保存答案
    this.saveAnswers();
  },

  // 保存答案到本地
  saveAnswers: function() {
    const userType = app.globalData.userType;
    const version = app.globalData.currentVersion || 'light';
    tt.setStorageSync('quizAnswers_' + userType + '_' + version, this.data.answers);
  },

  // 选择选项
  selectOption: function(e) {
    const value = e.currentTarget.dataset.value;
    const id = e.currentTarget.dataset.id;
    
    const newAnswers = {
      ...this.data.answers,
      [id]: value
    };
    
    this.setData({
      answers: newAnswers,
      showError: false
    });
    
    // 保存到全局
    app.globalData.answers = newAnswers;
  },

  // 上一题
  goPrevious: function() {
    if (this.data.currentIndex > 0) {
      const newIndex = this.data.currentIndex - 1;
      this.setData({
        currentIndex: newIndex,
        currentQuestion: this.data.questions[newIndex],
        showError: false
      });
    }
  },

  // 下一题
  goNext: function() {
    const currentQuestion = this.data.currentQuestion;
    if (!this.data.answers[currentQuestion.id]) {
      this.setData({
        showError: true
      });
      return;
    }
    
    if (this.data.currentIndex < this.data.questions.length - 1) {
      const newIndex = this.data.currentIndex + 1;
      this.setData({
        currentIndex: newIndex,
        currentQuestion: this.data.questions[newIndex],
        showError: false
      });
    }
  },

  // 提交答案
  submitAnswers: async function() {
    const currentQuestion = this.data.currentQuestion;
    if (!this.data.answers[currentQuestion.id]) {
      this.setData({
        showError: true
      });
      return;
    }
    
    // 检查所有题目是否都已作答
    const allAnswered = this.data.questions.every(q => this.data.answers[q.id]);
    if (!allAnswered) {
      showToast('请完成所有题目');
      return;
    }
    
    this.setData({
      submitting: true,
      showError: false
    });
    
    showLoading('AI分析中...');
    
    try {
      const userType = app.globalData.userType;
      const version = app.globalData.currentVersion || 'light';
      const questions = this.data.questions;
      const answers = this.data.answers;
      
      // 调用API
      let result;
      if (version === 'light') {
        result = await AnalyzeAPI.analyzeLight({
          userType: userType,
          answers: answers,
          questions: questions
        });
      } else if (version === 'deep') {
        result = await AnalyzeAPI.analyzeDeep({
          userType: userType,
          answers: answers,
          questions: questions
        });
      } else {
        result = await AnalyzeAPI.analyzeVIP({
          userType: userType,
          answers: answers,
          questions: questions
        });
      }
      
      hideLoading();
      
      if (result.status === 'generating') {
        // 后台生成中，跳转到加载页或轮询页
        this.setData({
          cacheKey: result.cacheKey
        });
        
        // 跳转到结果页轮询
        redirectTo('/pages/result/result?cacheKey=' + result.cacheKey + '&version=' + version + '&polling=true');
      } else if (result.analysis) {
        // 直接有结果
        app.globalData.analysisResult = result.analysis;
        redirectTo('/pages/result/result?version=' + version);
      } else {
        showToast('分析失败，请重试');
      }
    } catch (error) {
      console.error('提交失败', error);
      hideLoading();
      showToast('分析失败，请重试');
    } finally {
      this.setData({
        submitting: false
      });
    }
  }
});
