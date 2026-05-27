// API 基地址配置（开发环境）
var API_BASE = '';

const quizData = {
  1: {
    title: '30-40岁职业趣味测试',
    questions: [
      { text: '你的年龄区间是？', options: [{ label: '30-35岁', value: 'a' }, { label: '35-40岁', value: 'b' }, { label: '40岁以上', value: 'c' }] },
      { text: '你的最高学历是？', options: [{ label: '大专以下', value: '大专以下' }, { label: '大专', value: '大专' }, { label: '本科', value: '本科' }, { label: '硕士', value: '硕士' }, { label: '博士', value: '博士' }] },
      { text: '你目前的职业背景属于？', options: [
        { label: '技术研发类（IT/互联网/制造/建筑）', value: 'tech_rd' }, { label: '生产制造类（工厂/工艺/质量/供应链）', value: 'tech_prod' },
        { label: '医疗健康类（医生/护士/健康管理）', value: 'tech_medical' }, { label: '金融财务类（银行/证券/会计/审计）', value: 'tech_finance' },
        { label: '教育培训类（教师/培训/咨询/研究）', value: 'tech_edu' }, { label: '市场营销类（销售/运营/市场/BD）', value: 'market' },
        { label: '职能管理类（HR/行政/采购/法务）', value: 'manage' }, { label: '媒体创意类（设计/文案/内容/摄影）', value: 'media' },
        { label: '体力/劳动类（工厂/建筑/搬运/安装）', value: 'labor' }, { label: '服务类（餐饮/酒店/美容/快递/外卖）', value: 'service' },
        { label: '销售/零售类（店员/导购/摊贩/客服）', value: 'retail' }, { label: '个体经营（小生意/电商/地摊/微商）', value: 'self_emp' },
        { label: '司机/运输类（货车/出租/货运）', value: 'driver' }, { label: '农林牧渔类（务农/养殖/林果/渔业）', value: 'agri' },
        { label: '保安/保洁/家政/物业类', value: 'support' }, { label: '自由职业/打零工（没固定工作）', value: 'gig' }
      ]},
      { text: '你目前的经济压力如何？', options: [{ label: '有房贷/家庭开支，必须保持收入', value: 'high', desc: '需要过渡方案' }, { label: '有一定积蓄，可以承受短期收入下降', value: 'medium', desc: '可以直接转型' }, { label: '经济压力较小，可以慢慢探索', value: 'low', desc: '可以系统性规划' }] },
      { text: '你对转型后收入的期待是？', options: [{ label: '不低于现有水平', value: 'keep', desc: '难度较高' }, { label: '可以接受一定幅度的下降', value: 'accept', desc: '更灵活' }, { label: '收入不是首要考虑，稳定即可', value: 'stable', desc: '求稳' }] },
      { text: '你更倾向于哪种转型方式？', options: [{ label: '先找过渡工作，同时准备转型', value: '过渡+转型', desc: '骑驴找马' }, { label: '直接学习新技能，转型到目标行业', value: '直接转型', desc: 'all in' }, { label: '不确定，需要分析后决定', value: '待定', desc: '需要建议' }] },
      { text: '你目前的编程/代码能力？', options: [{ label: '精通（可独立完成项目）', value: 'pro' }, { label: '熟练（能完成常规开发）', value: 'mid' }, { label: '一般（了解基础）', value: 'basic' }, { label: '不会或很少接触', value: 'none' }] },
      { text: '你目前的专业技能/资历？', options: [
        { label: '数据分析/AI/机器学习', value: 'data_ai' }, { label: '硬件/嵌入式/机械/电气', value: 'hardware' },
        { label: '财务/法务/合规等专业资质', value: 'professional' }, { label: '运营/项目管理/团队协调', value: 'manage_skill' },
        { label: '沟通/销售/市场开拓', value: 'sales' }, { label: '内容创作/设计/策划', value: 'creative' },
        { label: '直播带货/短视频/电商运营', value: 'ecommerce' }, { label: '快递/外卖配送', value: 'delivery' },
        { label: '货运/客运/网约车', value: 'transport' }, { label: '餐饮/零售/服务业', value: 'service' },
        { label: '建筑/装修/水电工', value: 'construction' }, { label: '没什么技能/纯体力劳动', value: 'labor' }
      ]},
      { text: '你目前对新行业的了解程度？', options: [{ label: '有明确目标，已经开始准备', value: 'clear' }, { label: '有几个方向在考虑', value: 'some' }, { label: '完全不知道从哪开始', value: 'lost' }] },
      { text: '如果只能选一个关键词来描述你的现状，你会选？', options: [{ label: '焦虑：不知道下一步怎么走', value: 'anxious' }, { label: '迷茫：方向太多，不知道哪个对', value: 'confused' }, { label: '紧迫：必须尽快找到出路', value: 'urgent' }, { label: '理性：想清楚再行动', value: 'rational' }] }
    ]
  },
  2: {
    title: '应届/毕业学生趣味测试',
    questions: [
      { text: '你的学历背景是？', options: [{ label: '大专以下', value: 'high_school' }, { label: '大专', value: 'college' }, { label: '本科', value: 'bachelor' }, { label: '硕士', value: 'master' }, { label: '博士', value: 'phd' }] },
      { text: '你的专业属于？', options: [
        { label: '理科/工科（CS/工程/医学/金融等）', value: 'science' }, { label: '文科（文学/法学/传媒/历史/哲学等）', value: 'arts' },
        { label: '商科（管理/会计/营销等）', value: 'business' }, { label: '技校/职高/中专（学技术的）', value: 'vocational' },
        { label: '没什么专业（初高中毕业）', value: 'none' }, { label: '服务业技能（烹饪/美容/汽修/电工等）', value: 'skill_based' }
      ]},
      { text: '你目前最看重什么？', options: [{ label: '长期稳定发展', value: 'stable' }, { label: '持续晋升成长', value: 'grow' }, { label: '工作与生活平衡', value: 'balance' }, { label: '实现个人价值', value: 'value' }] },
      { text: '你对出海/国际化方向的态度？', options: [{ label: '很感兴趣，愿意考虑', value: 'interest' }, { label: '一般，主要看机会', value: 'maybe' }, { label: '暂时不考虑', value: 'not_now' }] },
      { text: '你掌握的外语水平？', options: [{ label: '英语精通 + 一门小语种', value: 'bilingual' }, { label: '英语精通', value: 'english' }, { label: '英语一般', value: 'basic' }, { label: '对外语不擅长', value: 'none' }] },
      { text: '你对AI工具的使用情况？', options: [{ label: '经常使用，能提高效率', value: 'pro' }, { label: '偶尔使用', value: 'basic' }, { label: '很少使用', value: 'rare' }] },
      { text: '5年后你希望自己在做什么？', options: [
        { label: '在一家稳定的大公司发展', value: 'bigcompany' }, { label: '自己创业或做自由职业', value: 'entrepreneur' },
        { label: '在出海企业工作', value: 'overseas' }, { label: '还没想清楚', value: 'unknown' },
        { label: '自己当老板（小生意/店铺/工作室）', value: 'own_business' }, { label: '有一技之长（师傅/技师/工匠）', value: 'skilled_worker' },
        { label: '有稳定工作能养家就行', value: 'stable_life' }, { label: '能比现在过得好就满足了', value: 'better_life' }
      ]},
      { text: '如果给你现在的状态贴一个标签，你选？', options: [{ label: '方向明确，但在犹豫', value: 'hesitate' }, { label: '有几个方向在纠结', value: 'confused' }, { label: '完全不知道想做什么', value: 'lost' }, { label: '有想法但担心不现实', value: 'worried' }] }
    ]
  },
  3: {
    title: '学生家长趣味测试',
    questions: [
      { text: '您的孩子目前处于哪个学习阶段？', options: [{ label: '小学（1-6年级）', value: 'primary' }, { label: '初中（7-9年级）', value: 'middle' }, { label: '高中（10-12年级）', value: 'high' }] },
      { text: '您孩子的成绩大概在？', options: [{ label: '尖子生水平', value: 'top' }, { label: '中上水平', value: 'good' }, { label: '中等水平', value: 'normal' }, { label: '中下/需要更多关注', value: 'struggle' }] },
      { text: '您孩子属于哪种类型？', options: [{ label: '理科/工科（数理化强）', value: 'science' }, { label: '文科/商科（语言表达强）', value: 'arts' }, { label: '艺术/体育/创意类', value: 'creative' }, { label: '职业技术/动手型', value: 'vocational' }] },
      { text: '选择专业/方向时最看重什么？', options: [{ label: '未来就业前景', value: 'job' }, { label: '孩子的兴趣和意愿', value: 'interest' }, { label: '稳定性和安全感', value: 'stable' }, { label: '薪资潜力', value: 'salary' }] },
      { text: '对出国的态度？', options: [{ label: '考虑出国读研/读本科/中学', value: 'consider' }, { label: '不确定，看情况和时机', value: 'maybe' }, { label: '不考虑出国', value: 'not_now' }] },
      { text: '对人民币升值的看法？', options: [{ label: '会影响我们的决策（留学/移民等）', value: 'affect' }, { label: '有一定影响，但不具决定性', value: 'some' }, { label: '影响不大，主要看国内发展', value: 'less' }] },
      { text: '对孩子的职业期待？', options: [{ label: '希望孩子成为专业人士/专家', value: 'expert' }, { label: '希望孩子有商业头脑', value: 'business' }, { label: '希望孩子稳定生活就好', value: 'stable' }, { label: '尊重孩子的选择', value: 'respect' }] },
      { text: '对AI技术冲击的担忧程度？', options: [{ label: '很担心，想选不容易被替代的方向', value: 'worried' }, { label: '有些担心，会作为参考因素', value: 'some' }, { label: '相信人的价值，不太担心', value: 'calm' }] },
      { text: '如果用一句话描述现在的状态？', options: [{ label: '信息太多，不知道听谁的', value: 'info_overload' }, { label: '孩子没想法，完全不知道选什么', value: 'child_lost' }, { label: '有想法但和孩子的意见不一致', value: 'conflict' }, { label: '有大致方向，想确认是否正确', value: 'confirm' }] }
    ]
  }
};

