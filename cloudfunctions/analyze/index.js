// 分析云函数
const cloud = require('tt-server-sdk');
cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const db = cloud.database();

// 行业数据库（从原项目server.py中提取）
const INDUSTRY_DATABASE = {
  "人工智能/大数据": {
    trends: ["大模型应用爆发", "AI赋能千行百业", "数据要素市场化"],
    salary: "高",
    growth: "高速增长",
    hot_roles: ["算法工程师", "AI产品经理", "数据工程师", "MLOps工程师"],
    education_require: "本科-硕士",
    physical_require: "light",
    threshold: "高"
  },
  "互联网/IT": {
    trends: ["产业互联网深化", "云原生普及", "信创加速"],
    salary: "中高",
    growth: "稳定增长",
    hot_roles: ["全栈工程师", "前端工程师", "后端工程师", "产品经理"],
    education_require: "本科",
    physical_require: "light",
    threshold: "中"
  },
  "医疗健康": {
    trends: ["老龄化加速", "医疗消费升级", "创新药发展"],
    salary: "中",
    growth: "稳定增长",
    hot_roles: ["医生", "医药代表", "医疗器械", "医疗销售"],
    education_require: "本科-博士",
    physical_require: "medium",
    threshold: "高"
  }
};

exports.main = async (event, context) => {
  const { userType, answers, questions, version } = event;
  const wxContext = cloud.getWXContext();
  const openid = wxContext.OPENID;
  
  console.log('分析请求', { userType, version, openid });
  
  try {
    // 1. 检查缓存
    const cacheKey = generateCacheKey(answers);
    const cacheResult = await checkCache(cacheKey, version, userType);
    
    if (cacheResult) {
      console.log('缓存命中');
      return {
        status: 'completed',
        analysis: cacheResult,
        cacheKey: cacheKey
      };
    }
    
    // 2. 进行评分和分析
    const analysisResult = await generateAnalysis(
      userType, 
      answers, 
      questions, 
      version
    );
    
    // 3. 保存缓存
    await saveCache(cacheKey, analysisResult, version, userType);
    
    // 4. 保存分析记录
    await saveAnalysisRecord(openid, {
      userType,
      version,
      answers,
      result: analysisResult
    });
    
    return {
      status: 'completed',
      analysis: analysisResult,
      cacheKey: cacheKey
    };
    
  } catch (error) {
    console.error('分析失败', error);
    
    // 失败时使用fallback
    const fallbackResult = generateFallbackAnalysis(userType, version);
    
    return {
      status: 'completed',
      analysis: fallbackResult,
      fromFallback: true
    };
  }
};

// 生成缓存Key
function generateCacheKey(answers) {
  const crypto = require('crypto');
  const sortedAnswers = Object.entries(answers)
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .map(([k, v]) => `${k}:${v}`)
    .join('+');
  
  return crypto
    .createHash('md5')
    .update(sortedAnswers)
    .digest('hex');
}

// 检查缓存
async function checkCache(cacheKey, version, userType) {
  try {
    const cacheCollection = db.collection('analysis_cache');
    const result = await cacheCollection
      .where({
        cacheKey: cacheKey,
        version: version,
        userType: userType
      })
      .get();
    
    if (result.data.length > 0) {
      return result.data[0].result;
    }
    
    return null;
  } catch (error) {
    console.error('检查缓存失败', error);
    return null;
  }
}

// 保存缓存
async function saveCache(cacheKey, result, version, userType) {
  try {
    const cacheCollection = db.collection('analysis_cache');
    await cacheCollection.add({
      cacheKey: cacheKey,
      version: version,
      userType: userType,
      result: result,
      createdAt: new Date(),
      updatedAt: new Date()
    });
  } catch (error) {
    console.error('保存缓存失败', error);
  }
}

