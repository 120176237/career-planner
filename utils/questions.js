// 题目配置
const QUESTIONS = {
  // 轻量版题目
  light: {
    1: [
      // 30-40岁转型群体题目
      {
        id: 1,
        text: '您的最高学历是？',
        type: 'single',
        options: [
          { label: '大专以下', value: 'below_college' },
          { label: '大专', value: 'college' },
          { label: '本科', value: 'bachelor' },
          { label: '硕士', value: 'master' },
          { label: '博士', value: 'doctor' }
        ]
      },
      {
        id: 2,
        text: '您目前的职业背景是？',
        type: 'single',
        options: [
          { label: '技术研发', value: 'tech_rd' },
          { label: '生产制造', value: 'tech_prod' },
          { label: '医疗健康', value: 'tech_medical' },
          { label: '金融财务', value: 'tech_finance' },
          { label: '教育培训', value: 'tech_edu' },
          { label: '市场营销', value: 'market' },
          { label: '职能管理', value: 'manage' },
          { label: '媒体创意', value: 'media' },
          { label: '体力劳动', value: 'labor' },
          { label: '服务类', value: 'service' }
        ]
      },
      {
        id: 3,
        text: '您的专业技能领域是？',
        type: 'single',
        options: [
          { label: '数据分析/AI', value: 'data_ai' },
          { label: '硬件/嵌入式', value: 'hardware' },
          { label: '财务/法务', value: 'finance_law' },
          { label: '运营/项目管理', value: 'operation' },
          { label: '沟通/销售', value: 'sales' },
          { label: '内容/设计', value: 'creative' },
          { label: '直播/电商', value: 'ecommerce' },
          { label: '快递/配送', value: 'delivery' }
        ]
      }
    ],
    2: [
      // 应届生题目
      {
        id: 1,
        text: '您的最高学历是？',
        type: 'single',
        options: [
          { label: '大专以下', value: 'below_college' },
          { label: '大专', value: 'college' },
          { label: '本科', value: 'bachelor' },
          { label: '硕士', value: 'master' },
          { label: '博士', value: 'doctor' }
        ]
      },
      {
        id: 2,
        text: '您的专业属于？',
        type: 'single',
        options: [
          { label: '理工科', value: 'science' },
          { label: '文科', value: 'arts' },
          { label: '商科', value: 'business' },
          { label: '艺术/创意', value: 'art' },
          { label: '无专业', value: 'none' }
        ]
      },
      {
        id: 3,
        text: '您的外语水平是？',
        type: 'single',
        options: [
          { label: '英语+小语种', value: 'english_plus' },
          { label: '英语精通', value: 'english_pro' },
          { label: '英语一般', value: 'english_ok' },
          { label: '不擅长', value: 'english_poor' }
        ]
      }
    ],
    3: [
      // 家长版题目
      {
        id: 1,
        text: '孩子的类型偏向？',
        type: 'single',
        options: [
          { label: '理科/工科', value: 'science' },
          { label: '文科/商科', value: 'arts' },
          { label: '艺术/创意', value: 'art' },
          { label: '职业技术', value: 'vocational' }
        ]
      },
      {
        id: 2,
        text: '最看重什么？',
        type: 'single',
        options: [
          { label: '就业前景', value: 'employment' },
          { label: '兴趣意愿', value: 'interest' },
          { label: '稳定安全', value: 'stable' },
          { label: '薪资潜力', value: 'salary' }
        ]
      },
      {
        id: 3,
        text: '对出国的态度是？',
        type: 'single',
        options: [
          { label: '考虑出国', value: 'consider' },
          { label: '不确定', value: 'not_sure' },
          { label: '不考虑', value: 'no' }
        ]
      }
    ]
  },
  
  // 深度版题目
  deep: {
    1: [
      // 30-40岁转型群体深度版题目
      {
        id: 1,
        text: '您的最高学历是？',
        type: 'single',
        options: [
          { label: '大专以下', value: 'below_college' },
          { label: '大专', value: 'college' },
          { label: '本科', value: 'bachelor' },
          { label: '硕士', value: 'master' },
          { label: '博士', value: 'doctor' }
        ]
      },
      {
        id: 2,
        text: '您目前的职业背景是？',
        type: 'single',
        options: [
          { label: '技术研发', value: 'tech_rd' },
          { label: '生产制造', value: 'tech_prod' },
          { label: '医疗健康', value: 'tech_medical' },
          { label: '金融财务', value: 'tech_finance' },
          { label: '教育培训', value: 'tech_edu' },
          { label: '市场营销', value: 'market' },
          { label: '职能管理', value: 'manage' },
          { label: '媒体创意', value: 'media' },
          { label: '体力劳动', value: 'labor' },
          { label: '服务类', value: 'service' }
        ]
      },
      {
        id: 3,
        text: '您的专业技能领域是？',
        type: 'single',
        options: [
          { label: '数据分析/AI', value: 'data_ai' },
          { label: '硬件/嵌入式', value: 'hardware' },
          { label: '财务/法务', value: 'finance_law' },
          { label: '运营/项目管理', value: 'operation' },
          { label: '沟通/销售', value: 'sales' },
          { label: '内容/设计', value: 'creative' },
          { label: '直播/电商', value: 'ecommerce' },
          { label: '快递/配送', value: 'delivery' }
        ]
      },
      {
        id: 4,
        text: '您的工作年限是？',
        type: 'single',
        options: [
          { label: '1-3年', value: '1-3' },
          { label: '3-5年', value: '3-5' },
          { label: '5-10年', value: '5-10' },
          { label: '10年以上', value: '10+' }
        ]
      },
      {
        id: 5,
        text: '您的经济压力程度？',
        type: 'single',
        options: [
          { label: '很大', value: 'high' },
          { label: '一般', value: 'medium' },
          { label: '较小', value: 'low' }
        ]
      },
      {
        id: 6,
        text: '您的学习意愿？',
        type: 'single',
        options: [
          { label: '很强，愿意投入大量时间', value: 'high' },
          { label: '一般，每天能学习1-2小时', value: 'medium' },
          { label: '较弱，不太想学习新东西', value: 'low' }
        ]
      },
      {
        id: 7,
        text: '您的兴趣方向是？',
        type: 'single',
        options: [
          { label: 'AI大模型', value: 'ai' },
          { label: '新能源/储能', value: 'energy' },
          { label: '出海/跨境', value: 'global' },
          { label: '医疗健康', value: 'health' },
          { label: '金融科技', value: 'fintech' },
          { label: '机器自动化', value: 'robotics' },
          { label: '低空经济', value: 'aviation' },
          { label: '不确定', value: 'not_sure' }
        ]
      },
      {
        id: 8,
        text: '您的英语水平？',
        type: 'single',
        options: [
          { label: '精通', value: 'pro' },
          { label: '良好', value: 'good' },
          { label: '一般', value: 'ok' },
          { label: '较差', value: 'poor' }
        ]
      }
    ],
    2: [
      // 应届生深度版题目
      {
        id: 1,
        text: '您的最高学历是？',
        type: 'single',
        options: [
          { label: '大专以下', value: 'below_college' },
          { label: '大专', value: 'college' },
          { label: '本科', value: 'bachelor' },
          { label: '硕士', value: 'master' },
          { label: '博士', value: 'doctor' }
        ]
      },
      {
        id: 2,
        text: '您的专业属于？',
        type: 'single',
        options: [
          { label: '理工科', value: 'science' },
          { label: '文科', value: 'arts' },
          { label: '商科', value: 'business' },
          { label: '艺术/创意', value: 'art' },
          { label: '无专业', value: 'none' }
        ]
      },
      {
        id: 3,
        text: '您的外语水平是？',
        type: 'single',
        options: [
          { label: '英语+小语种', value: 'english_plus' },
          { label: '英语精通', value: 'english_pro' },
          { label: '英语一般', value: 'english_ok' },
          { label: '不擅长', value: 'english_poor' }
        ]
      },
      {
        id: 4,
        text: '您的地域偏好？',
        type: 'single',
        options: [
          { label: '一线城市', value: 'first_tier' },
          { label: '新一线城市', value: 'new_first' },
          { label: '二线城市', value: 'second_tier' },
          { label: '回老家', value: 'hometown' },
          { label: '无所谓', value: 'any' }
        ]
      },
      {
        id: 5,
        text: '您的编程能力？',
        type: 'single',
        options: [
          { label: '精通', value: 'pro' },
          { label: '熟练', value: 'good' },
          { label: '一般', value: 'ok' },
          { label: '不会', value: 'none' }
        ]
      },
      {
        id: 6,
        text: '您对5年后的期望？',
        type: 'single',
        options: [
          { label: '大公司', value: 'big_company' },
          { label: '创业', value: 'startup' },
          { label: '出海', value: 'global' },
          { label: '技术专家', value: 'expert' },
          { label: '小事业', value: 'small_business' },
          { label: '没想清楚', value: 'not_sure' }
        ]
      }
    ],
    3: [
      // 家长版深度版题目
      {
        id: 1,
        text: '孩子的类型偏向？',
        type: 'single',
        options: [
          { label: '理科/工科', value: 'science' },
          { label: '文科/商科', value: 'arts' },
          { label: '艺术/创意', value: 'art' },
          { label: '职业技术', value: 'vocational' }
        ]
      },
      {
        id: 2,
        text: '最看重什么？',
        type: 'single',
        options: [
          { label: '就业前景', value: 'employment' },
          { label: '兴趣意愿', value: 'interest' },
          { label: '稳定安全', value: 'stable' },
          { label: '薪资潜力', value: 'salary' }
        ]
      },
      {
        id: 3,
        text: '对出国的态度是？',
        type: 'single',
        options: [
          { label: '考虑出国', value: 'consider' },
          { label: '不确定', value: 'not_sure' },
          { label: '不考虑', value: 'no' }
        ]
      },
      {
        id: 4,
        text: '家庭年收入？',
        type: 'single',
        options: [
          { label: '50万+', value: '50+' },
          { label: '30-50万', value: '30-50' },
          { label: '15-30万', value: '15-30' },
          { label: '15万以下', value: 'below_15' }
        ]
      },
      {
        id: 5,
        text: '希望孩子发展的城市？',
        type: 'single',
        options: [
          { label: '一线', value: 'first_tier' },
          { label: '新一线', value: 'new_first' },
          { label: '老家', value: 'hometown' },
          { label: '无所谓', value: 'any' },
          { label: '海外', value: 'overseas' }
        ]
      }
    ]
  }
};

// 获取题目
function getQuestions(userType, version = 'light') {
  const userTypeKey = String(userType);
  const versionQuestions = QUESTIONS[version];
  if (versionQuestions && versionQuestions[userTypeKey]) {
    return versionQuestions[userTypeKey];
  }
  return [];
}

module.exports = {
  QUESTIONS,
  getQuestions
};