var quizDataDeep = {
  1: {
    title: '30-40岁职业趣味测试（深度版）',
    questions: [
      { text: '你的年龄区间是？', options: [{ label: '30-32岁', value: '30_32' }, { label: '33-35岁', value: '33_35' }, { label: '36-38岁', value: '36_38' }, { label: '39-40岁', value: '39_40' }, { label: '40岁以上', value: '40_plus' }] },
      { text: '你的最高学历是？', options: [{ label: '高中/中专以下', value: 'below_high' }, { label: '大专', value: 'college' }, { label: '本科', value: 'bachelor' }, { label: '硕士', value: 'master' }, { label: '博士', value: 'phd' }] },
      { text: '你目前的职业背景属于哪类？', options: [{ label: '技术研发类（IT/互联网/制造/建筑/工程）', value: 'tech_rd' }, { label: '生产运营类（工厂/工艺/质量/供应链/采购）', value: 'tech_prod' }, { label: '医疗健康类（医生/护士/健康管理/药企）', value: 'tech_medical' }, { label: '金融财务类（银行/证券/会计/审计/投融资）', value: 'tech_finance' }, { label: '教育培训类（教师/培训/咨询/研究）', value: 'tech_edu' }, { label: '市场营销类（销售/运营/市场/BD/公关）', value: 'market' }, { label: '职能管理类（HR/行政/法务/董秘）', value: 'manage' }, { label: '媒体创意类（设计/文案/内容/摄影/影视）', value: 'media' }, { label: '体力/劳动类（工厂/建筑/搬运/安装）', value: 'labor' }, { label: '服务类（餐饮/酒店/美容/快递/外卖）', value: 'service' }, { label: '销售/零售类（店员/导购/摊贩/客服）', value: 'retail' }, { label: '自由职业/打零工', value: 'gig' }] },
      { text: '你目前的工作状态是？', options: [{ label: '在职但担心被裁员', value: 'employed_worried' }, { label: '已被裁员/失业', value: 'laid_off' }, { label: '主动离职想转型', value: 'resigned' }, { label: '收入大幅下降想改变', value: 'income_drop' }, { label: '行业明显下行', value: 'industry_down' }] },
      { text: '你目前的家庭状况？', options: [{ label: '单身无孩子', value: 'single' }, { label: '已婚无孩子', value: 'married_no_kids' }, { label: '已婚有孩子（12岁以下）', value: 'kids_young' }, { label: '已婚有孩子（12岁以上）', value: 'kids_older' }, { label: '单亲家庭', value: 'single_parent' }] },
      { text: '你目前的经济压力如何？', options: [{ label: '有高额房贷/必须保持收入', value: 'high' }, { label: '有普通房贷/养家压力大', value: 'medium_high' }, { label: '有一定积蓄，可以承受短期收入下降', value: 'medium' }, { label: '经济压力较小，可以慢慢探索', value: 'low' }] },
      { text: '你目前的月薪（税后）大概是多少？', options: [{ label: '5000以下', value: 'under_5k' }, { label: '5000-10000', value: '5k_10k' }, { label: '10000-20000', value: '10k_20k' }, { label: '20000-40000', value: '20k_40k' }, { label: '40000以上', value: 'above_40k' }] },
      { text: '你对转型后收入的期待是？', options: [{ label: '不低于现有水平', value: 'keep' }, { label: '可以接受20%以内的下降', value: 'accept_20' }, { label: '可以接受20-40%的下降', value: 'accept_40' }, { label: '收入不是首要考虑，稳定即可', value: 'stable' }] },
      { text: '你更倾向于哪种转型方式？', options: [{ label: '先找过渡工作，同时准备转型', value: '过渡+转型' }, { label: '直接学习新技能，转型到目标行业', value: '直接转型' }, { label: '不确定，需要分析后决定', value: '待定' }] },
      { text: '你目前的编程/代码能力？', options: [{ label: '精通（可独立完成项目）', value: 'pro' }, { label: '熟练（能完成常规开发）', value: 'mid' }, { label: '一般（了解基础）', value: 'basic' }, { label: '不会或很少接触', value: 'none' }] },
      { text: '你目前的专业技能/资历？', options: [{ label: '数据分析/AI/机器学习', value: 'data_ai' }, { label: '硬件/嵌入式/机械/电气/PLC', value: 'hardware' }, { label: '财务/法务/合规等专业资质', value: 'professional' }, { label: '运营/项目管理/PMP', value: 'manage_skill' }, { label: '沟通/销售/市场开拓', value: 'sales' }, { label: '内容创作/设计/策划', value: 'creative' }, { label: '直播带货/短视频/电商运营', value: 'ecommerce' }, { label: '物流/仓储/供应链管理', value: 'logistics' }, { label: '餐饮/零售/服务业管理', value: 'service_manage' }, { label: '建筑/装修/水电工', value: 'construction' }, { label: '驾驶/运输/特种设备', value: 'driving' }, { label: '没什么技能/纯体力劳动', value: 'labor' }] },
      { text: '你目前对新行业的了解程度？', options: [{ label: '有明确目标，已经开始准备', value: 'clear' }, { label: '有几个方向在考虑', value: 'some' }, { label: '完全不知道从哪开始', value: 'lost' }] },
      { text: '你愿意为转型投入多少时间和金钱？', options: [{ label: '愿意花1-2年系统学习', value: 'long_term' }, { label: '可以投入3-6个月', value: 'medium_term' }, { label: '希望1-2个月内快速转型', value: 'quick' }, { label: '不想投入太多，边做边看', value: 'minimal' }] },
      { text: '你的英语水平？', options: [{ label: '精通（可作为工作语言）', value: 'fluent' }, { label: '良好（能读写英文文档）', value: 'good' }, { label: '一般（能简单沟通）', value: 'basic' }, { label: '较差', value: 'poor' }] },
      { text: '你能否接受出差或外派？', options: [{ label: '可以接受频繁出差', value: 'frequent' }, { label: '可以接受偶尔出差', value: 'occasional' }, { label: '希望稳定在本地', value: 'local' }, { label: '可以接受异地工作', value: 'relocate' }] },
      { text: '你对以下哪个方向最感兴趣？', options: [{ label: 'AI/大模型/机器学习', value: 'interest_ai' }, { label: '新能源/储能/电动车', value: 'interest_energy' }, { label: '出海/跨境电商/全球化', value: 'interest_overseas' }, { label: '医疗健康/生物医药', value: 'interest_medical' }, { label: '金融科技/区块链', value: 'interest_fintech' }, { label: '机器人/自动化/智能制造', value: 'interest_robot' }, { label: '低空经济/无人机/航天', value: 'interest_aero' }, { label: '暂时不确定', value: 'interest_unknown' }] },
      { text: '如果只能选一个关键词来描述你的现状', options: [{ label: '焦虑：不知道下一步怎么走', value: 'anxious' }, { label: '迷茫：方向太多，不知道哪个对', value: 'confused' }, { label: '紧迫：必须尽快找到出路', value: 'urgent' }, { label: '理性：想清楚再行动', value: 'rational' }, { label: '疲惫：已经尝试过但没成功', value: 'exhausted' }] },
      { text: '你之前有过转型/转行的经历吗？', options: [{ label: '有成功转型经历', value: 'success' }, { label: '有尝试但未成功的经历', value: 'failed' }, { label: '没有，这是第一次', value: 'first' }] },
      { text: '你的抗压能力如何？', options: [{ label: '很强，可以承受很大压力', value: 'high' }, { label: '一般，能应对正常工作压力', value: 'medium' }, { label: '较弱，需要相对轻松的环境', value: 'low' }] },
      { text: '你希望转型后的工作节奏是？', options: [{ label: '996/高强度也可以接受', value: 'intense' }, { label: '正常朝九晚五', value: 'normal' }, { label: '弹性工作，可以远程', value: 'flexible' }, { label: '希望工作生活平衡', value: 'balance' }] },
      { text: '你对考取职业资格证书的态度？', options: [{ label: '愿意投入时间和金钱考取', value: 'willing' }, { label: '可以考，但不想花太多时间', value: 'maybe' }, { label: '不想考证，更看重实际经验', value: 'unwilling' }] },
      { text: '你的人脉资源情况？', options: [{ label: '有行业人脉，可以帮忙推荐', value: 'rich' }, { label: '有一些人脉，但不确定能否用到', value: 'some' }, { label: '人脉较少，主要靠自己', value: 'poor' }] },
      { text: '你的家庭支持度如何？', options: [{ label: '家人非常支持，愿意一起承担风险', value: 'full' }, { label: '家人一般支持，有一定顾虑', value: 'partial' }, { label: '家人不太支持，有经济顾虑', value: 'limited' }] },
      { text: '你对自己的学习能力有信心吗？', options: [{ label: '很有信心，学习能力强', value: 'confident' }, { label: '一般，需要时间适应', value: 'normal' }, { label: '担心学习能力跟不上', value: 'worried' }] },
      { text: '你最担心转型过程中的什么？', options: [{ label: '收入断档，还不起贷款', value: 'fear_income' }, { label: '学习时间太长，年龄歧视', value: 'fear_age' }, { label: '选错方向，白费功夫', value: 'fear_wrong' }, { label: '家庭不支持，压力太大', value: 'fear_family' }, { label: '不确定能不能成功', value: 'fear_uncertain' }] }
    ]
  },
  2: {
    title: '应届/毕业学生趣味测试（深度版）',
    questions: [
      { text: '你的学历背景是？', options: [{ label: '高中/中专以下', value: 'below_high' }, { label: '大专', value: 'college' }, { label: '本科', value: 'bachelor' }, { label: '硕士', value: 'master' }, { label: '博士', value: 'phd' }] },
      { text: '你的专业属于？', options: [{ label: '计算机/软件/AI相关', value: 'cs' }, { label: '其他理工科（机械/电子/化工等）', value: 'engineering' }, { label: '医学/生命科学/药学', value: 'medical' }, { label: '金融/经济/会计', value: 'finance' }, { label: '文科（文学/法学/传媒/历史）', value: 'arts' }, { label: '商科（管理/营销/人力资源）', value: 'business' }, { label: '艺术/设计/影视', value: 'art' }, { label: '师范/教育', value: 'edu' }, { label: '技校/职高/学技术的', value: 'vocational' }, { label: '其他/专业不对口', value: 'other' }] },
      { text: '你目前的学校档次？', options: [{ label: '985/211高校', value: 'top' }, { label: '普通一本', value: 'first_class' }, { label: '二本/独立学院', value: 'second_class' }, { label: '大专/高职', value: 'college' }, { label: '技校/职高', value: 'vocational' }] },
      { text: '你的毕业时间？', options: [{ label: '今年应届毕业生', value: 'this_year' }, { label: '毕业1年内', value: 'within_1' }, { label: '毕业1-3年', value: '1_3_years' }, { label: '毕业3年以上', value: 'above_3' }] },
      { text: '你目前最看重什么？', options: [{ label: '长期稳定发展', value: 'stable' }, { label: '持续晋升成长', value: 'grow' }, { label: '工作与生活平衡', value: 'balance' }, { label: '实现个人价值', value: 'value' }, { label: '高收入', value: 'high_salary' }] },
      { text: '你对工作的地域偏好？', options: [{ label: '一线城市（北上广深）', value: 'tier1' }, { label: '新一线城市（杭州/成都等）', value: 'new_tier1' }, { label: '二线城市', value: 'tier2' }, { label: '回老家/小城市', value: 'hometown' }, { label: '无所谓，哪里有机会去哪', value: 'anywhere' }] },
      { text: '你对出海/国际化方向的态度？', options: [{ label: '很感兴趣，愿意去海外工作', value: 'eager' }, { label: '感兴趣，但暂时不考虑', value: 'interest' }, { label: '一般，主要看机会', value: 'maybe' }, { label: '暂时不考虑', value: 'not_now' }] },
      { text: '你掌握的外语水平？', options: [{ label: '英语精通 + 一门小语种', value: 'bilingual' }, { label: '英语精通（CET-6/雅思6.5+）', value: 'english' }, { label: '英语一般（CET-4水平）', value: 'basic' }, { label: '对外语不擅长', value: 'none' }] },
      { text: '你对AI工具的使用情况？', options: [{ label: '精通，能用AI提高效率', value: 'pro' }, { label: '经常使用，了解主流工具', value: 'regular' }, { label: '偶尔使用', value: 'basic' }, { label: '很少使用', value: 'rare' }] },
      { text: '你有哪些实习经历？', options: [{ label: '有大厂/知名企业实习', value: 'big_company' }, { label: '有普通企业实习', value: 'normal_company' }, { label: '有创业公司/小公司实习', value: 'startup' }, { label: '没有实习经历', value: 'none' }] },
      { text: '你有哪些项目经历/作品？', options: [{ label: '有完整的项目作品集', value: 'portfolio' }, { label: '有一些项目经历', value: 'some' }, { label: '有课程项目经历', value: 'course' }, { label: '没有项目经历', value: 'none' }] },
      { text: '你的编程能力？', options: [{ label: '精通（可独立开发）', value: 'pro' }, { label: '熟练（能完成开发任务）', value: 'mid' }, { label: '一般（了解基础）', value: 'basic' }, { label: '不会/不相关', value: 'none' }] },
      { text: '你的数据分析能力？', options: [{ label: '精通（SQL/Python/BI工具）', value: 'pro' }, { label: '一般（会用Excel/基础统计）', value: 'basic' }, { label: '较弱', value: 'weak' }, { label: '不相关', value: 'none' }] },
      { text: '你的沟通表达能力？', options: [{ label: '很强，善于表达和演讲', value: 'excellent' }, { label: '良好，能正常沟通', value: 'good' }, { label: '一般，需要提升', value: 'normal' }, { label: '较弱', value: 'poor' }] },
      { text: '你参加过哪些校园活动/社团？', options: [{ label: '担任过学生干部/社团负责人', value: 'leader' }, { label: '积极参与过活动', value: 'active' }, { label: '偶尔参与', value: 'occasional' }, { label: '主要专注学业', value: 'study_only' }] },
      { text: '你有创业/副业经历吗？', options: [{ label: '创过业或做过创业项目', value: 'entrepreneur' }, { label: '有做过副业/兼职', value: 'side_job' }, { label: '没有，但有兴趣', value: 'interested' }, { label: '没有，也不想', value: 'not_interested' }] },
      { text: '5年后你希望自己在做什么？', options: [{ label: '在一家稳定的大公司发展', value: 'bigcompany' }, { label: '自己创业或做自由职业', value: 'entrepreneur' }, { label: '在出海企业工作', value: 'overseas' }, { label: '成为行业专家/技术专家', value: 'expert' }, { label: '有自己的小事业', value: 'small_business' }, { label: '还没想清楚', value: 'unknown' }] },
      { text: '你对考公/考编的态度？', options: [{ label: '正在备考或计划备考', value: 'preparing' }, { label: '有兴趣但没行动', value: 'interested' }, { label: '不考虑', value: 'not_interested' }] },
      { text: '你对第一份工作的期待？', options: [{ label: '薪资是第一位', value: 'salary_first' }, { label: '成长空间是第一位', value: 'growth_first' }, { label: '平台/公司背景是第一位', value: 'platform_first' }, { label: '工作生活平衡是第一位', value: 'balance_first' }] },
      { text: '你能接受的最低月薪（税后）？', options: [{ label: '10000以上', value: 'above_10k' }, { label: '8000-10000', value: '8k_10k' }, { label: '5000-8000', value: '5k_8k' }, { label: '5000以下也可以接受', value: 'under_5k' }] },
      { text: '你对加班的态度？', options: [{ label: '可以接受996/高强度', value: 'intense' }, { label: '可以接受偶尔加班', value: 'occasional' }, { label: '希望朝九晚五', value: 'normal' }, { label: '必须工作生活平衡', value: 'balance' }] },
      { text: '你对AI取代人类工作的看法？', options: [{ label: '很担心，希望选不容易被替代的方向', value: 'worried' }, { label: '有些担心，会作为参考', value: 'some' }, { label: '相信人的价值，不太担心', value: 'calm' }, { label: '认为AI是机会，想进入AI行业', value: 'opportunity' }] },
      { text: '你对出海行业（跨境电商/品牌出海）的了解？', options: [{ label: '很了解，有相关经历或学习', value: 'familiar' }, { label: '听说过，但不了解细节', value: 'heard' }, { label: '不了解', value: 'unknown' }] },
      { text: '你的家庭背景？', options: [{ label: '家里有资源可以支持（人脉/资金）', value: 'rich' }, { label: '家庭普通，需要自己奋斗', value: 'normal' }, { label: '家庭经济压力大，需要尽快赚钱', value: 'pressure' }] },
      { text: '你对职业发展的态度？', options: [{ label: '有明确目标，正在努力', value: 'clear' }, { label: '有大致方向，还在探索', value: 'some_direction' }, { label: '有几个方向在纠结', value: 'confused' }, { label: '完全不知道想做什么', value: 'lost' }] },
      { text: '你希望进入什么规模的公司？', options: [{ label: '大厂/上市公司', value: 'big' }, { label: '中型企业（500-5000人）', value: 'medium' }, { label: '小公司/创业公司', value: 'small' }, { label: '无所谓，关键看机会', value: 'any' }] },
      { text: '如果给你现在的状态贴一个标签，你选？', options: [{ label: '方向明确，但在犹豫', value: 'hesitate' }, { label: '有几个方向在纠结', value: 'confused' }, { label: '完全不知道想做什么', value: 'lost' }, { label: '有想法但担心不现实', value: 'worried' }] }
    ]
  },
  3: {
    title: '学生家长趣味测试（深度版）',
    questions: [
      { text: '您的孩子目前处于哪个学习阶段？', options: [{ label: '小学低年级（1-3年级）', value: 'primary_low' }, { label: '小学高年级（4-6年级）', value: 'primary_high' }, { label: '初中（7-9年级）', value: 'middle' }, { label: '高一/高二', value: 'high_early' }, { label: '高三/即将高考', value: 'high_late' }, { label: '大学在读', value: 'college' }] },
      { text: '您孩子的性别？', options: [{ label: '男孩', value: 'boy' }, { label: '女孩', value: 'girl' }] },
      { text: '您孩子的成绩大概在？', options: [{ label: '尖子生水平（前5%）', value: 'top' }, { label: '中上水平（前20%）', value: 'good' }, { label: '中等水平', value: 'normal' }, { label: '中下/需要更多关注', value: 'struggle' }] },
      { text: '您孩子的学习态度？', options: [{ label: '非常主动自律', value: 'very_active' }, { label: '需要督促但能完成', value: 'normal' }, { label: '需要较多督促', value: 'lazy' }, { label: '对学习抵触', value: 'resist' }] },
      { text: '您孩子属于哪种类型？', options: [{ label: '理科/工科（数理化强）', value: 'science' }, { label: '文科/商科（语言表达强）', value: 'arts' }, { label: '艺术/体育/创意类', value: 'creative' }, { label: '职业技术/动手型', value: 'vocational' }] },
      { text: '您孩子的性格特点？', options: [{ label: '外向开朗，善于社交', value: 'extrovert' }, { label: '内向沉稳，善于思考', value: 'introvert' }, { label: '两者兼有，看情况', value: 'balanced' }] },
      { text: '您孩子的抗压能力？', options: [{ label: '很强，经得起挫折', value: 'strong' }, { label: '一般，能应对正常压力', value: 'normal' }, { label: '较弱，需要多鼓励', value: 'weak' }] },
      { text: '您家庭年收入大概在？', options: [{ label: '50万以上', value: 'above_50' }, { label: '30-50万', value: '30_50' }, { label: '15-30万', value: '15_30' }, { label: '15万以下', value: 'under_15' }] },
      { text: '您对孩子的教育投入预算？', options: [{ label: '每年5万以上（补习/兴趣班等）', value: 'high' }, { label: '每年2-5万', value: 'medium' }, { label: '每年2万以下', value: 'low' }] },
      { text: '您家庭有几套房（不含自住）？', options: [{ label: '2套以上，无贷款压力', value: 'rich' }, { label: '1-2套，有一定贷款', value: 'normal' }, { label: '只有自住房', value: 'basic' }, { label: '还有房贷压力', value: 'pressure' }] },
      { text: '选择专业/方向时最看重什么？', options: [{ label: '未来就业前景和薪资', value: 'job' }, { label: '孩子的兴趣和意愿', value: 'interest' }, { label: '稳定性和安全感', value: 'stable' }, { label: '社会地位和声望', value: 'status' }] },
      { text: '您希望孩子将来在哪里发展？', options: [{ label: '一线城市（北上广深）', value: 'tier1' }, { label: '新一线/二线城市', value: 'tier2' }, { label: '老家/小城市', value: 'hometown' }, { label: '无所谓，看机会', value: 'anywhere' }, { label: '海外', value: 'overseas' }] },
      { text: '您对出国的态度？', options: [{ label: '计划出国读本科/中学', value: 'plan_abroad' }, { label: '考虑出国读研', value: 'consider_pg' }, { label: '不确定，看情况和时机', value: 'maybe' }, { label: '不考虑出国', value: 'not_now' }] },
      { text: '您对人民币升值的看法？', options: [{ label: '会影响我们的决策（留学/移民等）', value: 'affect' }, { label: '有一定影响，但不具决定性', value: 'some' }, { label: '影响不大，主要看国内发展', value: 'less' }] },
      { text: '您对孩子的职业期待？', options: [{ label: '希望孩子成为专业人士/专家', value: 'expert' }, { label: '希望孩子有商业头脑', value: 'business' }, { label: '希望孩子创业当老板', value: 'entrepreneur' }, { label: '希望孩子稳定生活就好', value: 'stable' }, { label: '尊重孩子的选择', value: 'respect' }] },
      { text: '您对AI技术冲击的担忧程度？', options: [{ label: '很担心，想选不容易被替代的方向', value: 'worried' }, { label: '有些担心，会作为参考因素', value: 'some' }, { label: '相信人的价值，不太担心', value: 'calm' }] },
      { text: '您了解新高考/选科政策吗？', options: [{ label: '非常了解，已经开始准备', value: 'familiar' }, { label: '了解一些，还在研究', value: 'some' }, { label: '不太了解', value: 'unfamiliar' }] },
      { text: '您的学历背景？', options: [{ label: '博士/硕士', value: 'high' }, { label: '本科', value: 'bachelor' }, { label: '大专', value: 'college' }, { label: '高中/中专以下', value: 'below' }] },
      { text: '您的职业背景？', options: [{ label: '体制内（公务员/事业单位/国企）', value: '体制内' }, { label: '大型私企/外企管理层', value: 'large_private' }, { label: '中小企业/创业', value: 'small_business' }, { label: '自由职业/个体', value: 'freelance' }, { label: '其他', value: 'other' }] },
      { text: '您和孩子的沟通关系？', options: [{ label: '非常好，孩子愿意听我的建议', value: 'excellent' }, { label: '良好，会尊重孩子的意见', value: 'good' }, { label: '一般，孩子有自己的想法', value: 'normal' }, { label: '紧张，孩子不太听', value: 'bad' }] },
      { text: '您周围朋友孩子的教育方向？', options: [{ label: '大部分选择理工科/热门专业', value: 'stem' }, { label: '比较多元化，文理科都有', value: 'mixed' }, { label: '不太了解', value: 'unknown' }] },
      { text: '您对考研/升学的态度？', options: [{ label: '必须考研，不考研没出路', value: 'must' }, { label: '鼓励考研，但不是必须', value: 'encourage' }, { label: '看孩子意愿，不强求', value: 'respect' }, { label: '不希望孩子考研，早点工作', value: 'not_needed' }] },
      { text: '您对电竞/网红/直播等新兴职业的看法？', options: [{ label: '支持，认为是机会', value: 'support' }, { label: '不反对，但不希望主业', value: 'neutral' }, { label: '不太支持，希望走传统路线', value: 'against' }] },
      { text: '您家庭的主要收入来源稳定吗？', options: [{ label: '非常稳定（体制内/大型企业）', value: 'very_stable' }, { label: '比较稳定', value: 'stable' }, { label: '有一定波动', value: 'some_risk' }, { label: '不稳定，需要灵活规划', value: 'risky' }] },
      { text: '您预计还能为孩子提供支持多少年？', options: [{ label: '10年以上', value: 'long' }, { label: '5-10年', value: 'medium' }, { label: '5年以内', value: 'short' }] },
      { text: '您对孩子创业的态度？', options: [{ label: '支持，愿意提供资金支持', value: 'support' }, { label: '不反对，但要自己努力', value: 'neutral' }, { label: '不太支持，希望稳定就业', value: 'against' }] },
      { text: '您焦虑孩子未来的程度？', options: [{ label: '非常焦虑，经常睡不着', value: 'very_anxious' }, { label: '有些焦虑，在积极准备', value: 'anxious' }, { label: '还好，相信车到山前必有路', value: 'calm' }] },
      { text: '您获取教育信息的渠道？', options: [{ label: '关注很多教育博主/专家', value: 'many' }, { label: '偶尔看看，主要靠自己判断', value: 'some' }, { label: '很少看，容易被信息淹没', value: 'overwhelmed' }] },
      { text: '如果用一句话描述现在的状态？', options: [{ label: '信息太多，不知道听谁的', value: 'info_overload' }, { label: '孩子没想法，完全不知道选什么', value: 'child_lost' }, { label: '有想法但和孩子的意见不一致', value: 'conflict' }, { label: '有大致方向，想确认是否正确', value: 'confirm' }] },
      { text: '您对"热门专业"变动的看法？', options: [{ label: '担心选热门专业时已经过饱和', value: 'worried_hot' }, { label: '会关注但不会盲目追热门', value: 'cautious' }, { label: '相信只要学得好就有出路', value: 'confident' }] },
      { text: '您希望孩子将来的生活状态？', options: [{ label: '事业有成，有社会地位', value: 'career' }, { label: '工作稳定，生活舒适', value: 'comfortable' }, { label: '开心就好，不求大富大贵', value: 'happy' }] }
    ]
  }
};