// 生成分析
async function generateAnalysis(userType, answers, questions, version) {
  // 简单的评分算法（原项目算法简化版）
  const scores = calculateIndustryScores(userType, answers);
  
  // 排序并取前5个
  const topIndustries = Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  
  // 构建推荐列表
  const industries = topIndustries.map(([name, score], index) => {
    const industryData = INDUSTRY_DATABASE[name] || {
      trends: [],
      hot_roles: []
    };
    
    return {
      name: name,
      match: `${Math.min(100, Math.round(score))}%`,
      description: generateDescription(name, userType, industryData),
      roles: industryData.hot_roles || []
    };
  });
  
  // 生成摘要
  const summary = generateSummary(userType, industries, version);
  
  // 构建完整结果
  const result = {
    summary: summary,
    industries: industries,
    details: version !== 'light' ? 
      generateDetails(userType, industries, answers) : null,
    actionPlan: version !== 'light' ? 
      generateActionPlan(userType, industries) : null
  };
  
  return result;
}

// 简单评分
function calculateIndustryScores(userType, answers) {
  const scores = {};
  
  // 给每个行业基础分
  Object.keys(INDUSTRY_DATABASE).forEach(industry => {
    scores[industry] = 50; // 基础分
  });
  
  // 简单规则（可扩展）
  const userProfession = Object.values(answers)[0];
  
  if (userProfession === 'tech_rd' || userProfession === 'science') {
    scores["人工智能/大数据"] += 30;
    scores["互联网/IT"] += 25;
  }
  
  if (userProfession === 'tech_medical' || userProfession === 'medicine') {
    scores["医疗健康"] += 30;
  }
  
  return scores;
}

// 生成描述
function generateDescription(name, userType, data) {
  const descriptions = {
    1: `这是一个适合转型的稳定行业。${data.growth || '该行业'}前景良好。`,
    2: `这是一个适合应届生发展的行业。${data.growth || '该行业'}处于上升期。`,
    3: `这是一个长期稳定的行业，适合孩子未来发展。`
  };
  
  return descriptions[userType] || `该行业${data.growth || '发展稳定'}。`;
}

// 生成摘要
function generateSummary(userType, industries, version) {
  const summaries = {
    1: `根据您的情况，推荐考虑${industries[0]?.name || '相关'}行业，这是一个不错的转型方向。`,
    2: `基于您的背景，${industries[0]?.name || '相关'}行业比较适合您的发展。`,
    3: `综合考虑，${industries[0]?.name || '相关'}是一个适合孩子的长期稳定方向。`
  };
  
  return summaries[userType] || '根据您的情况，已为您推荐了适合的行业。';
}

// 生成详细分析
function generateDetails(userType, industries, answers) {
  return `基于您提供的信息，我们对${industries.length}个行业进行了匹配分析。`;
}

// 生成行动计划
function generateActionPlan(userType, industries) {
  return [
    {
      title: '了解行业',
      description: `深入了解${industries[0]?.name || '推荐'}行业的基础知识。`
    },
    {
      title: '学习技能',
      description: '制定学习计划，补充必要的技能。'
    },
    {
      title: '人脉拓展',
      description: '认识行业内的人，建立连接。'
    }
  ];
}

// Fallback分析
function generateFallbackAnalysis(userType, version) {
  const fallbackIndustries = [
    { name: '互联网/IT', match: '85%', description: '发展前景良好的行业' },
    { name: '医疗健康', match: '75%', description: '长期稳定的行业' }
  ];
  
  return {
    summary: '根据您的情况，为您推荐以下行业方向。',
    industries: fallbackIndustries,
    details: version !== 'light' ? '详细分析内容（Fallback）' : null,
    actionPlan: version !== 'light' ? [
      { title: '第一步', description: '了解行业' },
      { title: '第二步', description: '学习技能' }
    ] : null
  };
}

// 保存分析记录
async function saveAnalysisRecord(openid, data) {
  try {
    const recordsCollection = db.collection('analysis_records');
    await recordsCollection.add({
      openid: openid,
      userType: data.userType,
      version: data.version,
      answers: data.answers,
      result: data.result,
      createdAt: new Date()
    });
  } catch (error) {
    console.error('保存记录失败', error);
  }
}