var vipConsultQuestions = [
  { text: '请说说您对未来职业的想法或疑问？', placeholder: '例如：我对AI领域很感兴趣，想知道如果尝试一下会是什么感觉...' },
  { text: '您希望从测试中探索哪些方向？', placeholder: '例如：希望了解哪些职业方向比较有趣，适合我的性格特点...' },
  { text: '关于职业探索，你还有其他想了解的吗?(可选)', placeholder: '例如：我还想知道如果尝试新领域会有什么有趣的发现？' }
];

var LIGHT_QUESTION_INDICES = { 1: [1, 2, 7], 2: [0, 1, 4], 3: [2, 3, 4] };
var DEEP_QUESTION_INDICES = { 1: [1, 2, 10, 13, 15], 2: [0, 1, 5, 7, 16], 3: [4, 8, 10, 11, 12] };

Page({
  data: {
    currentScreen: 'home',
    loading: false,
    showPaymentModal: false,
    showLightLimitModal: false,
    showExpertTip: false,
    showDouyinPayModal: false,

    // 轻量版
    currentUserType: 0, currentQuestion: 0, answers: {}, lightResult: null,
    lightAnalysisInProgress: false, lightPollTimer: null,

    // 深度版
    currentUserTypeDeep: 0, currentQuestionDeep: 0, answersDeep: {}, deepResult: null,
    deepAnalysisInProgress: false,

    // VIP版
    currentUserTypeVip: 0, currentQuestionVip: 0, answersVip: {}, vipAnswerTexts: {},
    currentConsultQuestion: 0, consultAnswersVip: [], vipResult: null,
    vipAnalysisInProgress: false, vipQuizLocked: false, vipConsultLocked: false,
    vipUserEmail: '', vipConsultId: '',

    // 支付状态
    currentPaymentVersion: '', currentPaymentUserType: 0, currentOrderId: '',
    paymentPollingTimer: null, paymentStatus: '等待支付...', paymentQrCode: '',

    // 支付弹窗数据
    paymentVersionName: '', paymentPrice: '',

    // 题库
    quizData: quizData, quizDataDeep: quizDataDeep, vipConsultQuestions: vipConsultQuestions,

    // 报告生成等待状态
    waitingForReport: false,
    reportVersion: '',
    waitingMessage: '',

    deviceId: '', lightLimitSkipped: false, lightUsedToday: false
  },

  onLoad: function() { this.initDeviceId(); this.checkLightUsage(); },
  onShow: function() { this.checkLightUsage(); },

  checkLightUsage: function() {
    var today = new Date().toDateString();
    var lastUsedDate = tt.getStorageSync('light_used_date_' + this.data.deviceId);
    this.setData({ lightUsedToday: lastUsedDate === today });
  },

  onUnload: function() { this.clearAllTimers(); },

  initDeviceId: function() {
    var deviceId = tt.getStorageSync('career_device_id');
    if (!deviceId) {
      deviceId = 'DEV' + Date.now() + Math.random().toString(36).substr(2, 9);
      tt.setStorageSync('career_device_id', deviceId);
    }
    this.setData({ deviceId: deviceId });
  },

  clearAllTimers: function() {
    if (this.data.lightPollTimer) clearTimeout(this.data.lightPollTimer);
    if (this.data.paymentPollingTimer) clearInterval(this.data.paymentPollingTimer);
  },

  // ======== 工具函数 ========
  safeGet: function(obj, path, fallback) { try { return path.split('.').reduce(function(o, k) { return o[k]; }, obj) || (fallback || '暂无内容'); } catch (e) { return fallback || '暂无内容'; } },
  getQuestionIndices: function(userType, version) { return (version === 'light' ? LIGHT_QUESTION_INDICES : DEEP_QUESTION_INDICES)[userType] || []; },
  filterAnswersForAI: function(answers, userType, version) { var indices = this.getQuestionIndices(userType, version); var filtered = {}; var that = this; indices.forEach(function(idx) { if (answers[idx] !== undefined) filtered[idx] = answers[idx]; }); return filtered; },
  filterQuestionsForAI: function(questions, userType, version) { var indices = this.getQuestionIndices(userType, version); return indices.map(function(idx) { return questions[idx]; }).filter(function(q) { return q !== undefined; }); },
  cleanPlaceholder: function(text) { 
    if (!text || typeof text !== 'string') return text; 
    text = text.replace(/(XX|xxx|待定|未知|暂无数据|暂无内容|TBD|N\/A)/gi, '数据待分析');
    text = text.replace(/成功转型|转型完成|已转型|转型成功|成功转行|转行成功/g, '建议转型');
    text = text.replace(/```[\s\S]*?```/g, '');
    text = text.replace(/`[^`]+`/g, '');
    text = text.replace(/【[\s\S]*?】/g, '');
    text = text.replace(/[a-zA-Z]{4,}/g, '');
    return text;
  },
  deepClean: function(obj) { 
    var that = this; 
    if (typeof obj === 'string') return that.cleanPlaceholder(obj); 
    if (Array.isArray(obj)) return obj.map(function(item) { return that.deepClean(item); }); 
    if (obj && typeof obj === 'object') { 
      var cleaned = {}; 
      for (var k in obj) {
        var value = obj[k];
        if (k === 'result' && typeof value === 'string') {
          if (value.includes('成功转型') || value.includes('转型完成')) {
            cleaned[k] = '建议转型';
          } else {
            cleaned[k] = that.cleanPlaceholder(value);
          }
        } else {
          cleaned[k] = that.deepClean(value);
        }
      } 
      return cleaned; 
    } 
    return obj; 
  },
  switchScreen: function(screen) { this.setData({ currentScreen: screen }); tt.pageScrollTo({ scrollTop: 0, duration: 300 }); },
  goBackHome: function() { this.switchScreen('home'); },
  goBackUserType: function() { this.switchScreen('userType'); },
  stopPropagation: function() {},

  // ======== 报告等待页面 ========
  showWaitingScreen: function(version) {
    var messages = [
      'AI正在分析您的职业背景...',
      'AI正在匹配宏观趋势数据...',
      'AI正在生成个性化建议...',
      'AI正在整理分析报告...',
      '报告即将生成完成...'
    ];
    this.setData({ 
      currentScreen: 'waiting',
      waitingForReport: true,
      reportVersion: version,
      waitingMessage: messages[0]
    });
    this.startWaitingAnimation(messages);
  },

  startWaitingAnimation: function(messages) {
    var that = this;
    var index = 0;
    setInterval(function() {
      index = (index + 1) % messages.length;
      that.setData({ waitingMessage: messages[index] });
    }, 2500);
  },

  hideWaitingScreen: function() {
    this.setData({ waitingForReport: false, reportVersion: '', waitingMessage: '' });
  },

  // ======== 轻量版 ========
  goToLightVersion: function() { if (this.data.lightUsedToday && !this.data.lightLimitSkipped) { this.setData({ showLightLimitModal: true }); return; } this.switchScreen('userType'); },
  closeLightLimitModal: function() { this.setData({ showLightLimitModal: false, lightUsedToday: true }); },
  closeLightLimitModalAndGoPay: function() { this.setData({ showLightLimitModal: false }); this.switchScreen('userTypeDeep'); },
  skipLightLimitForTest: function() { this.setData({ lightLimitSkipped: true, showLightLimitModal: false }); this.switchScreen('userType'); },

  selectUserType: function(e) {
    var type = e.currentTarget.dataset.type;
    var today = new Date().toDateString();
    if (!this.data.lightLimitSkipped) tt.setStorageSync('light_used_date_' + this.data.deviceId, today);
    this.setData({ currentUserType: type, currentQuestion: 0, answers: {}, lightResult: null, lightUsedToday: true });
    this.switchScreen('quiz'); this.renderQuestion();
  },

  renderQuestion: function() {
    var data = this.data.quizData[this.data.currentUserType];
    var q = data.questions[this.data.currentQuestion];
    var percent = Math.round(((this.data.currentQuestion + 1) / data.questions.length) * 100);
    this.setData({ currentQuestionData: q, quizQuestions: data.questions, selectedAnswer: this.data.answers[this.data.currentQuestion], quizProgress: percent, quizProgressText: '问题 ' + (this.data.currentQuestion + 1) + '/' + data.questions.length });
  },

  selectOption: function(e) {
    var value = e.currentTarget.dataset.value;
    var answers = this.data.answers;
    answers[this.data.currentQuestion] = value;
    this.setData({ answers: answers, selectedAnswer: value });
    var that = this;
    setTimeout(function() {
      var data = that.data.quizData[that.data.currentUserType];
      if (that.data.currentQuestion < data.questions.length - 1) { that.setData({ currentQuestion: that.data.currentQuestion + 1 }); that.renderQuestion(); }
      else { that.showResult(); }
    }, 200);
  },

  quizBack: function() { if (this.data.currentQuestion > 0) { this.setData({ currentQuestion: this.data.currentQuestion - 1 }); this.renderQuestion(); } },
  showResult: function() { if (this.data.lightAnalysisInProgress) return; this.showWaitingScreen('light'); this.callAIAnalysis(); },

  callAIAnalysis: function() {
    var that = this;
    this.setData({ lightAnalysisInProgress: true });
    try {
      var data = that.data.quizData[that.data.currentUserType];
      var filteredAnswers = that.filterAnswersForAI(that.data.answers, that.data.currentUserType, 'light');
      var filteredQuestions = that.filterQuestionsForAI(data.questions, that.data.currentUserType, 'light');
      tt.request({ url: API_BASE + '/api/analyze', method: 'POST', data: { userType: that.data.currentUserType, answers: filteredAnswers, questions: filteredQuestions },
        success: function(res) { if (res.data.status === 'generating') { that.pollLightAnalysis(res.data.cacheKey); return; } if (res.data.error) { that.hideWaitingScreen(); that.switchScreen('result'); that.showFallbackResult(res.data.error); return; } that.displayAIResult(res.data); },
        fail: function(err) { that.hideWaitingScreen(); that.switchScreen('result'); that.showFallbackResult('网络连接失败，请检查网络后重试'); },
        complete: function() { that.setData({ lightAnalysisInProgress: false }); } });
    } catch (e) { that.hideWaitingScreen(); that.switchScreen('result'); that.setData({ lightAnalysisInProgress: false }); that.showFallbackResult('网络连接失败'); }
  },

  pollLightAnalysis: function(cacheKey) {
    var that = this, maxAttempts = 600, attempts = 0;
    function poll() { if (attempts >= maxAttempts) { that.hideWaitingScreen(); that.switchScreen('result'); that.showFallbackResult('报告生成超时'); return; } tt.request({ url: API_BASE + '/api/analyze/poll/' + cacheKey, success: function(res) { if (res.data.status === 'completed') { that.displayAIResult(res.data.analysis); return; } attempts++; setTimeout(poll, 2000); }, fail: function() { attempts++; setTimeout(poll, 2000); } }); } poll();
  },

  showFallbackResult: function(message) {
    this.setData({ lightResult: { summary: { analysis: message || '请配置AI分析服务后重试', result: '请配置AI分析服务后重试' }, macroTrends: [{ trend: 'AI/大模型正在重塑所有行业', outlook: '长期看好', period: '5-10年', analysis: '技术类岗位需求增加，但基础编程可能被替代' }], persona: [{ label: '优势', value: '技术背景扎实，学习能力强' }], recommendedIndustries: [{ name: 'AI应用开发', outlook: '高速增长', reason: '技术+应用结合，适合技术人转型', hotRoles: ['AI产品经理', 'Prompt工程师'] }], risks: ['技术迭代快，需保持持续学习', '转型期收入可能下降20-30%'] } });
  },
  displayAIResult: function(result) { 
    this.hideWaitingScreen();
    this.switchScreen('result');
    this.setData({ lightResult: this.deepClean(result) }); 
  },

  resetQuiz: function() { this.setData({ currentUserType: 0, currentQuestion: 0, answers: {}, lightResult: null, lightAnalysisInProgress: false, lightLimitSkipped: false }); this.checkLightUsage(); this.switchScreen('home'); },

  // ======== 深度版 ========
  startQuiz: function(e) { var v = e.currentTarget.dataset.version; if (v === 'light') this.goToLightVersion(); else if (v === 'deep') this.switchScreen('userTypeDeep'); else if (v === 'vip') this.switchScreen('userTypeVip'); },

  startDeepWithPayment: function(e) {
    var type = e.currentTarget.dataset.type;
    var paidToken = tt.getStorageSync('paid_deep');
    this.setData({ currentPaymentUserType: type, currentPaymentVersion: 'deep' });
    if (paidToken) { this.startDeepQuiz(type); } else { this.openDouyinPayModal('deep'); }
  },

  startDeepQuiz: function(type) { this.setData({ currentUserTypeDeep: type || this.data.currentPaymentUserType || 1, currentQuestionDeep: 0, answersDeep: {}, deepResult: null }); this.switchScreen('quizDeep'); this.renderQuestionDeep(); },

  renderQuestionDeep: function() {
    var data = this.data.quizDataDeep[this.data.currentUserTypeDeep];
    var q = data.questions[this.data.currentQuestionDeep];
    var percent = Math.round(((this.data.currentQuestionDeep + 1) / data.questions.length) * 100);
    this.setData({ deepQuestionText: q.text, deepQuestionOptions: q.options, deepSelectedAnswer: this.data.answersDeep[this.data.currentQuestionDeep], deepQuizProgress: percent, deepQuizProgressText: '问题 ' + (this.data.currentQuestionDeep + 1) + '/' + data.questions.length });
  },

  selectOptionDeep: function(e) {
    var value = e.currentTarget.dataset.value;
    var answersDeep = this.data.answersDeep;
    answersDeep[this.data.currentQuestionDeep] = value;
    this.setData({ answersDeep: answersDeep, deepSelectedAnswer: value });
    var that = this;
    setTimeout(function() { var data = that.data.quizDataDeep[that.data.currentUserTypeDeep]; if (that.data.currentQuestionDeep < data.questions.length - 1) { that.setData({ currentQuestionDeep: that.data.currentQuestionDeep + 1 }); that.renderQuestionDeep(); } else { that.showResultDeep(); } }, 200);
  },

  quizBackDeep: function() { if (this.data.currentQuestionDeep > 0) { this.setData({ currentQuestionDeep: this.data.currentQuestionDeep - 1 }); this.renderQuestionDeep(); } },
  showResultDeep: function() { if (this.data.deepAnalysisInProgress) return; this.showWaitingScreen('deep'); this.callAIAnalysisDeep(); },

  callAIAnalysisDeep: function() {
    var that = this;
    this.setData({ deepAnalysisInProgress: true });
    try {
      var data = that.data.quizDataDeep[that.data.currentUserTypeDeep];
      var filteredAnswers = that.filterAnswersForAI(that.data.answersDeep, that.data.currentUserTypeDeep, 'deep');
      var filteredQuestions = that.filterQuestionsForAI(data.questions, that.data.currentUserTypeDeep, 'deep');
      tt.request({ url: API_BASE + '/api/analyze-deep', method: 'POST', data: { userType: that.data.currentUserTypeDeep, answers: filteredAnswers, questions: filteredQuestions, version: 'deep' },
        success: function(res) { if (res.data.status === 'generating') { that.pollDeepAnalysis(res.data.cacheKey); return; } that.displayDeepResult(res.data); },
        fail: function() { that.hideWaitingScreen(); that.switchScreen('resultDeep'); that.showFallbackResultDeep('深度报告生成中...'); },
        complete: function() { that.setData({ deepAnalysisInProgress: false }); } });
    } catch (e) { that.hideWaitingScreen(); that.switchScreen('resultDeep'); that.setData({ deepAnalysisInProgress: false }); that.showFallbackResultDeep('深度报告生成中...'); }
  },

  pollDeepAnalysis: function(cacheKey) { var that = this, maxAttempts = 600, attempts = 0; function poll() { if (attempts >= maxAttempts) { that.hideWaitingScreen(); that.switchScreen('resultDeep'); that.showFallbackResultDeep('报告生成超时'); return; } tt.request({ url: API_BASE + '/api/analyze-deep/poll/' + cacheKey, success: function(res) { if (res.data.status === 'completed') { that.displayDeepResult(res.data); return; } attempts++; setTimeout(poll, 2000); }, fail: function() { attempts++; setTimeout(poll, 2000); } }); } poll(); },

  showFallbackResultDeep: function(message) { this.setData({ deepResult: { summary: { analysis: message || '深度报告生成中', result: '深度报告生成中' }, macroTrends: [], persona: {}, recommendedIndustries: [], skillGap: [], actionPlan: [], risks: [] } }); },
  displayDeepResult: function(result) { 
    this.hideWaitingScreen();
    this.switchScreen('resultDeep');
    var cleanedResult = this.deepClean(result); 
    this.setData({ deepResult: cleanedResult.analysis || cleanedResult }); 
    tt.removeStorageSync('paid_deep'); 
  },
  resetDeepQuiz: function() { this.setData({ currentUserTypeDeep: 0, currentQuestionDeep: 0, answersDeep: {}, deepResult: null, deepAnalysisInProgress: false }); this.switchScreen('home'); },

  // ======== VIP版 ========
  startVipWithPayment: function(e) { var type = e.currentTarget.dataset.type; var paidToken = tt.getStorageSync('paid_vip'); this.setData({ currentPaymentUserType: type, currentPaymentVersion: 'vip' }); if (paidToken) { this.startVipQuiz(type); } else { this.openDouyinPayModal('vip'); } },

  startVipQuiz: function(type) { this.clearVipState(); this.setData({ currentUserTypeVip: type || this.data.currentPaymentUserType || 1, currentQuestionVip: 0, answersVip: {} }); this.switchScreen('quizVip'); this.renderQuestionVip(); },

  renderQuestionVip: function() {
    var data = this.data.quizDataDeep[this.data.currentUserTypeVip];
    var q = data.questions[this.data.currentQuestionVip];
    var percent = Math.round(((this.data.currentQuestionVip + 1) / data.questions.length) * 100);
    this.setData({ vipQuestionText: q.text, vipQuestionOptions: q.options, vipSelectedAnswer: this.data.answersVip[this.data.currentQuestionVip], vipQuizProgress: percent, vipQuizProgressText: '问题 ' + (this.data.currentQuestionVip + 1) + '/' + data.questions.length });
  },

  selectOptionVip: function(e) {
    if (this.data.vipQuizLocked || this.data.vipConsultLocked) return;
    this.setData({ vipQuizLocked: true });
    var value = e.currentTarget.dataset.value;
    var answersVip = this.data.answersVip;
    answersVip[this.data.currentQuestionVip] = value;
    var questions = this.data.quizDataDeep[this.data.currentUserTypeVip].questions;
    var question = questions[this.data.currentQuestionVip];
    var selectedOption = null;
    if (question && question.options) { for (var i = 0; i < question.options.length; i++) { if (question.options[i].value === value) { selectedOption = question.options[i]; break; } } }
    if (!selectedOption) { for (var qi = 0; qi < questions.length; qi++) { var opts = questions[qi].options; if (opts) { for (var oi = 0; oi < opts.length; oi++) { if (opts[oi].value === value) { selectedOption = opts[oi]; break; } } } if (selectedOption) break; } }
    var vipAnswerTexts = this.data.vipAnswerTexts;
    vipAnswerTexts[this.data.currentQuestionVip] = selectedOption ? selectedOption.label : value;
    this.setData({ answersVip: answersVip, vipAnswerTexts: vipAnswerTexts, vipSelectedAnswer: value });
    var that = this;
    setTimeout(function() {
      try {
        var data = that.data.quizDataDeep[that.data.currentUserTypeVip];
        if (that.data.currentQuestionVip < data.questions.length - 1) { that.setData({ currentQuestionVip: that.data.currentQuestionVip + 1, vipQuizLocked: false }); that.renderQuestionVip(); }
        else { that.setData({ currentConsultQuestion: 0, consultAnswersVip: [], vipQuizLocked: false }); that.switchScreen('vipConsult'); setTimeout(function() { that.renderVipConsult(); }, 200); }
      } catch (err) { that.setData({ vipQuizLocked: false }); tt.showToast({ title: '加载失败，请重试', icon: 'none' }); }
    }, 200);
  },

  quizBackVip: function() { if (this.data.vipQuizLocked) this.setData({ vipQuizLocked: false }); if (this.data.currentQuestionVip > 0) { this.setData({ currentQuestionVip: this.data.currentQuestionVip - 1 }); this.renderQuestionVip(); } },
  consultBack: function() { if (this.data.currentConsultQuestion > 0) { this.setData({ currentConsultQuestion: this.data.currentConsultQuestion - 1 }); this.renderVipConsult(); } },

  renderVipConsult: function() {
    if (this.data.currentConsultQuestion >= this.data.vipConsultQuestions.length) { this.submitVipAnalysis(); return; }
    var q = this.data.vipConsultQuestions[this.data.currentConsultQuestion];
    var percent = Math.round(((this.data.currentConsultQuestion + 1) / this.data.vipConsultQuestions.length) * 100);
    var currentAnswer = this.data.consultAnswersVip[this.data.currentConsultQuestion];
    if (currentAnswer === undefined || currentAnswer === null) { var consultAnswersVip = this.data.consultAnswersVip.slice(); consultAnswersVip[this.data.currentConsultQuestion] = ''; this.setData({ consultAnswersVip: consultAnswersVip }); }
    this.setData({ vipConsultQuestionText: q.text, vipConsultPlaceholder: q.placeholder, vipConsultAnswer: this.data.consultAnswersVip[this.data.currentConsultQuestion], vipConsultProgress: percent, vipConsultProgressText: '咨询问题 ' + (this.data.currentConsultQuestion + 1) + '/' + this.data.vipConsultQuestions.length, showVipEmailSection: false });
  },

  onVipConsultInput: function(e) { var consultAnswersVip = this.data.consultAnswersVip.slice(); consultAnswersVip[this.data.currentConsultQuestion] = e.detail.value; this.setData({ consultAnswersVip: consultAnswersVip, vipConsultAnswer: e.detail.value }); },

  submitVipConsult: function() {
    var answer = this.data.consultAnswersVip[this.data.currentConsultQuestion] || '';
    if (!answer && this.data.currentConsultQuestion < 2) { tt.showToast({ title: '请填写咨询问题', icon: 'none' }); return; }
    this.setData({ currentConsultQuestion: this.data.currentConsultQuestion + 1 });
    if (this.data.currentConsultQuestion < this.data.vipConsultQuestions.length) { this.renderVipConsult(); } else { this.setData({ showVipEmailSection: true }); }
  },

  onVipEmailInput: function(e) { this.setData({ vipUserEmail: e.detail.value }); },

  submitVipEmail: function() { var email = this.data.vipUserEmail.trim(); if (!email) { tt.showToast({ title: '请填写邮箱地址', icon: 'none' }); return; } if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { tt.showToast({ title: '请输入有效邮箱', icon: 'none' }); return; } this.submitVipConsultData(email); this.submitVipAnalysis(); },

  submitVipConsultData: function(email) {
    var that = this;
    try { var consultQuestionsData = that.data.vipConsultQuestions.map(function(q, idx) { return { question: q.text, answer: that.data.consultAnswersVip[idx] || '' }; }); tt.request({ url: API_BASE + '/api/vip/consult', method: 'POST', data: { email: email, answers: that.data.answersVip, answerTexts: that.data.vipAnswerTexts, consultQuestions: consultQuestionsData, userType: String(that.data.currentUserTypeVip), questions: that.data.quizDataDeep[that.data.currentUserTypeVip].questions }, success: function(res) { if (res.data.id) that.setData({ vipConsultId: res.data.id }); }, fail: function(err) { console.error('提交VIP咨询失败:', err); } }); } catch (e) { console.error('提交VIP咨询失败:', e); }
  },

  submitVipAnalysis: function() { if (this.data.vipAnalysisInProgress) return; this.showWaitingScreen('vip'); this.callAIAnalysisVip(); },

  callAIAnalysisVip: function() {
    var that = this; this.setData({ vipAnalysisInProgress: true });
    try { var data = that.data.quizDataDeep[that.data.currentUserTypeVip]; var filteredAnswers = that.filterAnswersForAI(that.data.answersVip, that.data.currentUserTypeVip, 'deep'); var filteredQuestions = that.filterQuestionsForAI(data.questions, that.data.currentUserTypeVip, 'deep'); tt.request({ url: API_BASE + '/api/analyze-deep', method: 'POST', data: { userType: that.data.currentUserTypeVip, answers: filteredAnswers, questions: filteredQuestions, version: 'vip' }, success: function(res) { if (res.data.status === 'generating') { that.pollVipAnalysis(res.data.cacheKey); return; } that.displayVipResult(res.data); }, fail: function() { that.hideWaitingScreen(); that.switchScreen('resultVip'); that.showFallbackResultVip('VIP报告生成中...'); }, complete: function() { that.setData({ vipAnalysisInProgress: false }); } }); } catch (e) { that.hideWaitingScreen(); that.switchScreen('resultVip'); that.setData({ vipAnalysisInProgress: false }); that.showFallbackResultVip('VIP报告生成中...'); }
  },

  pollVipAnalysis: function(cacheKey) { var that = this, maxAttempts = 600, attempts = 0; function poll() { if (attempts >= maxAttempts) { that.hideWaitingScreen(); that.switchScreen('resultVip'); that.showFallbackResultVip('报告生成超时'); return; } tt.request({ url: API_BASE + '/api/analyze-vip/poll/' + cacheKey, success: function(res) { if (res.data.status === 'completed') { that.displayVipResult(res.data); return; } attempts++; setTimeout(poll, 2000); }, fail: function() { attempts++; setTimeout(poll, 2000); } }); } poll(); },

  showFallbackResultVip: function(message) { this.setData({ vipResult: { summary: { analysis: message || 'VIP深度报告生成中', result: 'VIP深度报告生成中' }, macroTrends: [], persona: {}, recommendedIndustries: [], skillGap: [], actionPlan: [], risks: [] } }); },

  displayVipResult: function(result) { 
    this.hideWaitingScreen();
    this.switchScreen('resultVip');
    var cleanedResult = this.deepClean(result); 
    this.setData({ vipResult: cleanedResult.analysis || cleanedResult, showExpertTip: true }); 
    if (this.data.vipConsultId) this.saveVipReportData(this.data.vipConsultId, cleanedResult.analysis || cleanedResult); 
    tt.removeStorageSync('paid_vip'); 
    var that = this; 
    setTimeout(function() { that.setData({ showExpertTip: false }); }, 30000); 
  },

  saveVipReportData: function(consultId, reportData) { try { tt.request({ url: API_BASE + '/api/vip/consult/' + consultId + '/report', method: 'PUT', data: { reportData: reportData } }); } catch (e) { console.error('保存VIP报告失败:', e); } },

  clearVipState: function() { this.setData({ currentUserTypeVip: 0, currentQuestionVip: 0, answersVip: {}, vipAnswerTexts: {}, currentConsultQuestion: 0, consultAnswersVip: [], vipResult: null, vipAnalysisInProgress: false, vipQuizLocked: false, vipConsultLocked: false, vipUserEmail: '', vipConsultId: '', showExpertTip: false }); },
  resetVipQuiz: function() { this.clearVipState(); this.switchScreen('home'); },


  // ======== 支付弹窗 ========
  openDouyinPayModal: function(version) {
    var paidToken = tt.getStorageSync('paid_' + version);
    if (paidToken) { if (version === 'deep') this.startDeepQuiz(); else this.startVipQuiz(); return; }
    var paymentVersionName = version === 'deep' ? '深度趣味测试版' : 'VIP趣味体验版';
    var paymentPrice = version === 'deep' ? '¥9.9' : '¥19.9';
    this.setData({ currentPaymentVersion: version, paymentVersionName: paymentVersionName, paymentPrice: paymentPrice, showDouyinPayModal: true, paymentStatus: '正在创建订单...', currentOrderId: '' });
    this.createDouyinPaymentOrder(version);
  },

  closeDouyinPayModal: function() { this.setData({ showDouyinPayModal: false }); },

  createDouyinPaymentOrder: function(version) {
    var that = this;
    var orderAmount = version === 'deep' ? 990 : 1990;
    var orderTitle = version === 'deep' ? '职路星途-深度趣味测试' : '职路星途-VIP趣味体验';
    
    tt.showLoading({ title: '创建订单中...', mask: true });
    
    tt.request({
      url: API_BASE + '/api/douyin-payment/create-order',
      method: 'POST',
      data: { version: version, amount: orderAmount, subject: orderTitle, device_id: that.data.deviceId || 'mini_program_' + Date.now(), out_order_no: 'ORDER_' + Date.now() + '_' + version },
      success: function(res) {
        tt.hideLoading();
        if (res.data.code === 0 && res.data.order_id) {
          that.setData({ currentOrderId: res.data.order_id, paymentStatus: '订单已创建，正在拉起支付...' });
          that.invokeDouyinPay(res.data);
        } else {
          tt.showModal({ title: '订单创建失败', content: res.data.msg || '请稍后重试', showCancel: false });
          that.closeDouyinPayModal();
        }
      },
      fail: function(err) {
        tt.hideLoading();
        tt.showModal({ title: '提示', content: '支付服务暂时不可用，是否使用模拟测试模式？', confirmText: '模拟测试', cancelText: '取消', success: function(res) { if (res.confirm) that.simulatePaymentSuccess(); else that.closeDouyinPayModal(); } });
      }
    });
  },

  invokeDouyinPay: function(orderData) {
    var that = this;
    that.setData({ paymentStatus: '正在拉起支付...' });
    tt.pay({
      orderInfo: { order_id: orderData.order_id, order_token: orderData.order_token, order_amount: orderData.amount || (that.data.currentPaymentVersion === 'deep' ? 990 : 1990) },
      success: function(payRes) {
        that.setData({ paymentStatus: '支付成功！正在跳转...' });
        // 同步更新后端订单状态
        that.updatePaymentStatusToPaid(orderData.order_id);
        tt.setStorageSync('paid_' + that.data.currentPaymentVersion, { paid: true, order_id: orderData.order_id, version: that.data.currentPaymentVersion, time: Date.now() });
        setTimeout(function() { that.closeDouyinPayModal(); if (that.data.currentPaymentVersion === 'deep') that.startDeepQuiz(that.data.currentPaymentUserType); else that.startVipQuiz(that.data.currentPaymentUserType); }, 1500);
      },
      fail: function(payRes) {
        var errMsg = payRes.err_msg === 'cancel' ? '支付已取消' : (payRes.err_msg || '支付失败');
        tt.showModal({ title: '支付未完成', content: errMsg + '，您可以随时返回重新支付', confirmText: '重新支付', cancelText: '返回', success: function(res) { if (res.confirm) that.invokeDouyinPay(orderData); else that.closeDouyinPayModal(); } });
      }
    });
  },
  
  updatePaymentStatusToPaid: function(orderId) {
    // 调用后端模拟支付接口，更新订单状态
    try {
      tt.request({
        url: API_BASE + '/api/payment/simulate',
        method: 'POST',
        data: { order_id: orderId },
        success: function() {
          console.log('后端订单状态已更新为已支付');
        },
        fail: function() {
          console.log('更新后端订单状态失败，但不影响用户体验');
        }
      });
    } catch(e) {
      console.error('更新订单状态异常:', e);
    }
  },

  simulatePaymentSuccess: function() {
    var that = this;
    var simulateOrderId = 'SIMULATE_' + Date.now();
    that.setData({ paymentStatus: '模拟支付成功！正在跳转...' });
    // 模拟支付时也更新后端订单状态（使用当前订单ID或模拟一个）
    if (that.data.currentOrderId) {
      that.updatePaymentStatusToPaid(that.data.currentOrderId);
    }
    tt.setStorageSync('paid_' + that.data.currentPaymentVersion, { paid: true, order_id: simulateOrderId, version: that.data.currentPaymentVersion, time: Date.now() });
    setTimeout(function() { that.closeDouyinPayModal(); if (that.data.currentPaymentVersion === 'deep') that.startDeepQuiz(that.data.currentPaymentUserType); else that.startVipQuiz(that.data.currentPaymentUserType); }, 1500);
  },

  douyinPaySimulate: function(e) { this.simulatePaymentSuccess(); },
  showPaymentModal: function(version) { this.openDouyinPayModal(version); },
  hidePaymentModal: function() { this.closeDouyinPayModal(); },
  createPaymentOrder: function(version) { this.createDouyinPaymentOrder(version); },
  startPaymentPolling: function() { },
  stopPaymentPolling: function() { },
  simulatePayment: function() { this.simulatePaymentSuccess(); }
});
