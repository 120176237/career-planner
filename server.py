"""
职路星途 - AI职业分析后端服务
支持: OpenAI / DeepSeek / 豆包(Doubao) API
"""

# ==================== 依赖自检查与安装 ====================
import sys
try:
    import portalocker
    print("✅ portalocker已安装")
except ImportError:
    print("⚠️ portalocker未安装，正在自动安装...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "portalocker"])
        print("✅ portalocker安装成功")
        import portalocker
    except Exception as e:
        print(f"❌ 自动安装失败: {e}")
        print("请手动执行: pip install portalocker")
        sys.exit(1)

import os
import json
import re
import asyncio
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from datetime import datetime
import uuid

# 数据库抽象层
from db import init_db, get_connection, db_execute, DB_TYPE

app = FastAPI(title="职路星途 - AI职业规划")

# CORS配置 - 抖音小程序跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# API密钥配置（从环境变量读取，上线前必须在云托管配置）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# ============================================
# 缓存模块 - 完全匹配缓存系统
# 版本: 轻量版/深度版/VIP版 × 人群
# 每年更新缓存数据库
# ============================================
import hashlib
from pathlib import Path as PathLib

CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

# ==================== 跨平台文件锁（portalocker）====================
# 替代threading.Lock，支持多Worker（多进程）场景
def get_lock_file(cache_type: str) -> Path:
    """返回锁文件路径（多Worker共享）"""
    return CACHE_DIR / f"{cache_type}.lock"

def lock_read(cache_type: str, timeout=1):
    """读锁（共享锁，极短持有）"""
    lock_file = get_lock_file(cache_type)
    lock_file.touch(exist_ok=True)
    f = open(lock_file, 'r')
    try:
        portalocker.lock(f, portalocker.LOCK_SH)
        return f
    except Exception:
        f.close()
        raise

def lock_write(cache_type: str, timeout=5):
    """写锁（排他锁，极短持有）"""
    lock_file = get_lock_file(cache_type)
    lock_file.touch(exist_ok=True)
    f = open(lock_file, 'w')
    try:
        portalocker.lock(f, portalocker.LOCK_EX)
        return f
    except Exception:
        f.close()
        raise

def get_cache_file_path(version: str, user_type: int) -> Path:
    """
    获取缓存文件路径
    version: light / deep / vip
    user_type: 1=30-40转型 / 2=应届生 / 3=学生家长
    """
    current_year = datetime.now().year
    type_prefix = {
        1: "30_40",
        2: "fresh",
        3: "parent"
    }[user_type]
    return CACHE_DIR / f"{version}_{type_prefix}_{current_year}.json"

def generate_cache_key(answers: dict) -> str:
    """
    生成缓存Key
    将所有答题数据排序后拼接，用MD5生成唯一Key
    """
    # 排序确保一致性
    sorted_answers = sorted(answers.items(), key=lambda x: str(x[0]))
    # 拼接所有value
    answer_str = "+".join([f"{k}:{v}" for k, v in sorted_answers if v is not None])
    # 生成MD5
    return hashlib.md5(answer_str.encode('utf-8')).hexdigest()

def load_cache(version: str, user_type: int) -> dict:
    """加载缓存文件（极短读锁：5毫秒）"""
    cache_file = get_cache_file_path(version, user_type)
    cache_type = f"{version}_{user_type}"
    
    try:
        # 极短读锁（共享锁）
        with lock_read(cache_type):
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception as e:
        print(f"读缓存失败: {e}")
    
    return {"_meta": get_default_meta(version, user_type), "_cache": {}}

def save_cache(version: str, user_type: int, cache_data: dict):
    """保存缓存文件（极短写锁：5毫秒）"""
    cache_file = get_cache_file_path(version, user_type)
    cache_type = f"{version}_{user_type}"
    
    try:
        # 极短写锁（排他锁）
        with lock_write(cache_type):
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写缓存失败: {e}")

def get_default_meta(version: str, user_type: int) -> dict:
    """获取默认的缓存元信息"""
    type_name = {
        1: "30-40转型群体",
        2: "应届/毕业生",
        3: "学生家长"
    }[user_type]
    return {
        "version": str(datetime.now().year),
        "type": f"{version}_{user_type}",
        "description": f"{version.upper()}版-{type_name}分析缓存",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_entries": 0
    }

def get_cache(answers: dict, version: str, user_type: int) -> tuple:
    """
    获取缓存（极短锁：5毫秒）
    返回: (缓存结果, 是否命中, cache_key)
    """
    cache_key = generate_cache_key(answers)
    cache_type = f"{version}_{user_type}"
    
    # 极短读锁（共享锁）
    with lock_read(cache_type):
        cache_data = load_cache(version, user_type)
        
        if cache_key in cache_data.get("_cache", {}):
            entry = cache_data["_cache"][cache_key]
            return entry["result"], True, cache_key
    
    return None, False, cache_key

def get_cache_by_key(cache_key: str, version: str = None) -> tuple:
    """
    通过cache_key直接查找缓存（跨user_type搜索）
    返回: (缓存结果, 是否命中, user_type)
    """
    # 如果指定了version，只搜索指定的版本
    versions_to_check = [version] if version else ['light', 'deep', 'vip']
    user_types_to_check = [1, 2, 3]
    
    for ver in versions_to_check:
        for ut in user_types_to_check:
            cache_data = load_cache(ver, ut)
            if cache_key in cache_data.get("_cache", {}):
                entry = cache_data["_cache"][cache_key]
                return entry["result"], True, ut
    
    return None, False, None

def set_cache(answers: dict, result: dict, version: str, user_type: int, cache_key: str):
    """
    设置缓存（无锁版本 - JSON覆盖写入本身是原子操作）
    """
    cache_file = get_cache_file_path(version, user_type)
    
    try:
        # 直接读取现有缓存（读锁保护）
        cache_data = load_cache(version, user_type)
        
        # 更新缓存条目
        cache_data["_cache"][cache_key] = {
            "input_hash": cache_key,
            "input_snapshot": {k: v for k, v in answers.items() if v is not None},
            "result": result,
            "created_at": datetime.now().isoformat()
        }
        
        # 更新元信息
        cache_data["_meta"]["updated_at"] = datetime.now().isoformat()
        cache_data["_meta"]["total_entries"] = len(cache_data["_cache"])
        
        # 直接写入缓存文件（覆盖写入，原子操作）
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"[BG] ✅ 缓存保存完成: {cache_file.name}")
        
    except Exception as e:
        print(f"[BG] ❌ 写缓存失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

# ==================== "生成中"标记机制（多Worker可见）====================
# 使用文件标记，替代内存dict（多进程不共享内存）
GENERATING_DIR = CACHE_DIR / "_generating"
GENERATING_DIR.mkdir(exist_ok=True)
GENERATING_TIMEOUT = 300  # 5分钟超时

def get_generating_flag(cache_key: str) -> Path:
    """返回生成中标记文件路径"""
    return GENERATING_DIR / f"{cache_key}.flag"

def is_generating(cache_key: str) -> bool:
    """检查是否正在生成中（文件标记，多Worker可见）"""
    flag_file = get_generating_flag(cache_key)
    if flag_file.exists():
        # 检查是否超时（5分钟）
        if time.time() - flag_file.stat().st_mtime > GENERATING_TIMEOUT:
            flag_file.unlink()  # 删除超时标记
            return False
        return True
    return False

def start_generating(cache_key: str):
    """标记开始生成"""
    flag_file = get_generating_flag(cache_key)
    flag_file.touch()

def finish_generating(cache_key: str):
    """标记生成完成"""
    flag_file = get_generating_flag(cache_key)
    if flag_file.exists():
        flag_file.unlink()

# ==================== 后台异步生成（完美解决AI慢问题）====================
# 流程：极短锁读缓存 → 有缓存立即返回 → 无缓存检查是否在生成 → 
#       已在生成则等结果 → 未生成则启动后台生成 + 立即返回"正在生成"

# ==================== 行业硬性过滤 + 体力校验 ====================

EDUCATION_LEVELS = ["大专以下", "大专", "本科", "硕士", "博士"]
PHYSICAL_LEVELS = ["light", "medium", "heavy"]

def normalize_education(edu: str) -> str:
    """将各种学历描述归一化为 EDUCATION_LEVELS 中的一个"""
    for level in EDUCATION_LEVELS:
        if level in edu:
            return level
    return "大专以下"

def find_industry_info(industry_name: str) -> dict:
    """精确或模糊查找行业信息，找不到返回空字典"""
    if industry_name in INDUSTRY_DATABASE:
        return INDUSTRY_DATABASE[industry_name]
    # 模糊匹配：行业名包含数据库键，或数据库键包含行业名
    for db_key, info in INDUSTRY_DATABASE.items():
        if industry_name in db_key or db_key in industry_name:
            return info
    return {}

def education_filter(user_edu: str, industry_name: str) -> bool:
    """检查用户学历是否满足行业最低要求（支持模糊匹配行业名）"""
    industry = find_industry_info(industry_name)
    if not industry:
        return True          # 未知行业，放行
    req = industry.get("学历要求", "不限")
    if req == "不限":
        return True
    # 取最低要求（如 "本科-硕士" → "本科"，"本科（医学）" → "本科"）
    min_req = req.split("-")[0].split("（")[0].strip()
    if min_req not in EDUCATION_LEVELS:
        return True
    return EDUCATION_LEVELS.index(normalize_education(user_edu)) >= EDUCATION_LEVELS.index(min_req)

def physical_filter(user_cap: str, industry_name: str) -> bool:
    """检查用户体力能否承受行业要求（支持模糊匹配行业名）"""
    if user_cap not in PHYSICAL_LEVELS:
        user_cap = "light"
    industry = find_industry_info(industry_name)
    if not industry:
        return True          # 未知行业，放行
    req = industry.get("体力要求", "light")
    if req not in PHYSICAL_LEVELS:
        req = "light"
    return PHYSICAL_LEVELS.index(user_cap) >= PHYSICAL_LEVELS.index(req)

def filter_industries_by_constraints(industries: list, user_edu: str, user_physical: str):
    """
    对 AI 推荐的行业列表进行硬性过滤（学历 + 体力）
    - 未知行业（数据库中查不到）：标记 isUnknownIndustry=True 并保留
    - 已知行业：通过学历+体力双重过滤
    返回：(过滤后的行业列表, 调整说明字符串)
    """
    if not industries:
        return industries, ""

    def get_name(ind):
        return ind["name"] if isinstance(ind, dict) else ind

    original_list = [get_name(i) for i in industries]
    filtered = []
    for ind in industries:
        name = get_name(ind)
        info = find_industry_info(name)
        if not info:
            # 未知行业：标记并保留，避免误删
            if isinstance(ind, dict):
                ind = dict(ind)   # 浅拷贝，避免污染缓存原始数据
                ind["isUnknownIndustry"] = True
            filtered.append(ind)
            print(f"[FILTER] 未知行业（保留+标记）: {name}")
        elif education_filter(user_edu, name) and physical_filter(user_physical, name):
            filtered.append(ind)
        else:
            print(f"[FILTER] 行业已过滤（学历/体力不符）: {name}")

    note = ""
    if not filtered:
        filtered = industries  # 降级：全放行
        note = "无完全符合学历/体力要求的行业，已展示原始推荐"
    elif len(filtered) < len(industries):
        removed_first = original_list[0] not in [get_name(i) for i in filtered]
        if removed_first and filtered:
            note = f"因学历/体力限制，原推荐《{original_list[0]}》已调整为《{get_name(filtered[0])}》"
    return filtered, note

def parse_user_profile(answers: dict, questions: list) -> dict:
    """
    从答案中提取关键用户画像（学历、体力能力）
    返回 {"education": "本科", "physical_cap": "light"}
    """
    profile = {"education": "大专以下", "physical_cap": "light"}
    for q_idx, q in enumerate(questions):
        q_text = q.get("text", "")
        user_ans = answers.get(str(q_idx)) or answers.get(q_idx)
        if not user_ans:
            continue

        # 学历提取
        if "学历" in q_text:
            for opt in q.get("options", []):
                if opt.get("value") == user_ans or opt.get("label") == user_ans:
                    label = opt.get("label", "")
                    if "博士" in label:
                        profile["education"] = "博士"
                    elif "硕士" in label:
                        profile["education"] = "硕士"
                    elif "本科" in label:
                        profile["education"] = "本科"
                    elif "大专" in label:
                        profile["education"] = "大专"
                    else:
                        profile["education"] = "大专以下"
                    break

        # 体力提取（包含"体力"/"体能"/"劳动强度"/"身体条件"的题目）
        if any(kw in q_text for kw in ["体力", "体能", "劳动强度", "身体条件"]):
            for opt in q.get("options", []):
                if opt.get("value") == user_ans or opt.get("label") == user_ans:
                    label = opt.get("label", "").lower()
                    if any(w in label for w in ["重", "强", "高强度"]):
                        profile["physical_cap"] = "heavy"
                    elif any(w in label for w in ["中", "中等"]):
                        profile["physical_cap"] = "medium"
                    else:
                        profile["physical_cap"] = "light"
                    break
    return profile

# ==================== persona 代码映射（轻量版专用） ====================
# AI 返回的 persona.value 可能是英文代码，前端直接渲染会导致显示异常
# 此映射表用于在结果返回前端前做清洗
PERSONA_CODE_MAP = {
    # 职业背景代码
    "tech_rd": "技术研发",
    "tech_prod": "生产制造",
    "tech_medical": "医疗健康",
    "tech_finance": "金融财务",
    "tech_edu": "教育培训",
    "market": "市场营销",
    "manage": "职能管理",
    "media": "媒体创意",
    "labor": "体力劳动",
    "service": "服务类",
    "retail": "销售零售",
    "self_emp": "个体经营",
    "driver": "司机运输",
    "agri": "农林牧渔",
    "support": "保安保洁",
    "gig": "自由职业",
    "data_ai": "数据分析/AI",
    "hardware": "硬件/嵌入式",
    "professional": "专业资质",
    "manage_skill": "项目管理",
    "sales": "沟通销售",
    "creative": "内容创作/设计",
    "ecommerce": "直播电商",
    "delivery": "快递配送",
    "transport": "货运客运",
    "service_manage": "服务管理",
    "construction": "建筑装修",
    "driving": "驾驶运输",
    # 学历/专业背景代码
    "cs": "计算机",
    "engineering": "理工科",
    "medical": "医学",
    "finance": "金融",
    "arts": "文科",
    "business": "商科",
    "art": "艺术",
    "edu": "教育",
    "vocational": "职业技术",
    "other": "其他"
}

def clean_persona_codes(result: dict) -> dict:
    """清洗 persona 中的英文代码为中文标签"""
    if not result.get("persona"):
        return result
    try:
        for p in result["persona"]:
            if isinstance(p, dict) and "value" in p:
                v = p["value"]
                # 如果 value 看起来像代码（纯字母+下划线），尝试映射
                if isinstance(v, str) and v.replace("_", "").isalpha() and v in PERSONA_CODE_MAP:
                    original = v
                    p["value"] = PERSONA_CODE_MAP[v]
                    print(f"[CLEAN] persona代码转换: {original} → {p['value']}")
        print(f"[CLEAN] persona清洗完成，共处理 {len(result['persona'])} 项")
    except Exception as e:
        print(f"[CLEAN] persona清洗异常: {e}")
    return result

# ==================== 答案数据清洗 + 错误追踪 ====================

# 已知合法选项集合（基于问题关键字匹配）
ANSWER_VALIDATION_RULES = {
    "出国态度": {"考虑出国", "不确定", "不考虑"},
    "学历": {"大专以下", "大专", "本科", "硕士", "博士"},
    "外语水平": {"英语+小语种", "英语精通", "英语一般", "不擅长"},
}

def log_invalid_answer(q_index: int, q_text: str, original: str, corrected: str, user_type: str):
    """记录非法答案到数据库"""
    try:
        conn, cursor = db_execute(
            "INSERT INTO invalid_answer_records (q_index, q_text, original_value, corrected_value, user_type) VALUES (?, ?, ?, ?, ?)",
            (q_index, q_text, original, corrected, user_type)
        )
        conn.commit()
        conn.close()
        print(f"[CLEAN] 记录异常答案: q{q_index}「{q_text[:20]}」{original} → {corrected}")
    except Exception as e:
        print(f"[CLEAN] 记录失败: {e}")

def clean_answers(questions: list, answers: dict, user_type: str) -> dict:
    """
    基于问题文本关键字对答案进行清洗
    - 若答案不在合法值集合中，尝试从选项中匹配，找不到则取中间值
    - 记录所有异常到 invalid_answer_records 表
    """
    cleaned = dict(answers)
    for q_idx, q in enumerate(questions):
        q_text = q.get("text", "")
        ans_key = str(q_idx)
        original = cleaned.get(ans_key)
        if not original:
            continue

        for keyword, valid_values in ANSWER_VALIDATION_RULES.items():
            if keyword in q_text and original not in valid_values:
                corrected = None
                # 尝试从选项中找到正确的 value
                for opt in q.get("options", []):
                    if opt.get("value") == original or opt.get("label") == original:
                        if opt.get("value") in valid_values:
                            corrected = opt["value"]
                            break
                if corrected is None:
                    vals = list(valid_values)
                    corrected = vals[len(vals) // 2]  # 取中间值作为兜底
                cleaned[ans_key] = corrected
                log_invalid_answer(q_idx, q_text, original, corrected, user_type)
                break  # 只匹配第一条规则
    return cleaned

async def generate_ai_background(user_type: int, answers: dict, questions: list, 
                                  version: str, cache_key: str):
    """
    后台异步生成AI分析结果
    
    Args:
        user_type: 用户类型（1/2/3）
        answers: 用户答题数据
        questions: 问题列表
        version: 版本（light/deep/vip）
        cache_key: 缓存Key
    """
    print(f"[BG] ===== 后台生成开始: {version}_{user_type} - {cache_key[:8]}... =====")
    print(f"[BG] 时间戳: {time.time()}")
    start_time = time.time()
    
    try:
        # 根据版本选择提示词构建函数
        print(f"[BG] 开始构建提示词...")
        if version == "light":
            prompt = build_analysis_prompt(user_type, answers, questions)
        else:
            prompt = build_deep_analysis_prompt(user_type, answers, questions)
        print(f"[BG] 提示词构建完成，长度: {len(prompt)} 字符")
        
        # 调用AI API（异步版本）
        print(f"[BG] 开始调用 AI API...")
        api_start = time.time()
        content = await call_ai_api(prompt)
        api_elapsed = time.time() - api_start
        print(f"[BG] AI API 调用完成，耗时: {api_elapsed:.1f}秒，返回内容长度: {len(content) if content else 0}")
        
        if content is None:
            print(f"[BG] ❌ AI API调用失败，跳过缓存保存")
            return
        
        # 解析AI结果
        print(f"[BG] 开始解析 JSON 响应...")
        result = parse_json_response(content)
        print(f"[BG] JSON 解析完成，keys: {list(result.keys()) if result else 'None'}")

        # ============================================================
        # 统一处理不同版本的输出格式（轻量 / 深度 / VIP）
        # ============================================================
        if version == "light":
            # ---- 轻量版：只保留一个行业，补全缺失字段 ----
            industries = result.get('recommendedIndustries', [])
            if len(industries) > 1:
                first_industry = industries[0]
                first_industry_name = first_industry.get('name', '待定')
                result['recommendedIndustries'] = [first_industry]

                # 兼容旧格式 summary
                if 'summary' in result:
                    summary = result['summary']
                    if 'result' in summary:
                        result_text = summary['result']
                        score_match = re.search(r'打分\\s*(\\d+)\\s*分', result_text)
                        score_text = f"打分{score_match.group(1)}分" if score_match else ""
                        summary['result'] = f"【分析结论】推荐转型到{first_industry_name}，{score_text}。"
                    if 'recommendedIndustries' in summary:
                        summary['recommendedIndustries'] = [first_industry_name]

            # 确保轻量版也有 summary（即使 AI 没给）
            if 'summary' not in result:
                first_name = result['recommendedIndustries'][0]['name'] if result.get('recommendedIndustries') else '待定'
                result['summary'] = {
                    'analysis': result.get('overallAnalysis', ''),
                    'result': f"推荐转型到{first_name}",
                    'short': first_name,
                    'overallScore': '由AI综合评估'
                }
                result.pop('overallAnalysis', None)  # 清理中间字段

            # 补全前端必用字段
            result.setdefault('macroTrends', [])
            result.setdefault('persona', [])
            result.setdefault('risks', [])

            # ---- persona 代码清洗：轻量版在硬性过滤之前处理 ----
            result = clean_persona_codes(result)

        elif version in ("deep", "vip"):
            # VIP 版加标识
            if version == "vip":
                result['_isVip'] = True

        # ---- 硬性过滤：学历 + 体力约束 ----
        if result.get("recommendedIndustries"):
            try:
                user_profile = parse_user_profile(answers, questions)
                filtered_industries, adjustment_note = filter_industries_by_constraints(
                    result["recommendedIndustries"],
                    user_profile["education"],
                    user_profile["physical_cap"]
                )
                result["recommendedIndustries"] = filtered_industries
                if adjustment_note:
                    if isinstance(result.get("summary"), dict):
                        result["summary"]["adjustmentNote"] = adjustment_note
                    else:
                        result.setdefault("summary", {})
                        result["summary"]["adjustmentNote"] = adjustment_note
                    print(f"[BG] 🔧 行业过滤调整: {adjustment_note}")
            except Exception as fe:
                print(f"[BG] ⚠️ 行业过滤异常（跳过）: {fe}")

        # 保存到缓存
        print(f"[BG] 开始保存到缓存...")
        set_cache(answers, result, version, user_type, cache_key)
        print(f"[BG] 缓存保存完成")
        
        elapsed = time.time() - start_time
        print(f"[BG] ✅ 后台生成完成: {version}_{user_type} - {cache_key[:8]}... ({elapsed:.1f}秒)")
        
    except Exception as e:
        print(f"[BG] ❌ 后台生成异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保清理生成标记
        print(f"[BG] 清理生成标记: {cache_key[:8]}...")
        finish_generating(cache_key)
        print(f"[BG] ===== 后台生成结束 =====")

# ============================================
# 家长版 System Prompt（分析对象：孩子）
# ============================================
PARENT_SYSTEM_PROMPT = """你是一位资深的青少年职业规划顾问。你的分析对象是**孩子**，不是家长本人。

## 轻量版题型（家长会回答其中3题）
- Q3: 孩子类型 [理科工科/文科商科/艺术创意/职业技术]
- Q4: 最看重什么 [就业前景/兴趣意愿/稳定安全/薪资潜力]
- Q5: 出国态度 [考虑出国/不确定/不考虑]

## 深度版额外题型
- Q8: 家庭年收入 [50万+/30-50万/15-30万/15万以下]
- Q12: 发展城市 [一线/新一线/老家/无所谓/海外]
- Q13: 出国态度（详细版）

## 分析维度
1. 孩子类型与行业匹配：理科→AI/半导体/新能源；文科→出海/内容创作/金融科技；艺术→AI设计/数字艺术/UX；职技→智能制造/新能源技术/数控
2. 面向未来10-15年推荐方向，考虑行业前景和反脆弱性
3. 结合家长最看重的点（就业vs兴趣vs稳定）给出推荐
4. 结合家庭收入、教育预算、出国意愿推荐路径

## 输出格式（严格 JSON，禁止用代码块包裹）
{
  "summary": {
    "overallScore": "综合匹配度评分：XX分",
    "recommendedIndustries": ["行业名称"],
    "analysis": "综合分析（100-150字，真实内容，禁用占位符）",
    "result": "分析结论（60-100字，真实内容，禁用占位符）",
    "short": "一句话总结"
  },
  "macroTrends": [
    {
      "trend": "行业趋势名称",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "analysis": "趋势分析（80-120字，需真实数据，禁用占位符）"
    }
  ],
  "persona": [
    {"label": "你现在的状态", "value": "基于答题数据的真实分析"},
    {"label": "你擅长什么", "value": "基于答题数据的真实分析"},
    {"label": "你适合什么", "value": "基于答题数据的真实分析"},
    {"label": "现在能做什么", "value": "基于答题数据的真实分析"}
  ],
  "recommendedIndustries": [
    {
      "name": "行业名称（必须从已知行业数据库中选择）",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "matchScore": "XX分",
      "reason": "推荐原因（15-30字）",
      "matchReason": "匹配分析（100-150字）",
      "hotRoles": ["岗位名称（月薪范围）"],
      "entryTips": "入行指南（真实可操作步骤）",
      "salaryRange": "入职薪资范围 → 3年后薪资范围"
    }
  ],
  "risks": ["风险描述1（真实具体）", "风险描述2（真实具体）"]
}
硬性约束：
1. 所有字段必须输出，缺一个则报告不合格
2. 严禁使用 XX、xxx、待定、未知、暂无、TBD 等任何占位符
3. recommendedIndustries 数组只能有 1 个行业
4. macroTrends 数组只能有 1 个趋势
5. persona 数组必须恰好 4 个条目
6. 行业名称必须从提供的行业数据库中选择"""
PARENT_SYSTEM_PROMPT = """你是一位资深的青少年职业规划顾问。你的分析对象是**孩子**，不是家长本人。

## 轻量版题型（家长会回答其中3题）
- Q3: 孩子类型 [理科工科/文科商科/艺术创意/职业技术]
- Q4: 最看重什么 [就业前景/兴趣意愿/稳定安全/薪资潜力]
- Q5: 出国态度 [考虑出国/不确定/不考虑]

## 深度版额外题型
- Q8: 家庭年收入 [50万+/30-50万/15-30万/15万以下]
- Q12: 发展城市 [一线/新一线/老家/无所谓/海外]
- Q13: 出国态度（详细版）

## 分析维度
1. 孩子类型与行业匹配：理科→AI/半导体/新能源；文科→出海/内容创作/金融科技；艺术→AI设计/数字艺术/UX；职技→智能制造/新能源技术/数控
2. 面向未来10-15年推荐方向，考虑行业前景和反脆弱性
3. 结合家长最看重的点（就业vs兴趣vs稳定）给出推荐
4. 结合家庭收入、教育预算、出国意愿推荐路径

## 输出格式（严格 JSON，禁止用代码块包裹）
{
  "summary": {
    "overallScore": "综合匹配度评分：XX分",
    "recommendedIndustries": ["行业名称"],
    "analysis": "综合分析（100-150字，真实内容，禁用占位符）",
    "result": "分析结论（60-100字，真实内容，禁用占位符）",
    "short": "一句话总结"
  },
  "macroTrends": [
    {
      "trend": "行业趋势名称",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "analysis": "趋势分析（80-120字，需真实数据，禁用占位符）"
    }
  ],
  "persona": [
    {"label": "你现在的状态", "value": "基于答题数据的真实分析"},
    {"label": "你擅长什么", "value": "基于答题数据的真实分析"},
    {"label": "你适合什么", "value": "基于答题数据的真实分析"},
    {"label": "现在能做什么", "value": "基于答题数据的真实分析"}
  ],
  "recommendedIndustries": [
    {
      "name": "行业名称（必须从已知行业数据库中选择）",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "matchScore": "XX分",
      "reason": "推荐原因（15-30字）",
      "matchReason": "匹配分析（100-150字）",
      "hotRoles": ["岗位名称（月薪范围）"],
      "entryTips": "入行指南（真实可操作步骤）",
      "salaryRange": "入职薪资范围 → 3年后薪资范围"
    }
  ],
  "risks": ["风险描述1（真实具体）", "风险描述2（真实具体）"]
}
硬性约束：
1. 所有字段必须输出，缺一个则报告不合格
2. 严禁使用 XX、xxx、待定、未知、暂无、TBD 等任何占位符
3. recommendedIndustries 数组只能有 1 个行业
4. macroTrends 数组只能有 1 个趋势
5. persona 数组必须恰好 4 个条目
6. 行业名称必须从提供的行业数据库中选择
7. persona 数组中每个 value 必须是中文自然语言，严禁输出内部代码（如 tech_finance）
8. risks 数组中每个元素必须是字符串，不能是对象"""

# ============================================
# 30-40 岁转型版 System Prompt
# ============================================
CAREER_SYSTEM_PROMPT = """你是一位资深的职业转型顾问，擅长为30-40岁职场人提供可落地的转型方案。

## 轻量版题型（用户会回答其中3题）
- Q2: 最高学历 [大专以下/大专/本科/硕士/博士]
- Q3: 职业背景 [技术研发/生产制造/医疗健康/金融财务/教育培训/市场营销/职能管理/媒体创意/体力劳动/服务类/销售零售/个体经营/司机运输/农林牧渔/保安保洁/自由职业]
- Q8: 专业技能 [数据分析AI/硬件机械/财务法务/运营项目/沟通销售/内容设计/直播电商/快递配送/货运客运/餐饮零售/建筑装修/纯体力]

## 深度版额外题型
- Q16: 兴趣方向 [AI大模型/新能源储能/出海跨境/医疗健康/金融科技/机器自动化/低空经济/不确定]
- Q14: 英语水平 [精通/良好/一般/较差]

## 分析维度
1. 技能可迁移性：用户的职业背景和专业技能能迁移到哪些行业？
2. 学历与门槛：学历是否匹配目标行业的入门要求？
3. 年龄与学习成本：30-40岁转型需要考虑学习周期和年龄歧视风险
4. 经济压力：经济压力大时优先推荐能快速上手、收入稳定的方向
5. 兴趣与长期发展：结合用户表达的兴趣方向，判断是否值得长期投入

## 输出格式（严格 JSON，禁止用代码块包裹）
{
  "summary": {
    "overallScore": "综合匹配度评分：XX分",
    "recommendedIndustries": ["行业名称"],
    "analysis": "综合分析（100-150字，真实内容，禁用占位符）",
    "result": "分析结论（60-100字，真实内容，禁用占位符）",
    "short": "一句话总结"
  },
  "macroTrends": [
    {
      "trend": "行业趋势名称",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "analysis": "趋势分析（80-120字，需真实数据，禁用占位符）"
    }
  ],
  "persona": [
    {"label": "你现在的状态", "value": "基于答题数据的真实分析"},
    {"label": "你擅长什么", "value": "基于答题数据的真实分析"},
    {"label": "你适合什么", "value": "基于答题数据的真实分析"},
    {"label": "现在能做什么", "value": "基于答题数据的真实分析"}
  ],
  "recommendedIndustries": [
    {
      "name": "行业名称（必须从已知行业数据库中选择）",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "matchScore": "XX分",
      "reason": "推荐原因（15-30字）",
      "matchReason": "匹配分析（100-150字）",
      "hotRoles": ["岗位名称（月薪范围）"],
      "entryTips": "入行指南（真实可操作步骤）",
      "salaryRange": "入职薪资范围 → 3年后薪资范围"
    }
  ],
  "risks": ["风险描述1（真实具体）", "风险描述2（真实具体）"]
}
硬性约束：
1. 所有字段必须输出，缺一个则报告不合格
2. 严禁使用 XX、xxx、待定、未知、暂无、TBD 等任何占位符
3. recommendedIndustries 数组只能有 1 个行业
4. macroTrends 数组只能有 1 个趋势
5. persona 数组必须恰好 4 个条目
6. 行业名称必须从提供的行业数据库中选择
7. persona 数组中每个 value 必须是中文自然语言，严禁输出内部代码（如 tech_finance）
8. risks 数组中每个元素必须是字符串，不能是对象"""

# ============================================
# 应届生版 System Prompt
# ============================================
GRADUATE_SYSTEM_PROMPT = """你是一位资深的应届生职业规划顾问，擅长为毕业生提供第一份工作的方向建议。

## 轻量版题型（用户会回答其中3题）
- Q1: 学历背景 [大专以下/大专/本科/硕士/博士]
- Q2: 专业属于 [理工科/文科/商科/技校职高/无专业/服务业技能]
- Q5: 外语水平 [英语+小语种/英语精通/英语一般/不擅长]

## 深度版额外题型
- Q6: 地域偏好 [一线城市/新一线/二线/回老家/无所谓]
- Q12: 编程能力 [精通/熟练/一般/不会]
- Q17: 5年后期望 [大公司/创业/出海/技术专家/小事业/没想清楚]

## 分析维度
1. 专业与行业匹配：理工科适合技术赛道，文科适合出海/内容/运营，商科适合金融/分析
2. 学历与起点：不同学历对应不同的入行起点和薪资预期
3. 外语能力：外语好可以走国际化/出海方向
4. 长期发展：结合5年后期望，推荐有积累效应的方向
5. 地域偏好：结合用户想去的城市推荐当地有优势的产业

## 输出格式（严格 JSON，禁止用代码块包裹）
{
  "summary": {
    "overallScore": "综合匹配度评分：XX分",
    "recommendedIndustries": ["行业名称"],
    "analysis": "综合分析（100-150字，真实内容，禁用占位符）",
    "result": "分析结论（60-100字，真实内容，禁用占位符）",
    "short": "一句话总结"
  },
  "macroTrends": [
    {
      "trend": "行业趋势名称",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10年以上/6-8年/3-5年",
      "analysis": "趋势分析（80-120字，需真实数据，禁用占位符）"
    }
  ],
  "persona": [
    {"label": "你现在的状态", "value": "基于答题数据的真实分析"},
    {"label": "你擅长什么", "value": "基于答题数据的真实分析"},
    {"label": "你适合什么", "value": "基于答题数据的真实分析"},
    {"label": "现在能做什么", "value": "基于答题数据的真实分析"}
  ],
  "recommendedIndustries": [
    {
      "name": "行业名称（必须从已知行业数据库中选择）",
      "outlook": "长期看好/中期看好/短期过渡",
      "period": "10岁以上/6-8年/3-5年",
      "matchScore": "XX分",
      "reason": "推荐原因（15-30字）",
      "matchReason": "匹配分析（100-150字）",
      "hotRoles": ["岗位名称（月薪范围）"],
      "entryTips": "入行指南（真实可操作步骤）",
      "salaryRange": "入职薪资范围 → 3年后薪资范围"
    }
  ],
  "risks": ["风险描述1（真实具体）", "风险描述2（真实具体）"]
}
硬性约束：
1. 所有字段必须输出，缺一个则报告不合格
2. 严禁使用 XX、xxx、待定、未知、暂无、TBD 等任何占位符
3. recommendedIndustries 数组只能有 1 个行业
4. macroTrends 数组只能有 1 个趋势
5. persona 数组必须恰好 4 个条目
6. 行业名称必须从提供的行业数据库中选择
7. persona 数组中每个 value 必须是中文自然语言，严禁输出内部代码（如 tech_finance）
8. risks 数组中每个元素必须是字符串，不能是对象"""

# 行业数据库（内置，包含所有细分行业，全行业覆盖）
# 【专业点评整合】每个行业可包含：专业点评、点评说明、适合人群、就业特点、性别倾向
INDUSTRY_DATABASE = {
    # ========== 第一产业 ==========
    "农业/种植业": {
        "trends": ["智慧农业", "订单农业", "品牌农业"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["农业技术", "电商运营", "品牌管理", "供应链"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["务实型", "耐心型"]
    },
    "畜牧业/养殖业": {
        "trends": ["规模化养殖", "绿色养殖", "深加工"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["养殖技术", "兽医", "食品加工", "销售"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "中",
        "适合性格": ["务实型", "耐心型"]
    },
    "农业服务/农资": {
        "trends": ["农技服务", "农业金融", "农机器具"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["农技推广", "农机销售", "农业保险", "农资电商"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["社交型", "服务型"]
    },

        # ========== 第二产业 ==========
        # 科技/互联网
        "人工智能/大数据": {
        "trends": ["大模型应用爆发", "AI赋能千行百业", "数据要素市场化"],
        "salary": "高",
        "growth": "高速增长",
        "hot_roles": ["算法工程师", "AI产品经理", "数据工程师", "MLOps工程师"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["逻辑型", "分析型", "创新型"],
        # 专业点评
        "专业点评": "高分能学好、低分赶紧跑",
        "点评说明": "高学历（硕士及以上）做AI算法研发方向，低学历转做AI应用落地、实施、运维等方向",
        "适合人群": ["高学历", "理工科", "数学好"],
        "就业特点": "算法岗门槛极高、应用岗需求大"
    },
    "软件开发/互联网": {
        "trends": ["AI赋能转型", "行业整体下行", "基础岗位收缩", "AI+应用有机会"],
        "salary": "中高（但两极分化）",
        "growth": "短期过渡到中期",
        "周期说明": "互联网整体在下行，只能往AI方向短期到中期可以，长期不确定",
        "hot_roles": ["AI工程师", "算法工程师", "数据工程师", "产品经理", "AI应用开发"],
        "学历要求": "本科",
        "入门门槛": "高",
        "适合性格": ["逻辑型", "创新型"],
        "风险提示": "传统开发岗位需求下降，非AI方向长期风险高",
        # 专业点评
        "专业点评": "不拼爹、不看脸，普通家庭都是首选",
        "点评说明": "靠技术能力吃饭，不需要背景资源，适合普通家庭出身的年轻人",
        "适合人群": ["普通家庭", "普通学历", "愿意拼搏"],
        "就业特点": "不看背景只看能力，收入与付出成正比",
        "加分标签": ["普通家庭"]
    },
    "云计算/基础设施": {
        "trends": ["多云部署", "边缘计算", "Serverless"],
        "salary": "高",
        "growth": "稳定增长",
        "hot_roles": ["云架构师", "SRE", "网络安全", "DBA"],
        "学历要求": "本科-硕士",
        "入门门槛": "中高",
        "适合性格": ["逻辑型", "系统型"]
    },
    "物联网/智能硬件": {
        "trends": ["智能家居", "车联网", "工业物联网"],
        "salary": "中高",
        "growth": "稳定增长",
        "hot_roles": ["嵌入式开发", "硬件工程", "IoT产品", "传感技术"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["技术型", "创新型"],
        # 专业点评（来自电子信息工程 + 物联网工程）
        "专业点评": "要高分、要考研，未来就业不犯难；万物互联、资源整合",
        "点评说明": "电子信息/物联网需要扎实基础，高学历有优势；行业涉及跨领域整合",
        "适合人群": ["高学历", "理工科", "系统思维"],
        "就业特点": "门槛较高但前景好，越老越值钱"
    },
    "网络安全": {
        "trends": ["数据安全", "云安全", "合规驱动"],
        "salary": "高",
        "growth": "高速增长",
        "hot_roles": ["安全工程师", "渗透测试", "安全运营", "合规审计"],
        "学历要求": "本科",
        "入门门槛": "中高",
        "适合性格": ["逻辑型", "分析型"],
        # 专业点评（来自信息安全）
        "专业点评": "学的多、用的广，就业都是高薪岗",
        "点评说明": "网络安全知识体系庞大，应用场景广，从业者薪资普遍较高",
        "适合人群": ["理工科", "逻辑思维强", "持续学习"],
        "就业特点": "岗位稀缺、薪资高、越老越吃香"
    },
    "通信/电信": {
        "trends": ["5G应用", "光通信", "卫星互联网"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["网络优化", "通信工程", "运营商", "通信设备"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["技术型", "务实型"],
        # 专业点评（来自网络工程）
        "专业点评": "布网线、建网络，弱电工程都能做",
        "点评说明": "网络工程主要做网络搭建和弱电工程，基础但不可或缺",
        "适合人群": ["技术型", "动手能力强"],
        "就业特点": "稳定但薪资上限不高，越老越需要转型"
    },
    
    # 制造业
    "半导体/芯片": {
        "trends": ["国产替代", "先进制程", "芯片设计"],
        "salary": "高",
        "growth": "高速增长",
        "hot_roles": ["芯片设计", "工艺工程师", "封装测试", "FAE"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["技术型", "严谨型"]
    },
    "新能源汽车/智能汽车": {
        "trends": ["电动化", "智能化", "出海加速"],
        "salary": "中高",
        "growth": "高速增长",
        "hot_roles": ["电池工程师", "自动驾驶", "智能座舱", "海外市场"],
        "学历要求": "本科-硕士",
        "入门门槛": "中高",
        "适合性格": ["技术型", "创新型"]
    },
    "智能制造/工业4.0": {
        "trends": ["数字化工厂", "机器人应用", "柔性生产"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["自动化工程师", "PLC开发", "MES实施", "工业数据"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["技术型", "务实型"],
        # 专业点评（来自自动化）
        "专业点评": "岗位多、万金油，就业一般不用愁",
        "点评说明": "自动化专业应用广泛，各行各业都需要，就业选择多，不愁找不到工作",
        "适合人群": ["工科生", "技术型", "动手能力强"],
        "就业特点": "万金油专业，哪里都需要，转型容易"
    },
    "传统制造/机械": {
        "trends": ["自动化升级", "出海布局", "供应链优化"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["工艺工程师", "设备管理", "质量管理", "供应链"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "中",
        "适合性格": ["务实型", "技术型"],
        # 专业点评（来自机械类）
        "专业点评": "拧螺丝、扳电闸，工厂车间一大把",
        "点评说明": "机械类专业主要在工厂车间工作，从基础操作到技术管理都有对应岗位",
        "适合人群": ["技术型", "动手型", "男生"],
        "就业特点": "工厂为主，工作环境一般，但稳定",
        "性别倾向": "男生"
    },
    "航空航天": {
        "trends": ["商业航天", "低轨卫星", "无人机"],
        "salary": "高",
        "growth": "快速增长",
        "hot_roles": ["飞行器设计", "航电系统", "发射技术", "卫星应用"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["技术型", "严谨型"]
    },
    "国防军工": {
        "trends": ["军民融合", "信息化", "装备升级"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["研发工程师", "项目管理", "质量管理", "技术支持"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["严谨型", "爱国型"]
    },
    "化工/新材料": {
        "trends": ["新能源材料", "新材料研发", "绿色化工"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["化工研发", "工艺工程", "质量控制", "安全工程"],
        "学历要求": "本科-硕士",
        "体力要求": "medium",
        "入门门槛": "中",
        "适合性格": ["技术型", "严谨型"]
    },
    "石油/能源": {
        "trends": ["能源转型", "新能源布局", "数字化油田"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["石油工程", "新能源技术", "项目管理", "安全管理"],
        "学历要求": "本科-硕士",
        "体力要求": "medium",
        "入门门槛": "中",
        "适合性格": ["技术型", "务实型"]
    },
    "电力/电网": {
        "trends": ["新型电力系统", "智能电网", "新能源消纳"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["电气工程师", "电网调度", "新能源运维", "售电"],
        "学历要求": "本科",
        "体力要求": "medium",
        "入门门槛": "中",
        "适合性格": ["技术型", "稳健型"],
        # 专业点评（来自电气工程 + 电力铁路两个专业）
        "专业点评": "毕业就进央国企、七险两金全都有；低分专属、男生优先",
        "点评说明": "电力电网是央国企集中地，工作稳定福利好；低学历（大专及以下）男生也有机会进入",
        "适合人群": ["男生", "低学历", "追求稳定", "普通家庭"],
        "就业特点": "央国企为主，铁饭碗，福利好，但晋升慢",
        "性别倾向": "男生优先",
        "加分标签": ["低分专属", "男生优先", "普通家庭", "追求稳定"]
    },
    "服装/纺织": {
        "trends": ["国潮品牌", "功能性面料", "智能制造"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["设计师", "供应链管理", "电商运营", "品牌策划"],
        "学历要求": "大专-本科",
        "入门门槛": "低",
        "适合性格": ["创意型", "务实型"]
    },
    "家具/家居": {
        "trends": ["智能家居", "全屋定制", "出海品牌"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["产品设计", "定制设计", "供应链", "电商运营"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["创意型", "务实型"]
    },
    
    # 建筑业
    "房地产/物业": {
        "trends": ["存量运营", "物业科技", "城市更新"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["运营管理", "资产管理", "物业经理", "招商"],
        "学历要求": "大专-本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "务实型"]
    },
    "建筑设计/工程": {
        "trends": ["绿色建筑", "BIM应用", "智能建造"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["建筑设计师", "项目经理", "造价工程师", "BIM"],
        "学历要求": "本科",
        "体力要求": "medium",
        "入门门槛": "中",
        "适合性格": ["技术型", "创意型"],
        # 专业点评（来自工程造价 + 土木工程）
        "专业点评": "走下坡、岗位少，加班熬夜少不了；进工地、国外跑",
        "点评说明": "房地产下行导致建筑设计行业整体收缩，岗位减少，加班严重；土木工程更是要去工地或出国",
        "适合人群": ["能吃苦", "不在意工作环境"],
        "就业特点": "行业下行，建议谨慎选择或考虑转型",
        "风险提示": "行业整体走下坡路，非必要不推荐"
    },
    "装修/装饰": {
        "trends": ["整装趋势", "智能家居", "环保材料"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["设计师", "项目管理", "材料采购", "营销"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["创意型", "社交型"]
    },
    
    # ========== 第三产业 ==========
    # 金融
    "金融科技": {
        "trends": ["数字人民币", "区块链应用", "智能风控"],
        "salary": "高",
        "growth": "快速增长",
        "hot_roles": ["量化分析师", "风控模型", "支付系统", "合规科技"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["分析型", "风险型"],
        # 专业点评（来自统计学）
        "专业点评": "精算师、互联网，数学不好想一想",
        "点评说明": "统计学可以做金融精算方向，也可以去互联网做数据分析，但需要数学基础好",
        "适合人群": ["数学好", "逻辑思维强", "高学历"],
        "就业特点": "高薪岗位，但需要扎实数学功底"
    },
    "投资/私募/风投": {
        "trends": ["硬科技投资", "ESG投资", "产业投资"],
        "salary": "高+提成",
        "growth": "稳健",
        "hot_roles": ["投资经理", "行业研究员", "投后管理", "IR"],
        "学历要求": "硕士优先",
        "入门门槛": "高",
        "适合性格": ["社交型", "分析型"]
    },
    "银行/保险": {
        "trends": ["数字化转型", "财富管理", "普惠金融"],
        "salary": "中高",
        "growth": "稳健",
        "hot_roles": ["理财顾问", "客户经理", "风控", "产品经理"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "稳健型"]
    },
    "证券/基金": {
        "trends": ["财富管理", "量化投资", "注册制改革"],
        "salary": "高",
        "growth": "稳健",
        "hot_roles": ["分析师", "基金经理", "投顾", "机构销售"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["分析型", "竞争型"]
    },
    "信托/资产管理": {
        "trends": ["净值化转型", "另类投资", "家族信托"],
        "salary": "高",
        "growth": "稳健",
        "hot_roles": ["信托经理", "资产配置", "风控", "家族财富"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["分析型", "稳健型"]
    },
    
    # 医疗健康
    "生物医药": {
        "trends": ["创新药研发", "细胞基因治疗", "AI药物发现"],
        "salary": "中高",
        "growth": "快速增长",
        "hot_roles": ["药物研发", "临床运营", "注册事务", "医学顾问"],
        "学历要求": "硕士优先",
        "入门门槛": "高",
        "适合性格": ["研究型", "严谨型"],
        # 专业点评（来自临床医学）
        "专业点评": "前期苦，后期牛，家庭不好别选它",
        "点评说明": "临床医学需要长周期学习（5+3年），前期投入大后期回报高，家庭经济压力大需谨慎",
        "适合人群": ["高学历", "家庭支持", "长期主义"],
        "就业特点": "周期长、投入大，但后期社会地位高、收入稳定",
        "加分标签": ["长期主义"]
    },
    "医疗器械": {
        "trends": ["国产替代", "高端设备", "家用医疗"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["产品经理", "注册专员", "临床支持", "销售"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["务实型", "社交型"]
    },
    "医疗服务/医院": {
        "trends": ["专科连锁", "互联网医院", "健康管理"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["医生", "医院管理", "护理", "医疗运营"],
        "学历要求": "本科（医学）",
        "体力要求": "medium",
        "入门门槛": "高",
        "适合性格": ["服务型", "严谨型"],
        # 专业点评（来自口腔医学）
        "专业点评": "压力小、收入高、就业稳、有面子",
        "点评说明": "口腔医学是医学中的黄金方向，相比临床医学压力小、收入高、就业灵活",
        "适合人群": ["高学历", "医学背景", "追求Work-Life Balance"],
        "就业特点": "可进医院、可开诊所、可去私立，灵活度高"
    },
    "互联网医疗": {
        "trends": ["在线问诊", "健康管理", "医药电商"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["产品经理", "运营", "医学编辑", "商务"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["创新型", "社交型"]
    },
    "养老/健康": {
        "trends": ["银发经济", "健康管理", "康复护理"],
        "salary": "中偏低",
        "growth": "快速增长",
        "hot_roles": ["养老运营", "健康管理", "康复治疗", "社工"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["服务型", "耐心型"],
        # 专业点评（来自护理学 + 针灸推拿）
        "专业点评": "低分专属、女生优先；会点穴、会针灸，文科理科它都收",
        "点评说明": "养老健康行业对学历要求不高，女性从业者多；针灸推拿等技术型岗位文理不限",
        "适合人群": ["低学历", "女生", "服务型人格"],
        "就业特点": "入门容易，但需要耐心和爱心",
        "性别倾向": "女生优先",
        "加分标签": ["低分专属", "女生优先"]
    },
    "医疗美容": {
        "trends": ["轻医美", "抗衰老", "个性化美学"],
        "salary": "中",
        "growth": "快速增长",
        "hot_roles": ["咨询顾问", "医生", "运营", "销售"],
        "学历要求": "大专-本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "审美型"],
        # 专业点评（来自护理学 + 医学技术类）
        "专业点评": "低分专属、女生优先；工作轻松、不能当医生",
        "点评说明": "医美行业女性从业者多，对学历要求不高，适合不想当医生但想在医疗领域工作的人",
        "适合人群": ["低学历", "女生", "审美型"],
        "就业特点": "工作环境好，但需要销售能力",
        "性别倾向": "女生优先",
        "加分标签": ["低分专属", "女生优先"]
    },
    
    # 消费/零售
    "电商/直播": {
        "trends": ["兴趣电商", "私域运营", "跨境电商"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["直播运营", "电商运营", "供应链管理", "选品"],
        "学历要求": "大专-本科",
        "入门门槛": "低",
        "适合性格": ["社交型", "创意型"],
        # 专业点评（来自网络与新媒体）
        "专业点评": "学的杂、学的多，杂而不精",
        "点评说明": "网络与新媒体学的东西很多很杂，但每样都不精，需要自己找方向深耕",
        "适合人群": ["杂学型", "社交型", "爱折腾"],
        "就业特点": "入门容易精通难，需要持续学习和实践"
    },
    "品牌/消费品": {
        "trends": ["国货崛起", "DTC模式", "品牌升级"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["品牌经理", "市场策划", "产品经理", "渠道管理"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["创意型", "社交型"]
    },
    "零售/商超": {
        "trends": ["会员店", "即时零售", "数字化运营"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["门店管理", "采购", "运营", "电商"],
        "学历要求": "大专-本科",
        "入门门槛": "低",
        "适合性格": ["务实型", "社交型"]
    },
    "餐饮/连锁": {
        "trends": ["连锁化", "数字化", "预制菜"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["运营管理", "供应链", "品牌拓展", "数字化"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["务实型", "社交型"]
    },
    "酒水/饮料": {
        "trends": ["新消费品牌", "健康饮品", "精酿啤酒"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["品牌管理", "渠道销售", "产品研发", "市场"],
        "学历要求": "大专-本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "创意型"]
    },
    
    # 教育/培训
    "职业教育/技能培训": {
        "trends": ["产教融合", "技能认证", "终身学习"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["课程研发", "培训讲师", "学习运营", "企业培训"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["分享型", "创意型"],
        # 专业点评（来自汉语言文学）
        "专业点评": "当老师、做编辑，考公考编也可以",
        "点评说明": "汉语言文学就业多元，可以当老师、做编辑，也可以考公考编",
        "适合人群": ["文科生", "文字能力强", "追求稳定"],
        "就业特点": "出路多，但每条路都需要继续努力",
        "加分标签": ["追求稳定"]
    },
    "K12教育/素质教育": {
        "trends": ["素质教育", "AI辅助教学", "研学"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["课程设计", "教学管理", "教研", "运营"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["分享型", "耐心型"]
    },
    "留学/出国服务": {
        "trends": ["留学咨询", "语言培训", "海外服务"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["留学顾问", "语培教师", "文书", "海外服务"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "专业型"]
    },
    "私立/国际学校": {
        "trends": ["素质教育", "双语教学", "国际化"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["教师", "教学管理", "招生", "运营"],
        "学历要求": "本科（相关专业）",
        "入门门槛": "中",
        "适合性格": ["分享型", "国际型"]
    },
    
    # 专业服务
    "咨询/战略": {
        "trends": ["数字化咨询", "行业纵深", "出海咨询"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["管理咨询", "战略顾问", "行业研究", "实施顾问"],
        "学历要求": "本科-硕士",
        "入门门槛": "中高",
        "适合性格": ["分析型", "社交型"]
    },
    "法律服务": {
        "trends": ["企业合规", "知识产权", "数据合规"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["企业法务", "合规顾问", "知识产权", "涉外律师"],
        "学历要求": "本科（法学）",
        "入门门槛": "高",
        "适合性格": ["严谨型", "分析型"],
        # 专业点评（来自法学）
        "专业点评": "分数资源都需要、没有只能跑龙套",
        "点评说明": "法学需要高学历+资源人脉，五院四系毕业+通过法考+有资源才能做高端业务",
        "适合人群": ["高学历", "有资源", "能吃苦"],
        "就业特点": "金字塔结构，顶尖律师很赚钱，底层律师很艰难",
        "加分标签": ["高学历", "有资源"]
    },
    "会计/审计": {
        "trends": ["数字化财务", "业财融合", "智能审计"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["财务分析", "审计", "税务", "内控"],
        "学历要求": "本科（财会）",
        "入门门槛": "中",
        "适合性格": ["严谨型", "务实型"],
        # 专业点评（来自会计、审计、财务专业）
        "专业点评": "企业收、单位要，高中低分都能报",
        "点评说明": "会计是刚需，每个企业都需要，就业面极广，从中专到博士都有对应岗位",
        "适合人群": ["低学历", "细心型", "追求稳定"],
        "就业特点": "万金油专业，不愁找不到工作，但薪资上限不高"
    },
    "人力资源": {
        "trends": ["HR数字化", "组织发展", "灵活用工"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["HRBP", "招聘专家", "OD", "薪酬绩效"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "服务型"]
    },
    "广告/公关": {
        "trends": ["数字营销", "内容营销", "全案服务"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["策划", "客户执行", "创意", "媒介"],
        "学历要求": "本科",
        "入门门槛": "低",
        "适合性格": ["创意型", "社交型"]
    },
    "会展/活动": {
        "trends": ["线上线下融合", "IP运营", "数字化会展"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["项目策划", "客户执行", "设计", "运营"],
        "学历要求": "大专-本科",
        "入门门槛": "低",
        "适合性格": ["社交型", "创意型"]
    },
    "检测/认证": {
        "trends": ["数字化检测", "新能源检测", "国际认证"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["检测工程师", "认证顾问", "销售", "质量管理"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["严谨型", "技术型"]
    },
    
    # 媒体/文化
    "内容创作/新媒体": {
        "trends": ["短视频", "知识付费", "AIGC创作"],
        "salary": "中（波动大）",
        "growth": "快速增长",
        "hot_roles": ["内容策划", "短视频创作", "账号运营", "MCN"],
        "学历要求": "不限",
        "入门门槛": "低",
        "适合性格": ["创意型", "表现型"],
        # 专业点评（来自数字媒体技术）
        "专业点评": "做游戏、做动漫、热门行业都能干",
        "点评说明": "数字媒体技术可以做游戏、动漫、短视频等泛娱乐方向，就业选择多样",
        "适合人群": ["创意型", "表现型", "喜欢玩"],
        "就业特点": "入门门槛低，但顶尖岗位竞争激烈"
    },
    "影视/综艺": {
        "trends": ["网络电影", "短剧", "内容出海"],
        "salary": "中（波动大）",
        "growth": "稳定",
        "hot_roles": ["制片", "导演", "编剧", "营销"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["创意型", "表现型"]
    },
    "游戏/互动娱乐": {
        "trends": ["手游出海", "元宇宙", "UGC游戏"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["游戏策划", "游戏开发", "运营", "美术设计"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["创意型", "玩家型"]
    },
    "音乐/演出": {
        "trends": ["流媒体", "livehouse", "偶像经济"],
        "salary": "中（波动大）",
        "growth": "稳定",
        "hot_roles": ["艺人经纪", "演出运营", "音乐制作", "版权"],
        "学历要求": "不限",
        "入门门槛": "低",
        "适合性格": ["创意型", "表现型"]
    },
    "出版/图书": {
        "trends": ["电子书", "知识付费", "IP运营"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["编辑", "策划", "营销", "版权"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["创意型", "严谨型"]
    },
    "体育/运动": {
        "trends": ["健身大众化", "电竞", "户外运动"],
        "salary": "中",
        "growth": "快速增长",
        "hot_roles": ["教练", "运营", "赛事", "健身管理"],
        "学历要求": "不限",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["活力型", "社交型"]
    },
    
    # 旅游/出行
    "旅游/OTA": {
        "trends": ["文旅融合", "定制游", "数字化"],
        "salary": "中",
        "growth": "恢复增长",
        "hot_roles": ["旅游规划", "产品经理", "运营", "导游"],
        "学历要求": "大专-本科",
        "入门门槛": "低",
        "适合性格": ["社交型", "探索型"]
    },
    "酒店/民宿": {
        "trends": ["精品酒店", "民宿经济", "数字化运营"],
        "salary": "中偏低",
        "growth": "恢复增长",
        "hot_roles": ["酒店管理", "运营", "收益管理", "销售"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["服务型", "社交型"]
    },
    "航空/机场": {
        "trends": ["国际化", "低成本航空", "数字化"],
        "salary": "中高",
        "growth": "恢复增长",
        "hot_roles": ["飞行员", "空乘", "运营", "地勤"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "中高",
        "适合性格": ["服务型", "专业型"]
    },
    "物流/供应链": {
        "trends": ["智能物流", "跨境物流", "同城配送"],
        "salary": "中",
        "growth": "稳定增长",
        "hot_roles": ["供应链管理", "仓储运营", "物流销售", "数据分析"],
        "学历要求": "大专-本科",
        "体力要求": "medium",
        "入门门槛": "低",
        "适合性格": ["务实型", "系统型"]
    },
    
    # 公共部门
    "政府/公共事业": {
        "trends": ["数字化政务", "智慧城市", "基层治理"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["政策研究", "项目管理", "基层服务", "数据分析"],
        "学历要求": "本科-硕士",
        "入门门槛": "考试",
        "适合性格": ["稳健型", "服务型"]
    },
    "非营利/NGO": {
        "trends": ["公益创新", "社会企业", "国际化"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["项目管理", "筹资", "传播", "项目官员"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["使命型", "服务型"]
    },
    "教育/科研机构": {
        "trends": ["产学研转化", "交叉学科", "AI科研"],
        "salary": "中偏低",
        "growth": "稳定",
        "hot_roles": ["科研人员", "博士后", "科研管理", "技术转移"],
        "学历要求": "硕士-博士",
        "入门门槛": "高",
        "适合性格": ["研究型", "严谨型"]
    },
    
    # 新兴行业
    "出海/跨境": {
        "trends": ["品牌出海", "本土化运营", "供应链出海"],
        "salary": "中高",
        "growth": "高速增长",
        "hot_roles": ["海外运营", "本地化", "跨境电商", "海外市场"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "适应型"]
    },
    "碳中和/ESG": {
        "trends": ["碳交易", "ESG报告", "绿色金融"],
        "salary": "中高",
        "growth": "快速增长",
        "hot_roles": ["碳管理", "ESG咨询", "绿色金融", "环境工程"],
        "学历要求": "本科-硕士",
        "入门门槛": "中高",
        "适合性格": ["分析型", "使命型"]
    },
    "元宇宙/Web3": {
        "trends": ["虚拟现实", "数字藏品", "DAO治理"],
        "salary": "高（波动大）",
        "growth": "探索期",
        "hot_roles": ["3D设计", "区块链开发", "产品经理", "运营"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["创新型", "探索型"]
    },
    "机器人/自动化": {
        "trends": ["服务机器人", "工业机器人", "人形机器人"],
        "salary": "高",
        "growth": "高速增长",
        "hot_roles": ["机器人算法", "机械设计", "嵌入式", "应用开发"],
        "学历要求": "本科-硕士",
        "入门门槛": "高",
        "适合性格": ["技术型", "创新型"]
    },
    "量子计算/前沿科技": {
        "trends": ["量子通信", "量子计算", "前沿研究"],
        "salary": "极高",
        "growth": "探索期",
        "hot_roles": ["量子算法", "硬件研发", "研究", "产业应用"],
        "学历要求": "博士优先",
        "入门门槛": "极高",
        "适合性格": ["研究型", "创新型"]
    },
    "低空经济/无人机": {
        "trends": ["eVTOL", "无人机物流", "低空旅游"],
        "salary": "中高",
        "growth": "快速增长",
        "hot_roles": ["飞手", "硬件工程师", "空管", "应用开发"],
        "学历要求": "本科",
        "入门门槛": "中高",
        "适合性格": ["技术型", "探索型"]
    },
    "脑机接口/生命科学": {
        "trends": ["神经调控", "脑机交互", "数字疗法"],
        "salary": "高",
        "growth": "探索期",
        "hot_roles": ["神经科学", "算法工程师", "临床研究", "产品"],
        "学历要求": "硕士-博士",
        "入门门槛": "极高",
        "适合性格": ["研究型", "创新型"]
    },
    
    # 特殊行业
    "自由职业/创业": {
        "trends": ["平台经济", "个人IP", "远程协作"],
        "salary": "不稳定",
        "growth": "增长",
        "hot_roles": ["咨询顾问", "自由开发者", "内容创作者", "独立设计师"],
        "学历要求": "不限",
        "入门门槛": "低（但需经验）",
        "适合性格": ["独立型", "创意型"]
    },
    "直播电商": {
        "trends": ["矩阵打法", "私域直播", "AI主播"],
        "salary": "中（+提成）",
        "growth": "稳定增长",
        "hot_roles": ["主播", "场控", "运营", "供应链"],
        "学历要求": "不限",
        "入门门槛": "低",
        "适合性格": ["表现型", "社交型"]
    },
    "保险经纪": {
        "trends": ["互联网保险", "健康险", "财富传承"],
        "salary": "中（+提成）",
        "growth": "稳健",
        "hot_roles": ["保险顾问", "团队管理", "产品设计", "核保"],
        "学历要求": "大专-本科",
        "入门门槛": "低",
        "适合性格": ["社交型", "服务型"]
    },
    
    # ========== 劳动密集型行业 ==========
    "货运/物流运输": {
        "trends": ["干线物流", "同城配送", "跨境物流", "智能仓储"],
        "salary": "中（+提成）",
        "growth": "稳定增长",
        "hot_roles": ["货车司机", "配送司机", "物流调度", "仓储管理"],
        "学历要求": "不限",
        "体力要求": "heavy",
        "入门门槛": "低",
        "适合性格": ["独立型", "务实型"],
        "注意事项": "需B2/A2驾驶证，入行后收入可观但较辛苦"
    },
    "工厂工人/制造业": {
        "trends": ["智能制造", "自动化产线", "技能升级"],
        "salary": "中",
        "growth": "稳定",
        "hot_roles": ["操作工", "技术工人", "班组长", "设备维护"],
        "学历要求": "不限",
        "体力要求": "heavy",
        "入门门槛": "低",
        "适合性格": ["务实型", "技术型"],
        "注意事项": "老龄化导致技工短缺，越老越值钱"
    },
    "个体户/小生意": {
        "trends": ["社区商业", "地摊经济", "小店升级"],
        "salary": "不稳定",
        "growth": "增长",
        "hot_roles": ["小超市", "餐饮小店", "修理铺", "便利店"],
        "学历要求": "不限",
        "入门门槛": "低（但需资金和经验）",
        "适合性格": ["独立型", "创业型"],
        "注意事项": "创业有风险，需量力而行"
    },
    "建筑工人": {
        "trends": ["基建投资", "城市化", "老旧小区改造"],
        "salary": "中高",
        "growth": "稳定",
        "hot_roles": ["钢筋工", "木工", "水电工", "装修工"],
        "学历要求": "不限",
        "体力要求": "heavy",
        "入门门槛": "低",
        "适合性格": ["务实型", "体力型"],
        "注意事项": "室外工作，较辛苦，但收入不低"
    },
    "技工/技术工人": {
        "trends": ["技能认证", "工匠精神", "智能制造"],
        "salary": "中高",
        "growth": "高速增长",
        "hot_roles": ["焊工", "车工", "数控操作", "模具工"],
        "学历要求": "大专以下",
        "体力要求": "heavy",
        "入门门槛": "中",
        "适合性格": ["技术型", "严谨型"],
        "注意事项": "老龄化严重，技工缺口大，越老越值钱"
    },
    "出海/全球化": {
        "trends": ["品牌出海", "本土化运营", "供应链出海", "跨境电商"],
        "salary": "中高",
        "growth": "高速增长",
        "hot_roles": ["海外运营", "本地化", "跨境电商", "海外市场"],
        "学历要求": "本科",
        "入门门槛": "中",
        "适合性格": ["社交型", "适应型"]
    }
}

class AnalysisRequest(BaseModel):
    userType: int
    answers: dict  # 前端发送的是对象格式
    questions: list
    version: str = "deep"  # 新增，用于区分 deep/vip


def calculate_industry_scores(user_type: int, answers: dict, questions: list) -> dict:
    """
    基于用户答题数据，计算每个行业的匹配度评分
    
    评分维度：
    1. 行业大类相关性（30分）【重要！】- 根据职业背景与行业大类匹配，跨大类转型难度大
    2. 学历匹配度（20分）- 根据学历与行业的入门门槛匹配
    3. 年龄/经验匹配度（15分）- 根据年龄与行业要求匹配
    4. 经济压力（10分）- 根据经济压力选择适合的行业
    5. 技能匹配度（15分）- 根据职业背景与行业技能要求匹配
    6. 行业前景（10分）- 行业的长期发展前景
    
    【用户类型差异化逻辑】
    - user_type=1 (30-40岁转型群体): 重点关注技能迁移、低门槛入门、收入维持
    - user_type=2 (应届/毕业学生): 重点关注长期发展、学习机会、行业前景
    - user_type=3 (学生家长): 重点关注孩子10-15年后的发展、反脆弱专业
    
    返回：dict {行业名: (总分, 各维度得分)}
    """
    
    scores = {}
    
    # ========== 【新增】短期过渡行业（高包容性兜底选项）============
    # 这些行业可以包容所有职业背景，作为短期过渡方案
    # 但不做第一推荐，只作为保底选项
    SHORT_TERM_TRANSITION_INDUSTRIES = [
        '电商运营',      # 包容性强，适合各类背景
        '外卖/快递',     # 无门槛，过渡首选
        '出租车/网约车', # 过渡选择
        '直播/短视频',   # 新兴行业包容性强
        '销售/客服',     # 几乎无专业要求
        '餐饮服务',     # 过渡餐饮
        '美容/健身',    # 服务行业
        '个体经营/小生意', # 创业型过渡
        '保险/证券销售', # 金融行业入门
        '外贸/跨境电商', # 语言+销售
        '自由职业/自媒体', # 自由职业者
    ]
    
    # ========== 【新增】行业大类相关性映射系统 ==========
    # 定义职业背景到行业大类的映射
    PROFESSION_TO_INDUSTRY_CATEGORY = {
        'tech_rd': ['互联网/IT', '制造业', '建筑业', '工程设计'],        # 技术研发类
        'tech_prod': ['制造业', '供应链', '质量管理', '采购'],              # 生产制造类
        'tech_medical': ['医疗健康', '生物医药', '健康管理', '医疗器械'],   # 医疗健康类
        'tech_finance': ['金融', '银行证券', '保险', '财务审计'],           # 金融财务类
        'tech_edu': ['教育培训', '科研', '咨询', '成人培训'],                # 教育培训类
        'market': ['市场营销', '销售', '运营', '电商', '品牌'],             # 市场营销类
        'manage': ['企业管理', '人力资源', '行政', '法务'],                 # 职能管理类
        'media': ['媒体创意', '设计', '内容创作', '影视'],                  # 媒体创意类
        'labor': ['制造业', '建筑业', '物流运输', '仓储'],                   # 体力劳动类
        'service': ['服务业', '餐饮酒店', '美容', '快递物流'],               # 服务类
        'retail': ['零售', '电商', '销售', '客服'],                          # 销售零售类
        'self_emp': ['电商', '创业', '小生意', '自媒体'],                    # 个体经营类
        'driver': ['物流运输', '仓储', '货运', '出行服务'],                  # 司机运输类
        'agri': ['农业', '林业', '牧业', '渔业', '农产品'],                  # 农林牧渔类
        'support': ['服务业', '物业管理', '安保', '家政'],                   # 保安保洁类
        'gig': ['服务业', '自由职业', '零工经济'],                            # 自由职业类
    }
    
    # 定义行业所属的大类
    INDUSTRY_CATEGORIES = {
        # 互联网/IT类
        'AI应用开发': ['互联网/IT'],
        '互联网/IT': ['互联网/IT'],
        '软件开发': ['互联网/IT'],
        '数据分析': ['互联网/IT', '金融'],
        '人工智能/机器学习': ['互联网/IT'],
        '网络安全': ['互联网/IT'],
        '游戏开发': ['互联网/IT'],
        '新媒体运营': ['互联网/IT', '市场营销'],
        '电商运营': ['互联网/IT', '电商', '零售'],
        
        # 制造业类
        '智能制造': ['制造业'],
        '工业自动化': ['制造业'],
        '半导体/芯片': ['制造业', '互联网/IT'],
        '汽车制造': ['制造业'],
        '新能源/储能': ['制造业'],
        '电力行业': ['制造业'],
        '航空航天': ['制造业'],
        
        # 医疗健康类
        '医疗健康': ['医疗健康'],
        '养老/健康': ['医疗健康', '服务业'],  # 【新增】养老行业归属医疗健康
        '生物医药': ['医疗健康', '生物医药'],
        '医疗器械': ['医疗健康'],
        '健康管理': ['医疗健康'],
        '养老服务': ['医疗健康', '服务业'],
        
        # 金融类
        '金融': ['金融'],
        '银行/证券': ['金融'],
        '银行/保险': ['金融', '保险'],  # 【新增】银行保险综合
        '保险': ['金融', '保险'],
        '保险经纪': ['保险', '金融'],  # 【新增】保险经纪归属保险/金融
        '财务审计': ['金融', '财务审计'],
        
        # 教育培训类
        '教育培训': ['教育培训'],
        '职业教育': ['教育培训'],
        '留学咨询': ['教育培训'],
        '科研': ['科研', '教育培训'],
        
        # 市场营销/销售类
        '市场营销': ['市场营销'],
        '品牌管理': ['市场营销'],
        '销售': ['销售', '市场营销'],
        'BD/商务拓展': ['市场营销', '销售'],
        
        # 服务业类
        '餐饮酒店': ['服务业', '餐饮酒店'],
        '旅游': ['服务业'],
        '美容健身': ['服务业'],
        '快递物流': ['物流运输', '仓储'],
        '仓储': ['仓储', '物流运输'],
        
        # 物流运输类
        '物流运输': ['物流运输'],
        '货运/物流': ['物流运输'],
        '供应链': ['供应链', '物流运输'],
        '跨境电商': ['电商', '物流运输'],
        
        # 建筑业类
        '建筑业': ['建筑业'],
        '房地产': ['建筑业', '金融'],
        '装修/装潢': ['建筑业'],
        
        # 农林牧渔类
        '农业/种植业': ['农业'],
        '畜牧业/养殖业': ['牧业'],
        '农产品加工': ['农业', '制造业'],
        
        # 媒体创意类
        '媒体创意': ['媒体创意'],
        '设计': ['媒体创意', '设计'],
        '内容创作': ['媒体创意', '内容创作'],
        '影视': ['媒体创意', '影视'],
        '广告': ['市场营销', '媒体创意'],
        
        # 企业管理类
        '企业管理': ['企业管理'],
        '人力资源': ['企业管理', '人力资源'],
        '法务合规': ['法务', '企业管理'],
        
        # 其他
        '新能源/电动汽车': ['制造业', '汽车制造'],
        '环保/新能源': ['制造业', '环保'],
        '新材料': ['制造业'],
        '消费品': ['零售', '制造业'],
        '跨境贸易': ['贸易', '电商'],
    }
    
    # ========== 1. 解析用户答题数据（用于评分，使用代码值）==========
    user_data = {
        'education': None,      # 学历（代码值，用于评分）
        'age': None,            # 年龄（代码值，用于评分）
        'economic_pressure': None,  # 经济压力（代码值，用于评分）
        'skills': [],           # 技能
        'profession': None,     # 职业背景（代码值，用于评分）
        'study_willingness': None,  # 学习意愿
        'risk_tolerance': None,  # 抗压能力
        # 【新增】编程能力和专业技能/资历
        'coding_ability': None,  # 编程/代码能力
        'professional_skill': None,  # 专业技能/资历
    }
    
    # 从questions和answers中提取用户信息
    for q_idx, q in enumerate(questions):
        user_answer = answers.get(str(q_idx)) or answers.get(q_idx)
        q_text = q.get('text', '').lower()
        
        # 学历识别（用于评分）
        if '学历' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if '博士' in label:
                        user_data['education'] = '博士'
                    elif '硕士' in label:
                        user_data['education'] = '硕士'
                    elif '本科' in label:
                        user_data['education'] = '本科'
                    elif '大专' in label:
                        user_data['education'] = '大专'
                    else:
                        user_data['education'] = '大专以下'
                    break
        
        # 年龄识别（用于评分）
        elif '年龄' in q_text or '岁' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if '25' in label or '30' in label or '35' in label:
                        user_data['age'] = 'young'  # 25-35岁
                    elif '35' in label or '40' in label:
                        user_data['age'] = 'mid'    # 35-40岁
                    elif '40' in label or '45' in label:
                        user_data['age'] = 'old'    # 40岁以上
                    break
        
        # 经济压力识别（用于评分）
        elif '经济压力' in q_text or '经济' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if '大' in label or '很高' in label:
                        user_data['economic_pressure'] = 'high'
                    elif '中' in label:
                        user_data['economic_pressure'] = 'medium'
                    else:
                        user_data['economic_pressure'] = 'low'
                    break
        
        # 职业背景识别（用于评分）
        elif any(keyword in q_text for keyword in ['职业', '工作', '从事', '岗位']):
            for opt in q.get('options', []):
                # 支持value或label匹配
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    profession_label = opt.get('label', user_answer)
                    profession_code = opt.get('value', user_answer)
                    user_data['profession'] = profession_label
                    # 【修复】代码值应该保存原始value（如tech_rd），而不是中文标签
                    user_data['profession_code'] = profession_code
                    break
        
        # 学习意愿识别
        elif '学习' in q_text or '提升' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if '愿意' in label or '想' in label:
                        user_data['study_willingness'] = 'high'
                    elif '一般' in label:
                        user_data['study_willingness'] = 'medium'
                    else:
                        user_data['study_willingness'] = 'low'
                    break
        
        # 抗压能力识别
        elif '抗压' in q_text or '压力' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if '强' in label or '高' in label:
                        user_data['risk_tolerance'] = 'high'
                    elif '中' in label:
                        user_data['risk_tolerance'] = 'medium'
                    else:
                        user_data['risk_tolerance'] = 'low'
                    break
        
        # 【新增】编程/代码能力识别
        elif any(keyword in q_text for keyword in ['编程', '代码', '开发能力', 'IT技能']):
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if any(kw in label for kw in ['强', '精通', '高级', '资深']):
                        user_data['coding_ability'] = 'high'
                    elif any(kw in label for kw in ['中', '一般', '中级', '良好']):
                        user_data['coding_ability'] = 'medium'
                    else:
                        user_data['coding_ability'] = 'low'
                    break
        
        # 【新增】专业技能/资历识别
        elif any(keyword in q_text for keyword in ['专业技能', '资历', '经验', '证书', '执业']):
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    if any(kw in label for kw in ['强', '资深', '高级', '10年']):
                        user_data['professional_skill'] = 'senior'
                    elif any(kw in label for kw in ['中', '中级', '5年', '6年', '7年']):
                        user_data['professional_skill'] = 'mid'
                    elif any(kw in label for kw in ['一般', '初级', '入门', '0年', '1年', '2年', '3年']):
                        user_data['professional_skill'] = 'junior'
                    else:
                        user_data['professional_skill'] = 'none'
                    break
    
    # ========== 2. 为每个行业打分 ==========
    for industry_name, industry_info in INDUSTRY_DATABASE.items():
        score_details = {
            'category_match': 0,    # 【新增】行业大类相关性
            'education_match': 0,
            'age_match': 0,
            'economic_match': 0,
            'skill_match': 0,
            'prospect': 0,
            'total': 0
        }
        
        # ========== 【核心】行业大类相关性（30分）============
        # 这是最重要的评分维度！跨大类转型难度极大，不能纯靠分数
        # 【修复】优先使用 profession_code（代码值如tech_rd），因为 PROFESSION_TO_INDUSTRY_CATEGORY 使用代码值作为键
        profession = user_data.get('profession_code', user_data.get('profession', ''))
        category_score = 15  # 默认中等
        
        # 获取用户职业背景对应的大类列表
        user_categories = PROFESSION_TO_INDUSTRY_CATEGORY.get(profession, [])
        
        # 获取该行业所属的大类列表
        industry_categories = INDUSTRY_CATEGORIES.get(industry_name, [])
        if not industry_categories:
            # 如果行业不在映射表中，尝试从行业名中提取
            industry_categories = [industry_name]
        
        # 计算大类匹配度
        if user_categories and industry_categories:
            # 检查是否有大类重叠
            overlap = set(user_categories) & set(industry_categories)
            if overlap:
                category_score = 30  # 完全匹配，大类一致
            else:
                # 检查是否有相关大类（跨类但有关联）
                related_pairs = [
                    ('制造业', '质量管理'),
                    ('物流运输', '仓储'),
                    ('互联网/IT', '电商'),
                    ('金融', '财务审计'),
                    ('市场营销', '销售'),
                    ('服务业', '餐饮酒店'),
                    ('医疗健康', '保险'),    # 【新增】医疗健康与保险相关（健康险）
                    ('医疗健康', '服务业'),  # 【新增】医疗健康与服务行业相关
                    ('保险', '金融'),        # 【新增】保险与金融相关
                ]
                is_related = False
                for uc in user_categories:
                    for ic in industry_categories:
                        for rp in related_pairs:
                            if (uc in rp and ic in rp):
                                is_related = True
                                break
                
                if is_related:
                    category_score = 15  # 相关大类，可以转型
                else:
                    category_score = 5   # 跨大类转型困难，给予极低分
                    # 特殊处理：高学历/年轻人可以尝试跨类
                    if user_data['education'] in ['硕士', '博士']:
                        category_score = 10  # 高学历可以跨类
                    elif user_data['age'] == 'young':
                        category_score = 10  # 年轻人可以跨类
        else:
            # 职业背景不明确，按默认处理
            category_score = 15
        
        score_details['category_match'] = category_score
        
        # 学历匹配度（20分）
        edu_req = industry_info.get('学历要求', '不限')
        edu_score = 20  # 默认满分
        if user_data['education']:
            if user_data['education'] == '大专以下':
                if '本科' in edu_req or '硕士' in edu_req:
                    edu_score = 8   # 学历不足
                elif '大专' in edu_req:
                    edu_score = 15  # 基本匹配
                else:
                    edu_score = 20  # 学历符合
            elif user_data['education'] == '大专':
                if '硕士' in edu_req:
                    edu_score = 8
                elif '本科' in edu_req:
                    edu_score = 15
                else:
                    edu_score = 20
            elif user_data['education'] == '本科':
                if '硕士' in edu_req:
                    edu_score = 15
                else:
                    edu_score = 20
            elif user_data['education'] in ['硕士', '博士']:
                edu_score = 20  # 高学历可以从事任何行业
        score_details['education_match'] = edu_score
        
        # 年龄/经验匹配度（15分）
        age_score = 15
        if user_data['age'] == 'young':
            age_score = 15  # 年轻人适合任何行业
        elif user_data['age'] == 'mid':
            if '入门门槛' in industry_info:
                threshold = industry_info['入门门槛']
                if threshold == '高':
                    age_score = 10  # 40岁左右学高门槛行业有点吃力
                else:
                    age_score = 15
        elif user_data['age'] == 'old':
            if '入门门槛' in industry_info:
                threshold = industry_info['入门门槛']
                if threshold == '高':
                    age_score = 3   # 年龄大+高门槛=困难
                elif threshold == '中':
                    age_score = 10  # 中等可以尝试
                else:
                    age_score = 15  # 低门槛欢迎
        score_details['age_match'] = age_score
        
        # 经济压力匹配度（10分）
        econ_score = 10
        if user_data['economic_pressure'] == 'high':
            # 高经济压力：优先推荐立即能赚钱的行业
            salary = industry_info.get('salary', '中')
            if '+' in salary or '高' in salary:
                econ_score = 10  # 高薪+提成
            elif salary == '高':
                econ_score = 10
            elif salary == '中':
                econ_score = 8
            else:
                econ_score = 5   # 低薪不适合高压力
        elif user_data['economic_pressure'] == 'medium':
            econ_score = 8
        else:
            econ_score = 10  # 低经济压力可以追求长期发展
        score_details['economic_match'] = econ_score
        
        # 【修复】技能匹配度（15分）- 确保profession不为None
        skill_score = 10  # 默认中等
        hot_roles = industry_info.get('hotRoles', [])
        # 【修复】profession_keywords 使用代码值作为键，所以优先使用 profession_code
        profession = user_data.get('profession_code') or user_data.get('profession') or ''
        
        # 根据职业背景与热门岗位的匹配程度
        profession_keywords = {
            'tech_rd': ['算法', '开发', '工程师', '研发', '技术'],
            'tech_prod': ['生产', '工艺', '制造', '质量', '设备', '工厂'],
            'service': ['服务', '客服', '销售', '运营'],
            'manage': ['管理', 'HR', '行政', '采购'],
            'media': ['设计', '创意', '文案', '内容', '摄影'],
            'labor': ['工人', '操作', '技工', '维修', '司机'],
            'driver': ['司机', '运输', '物流', '配送'],
            'agri': ['农业', '种植', '养殖', '农林'],
        }
        
        matched = False
        for key, keywords in profession_keywords.items():
            if any(kw in profession for kw in keywords):
                if any(kw in str(hot_roles) for kw in keywords):
                    skill_score = 15  # 技能高度匹配
                    matched = True
                    break
        
        if not matched:
            # 检查学习意愿
            if user_data['study_willingness'] == 'high':
                skill_score = 10  # 愿意学习可以弥补
            elif user_data['study_willingness'] == 'medium':
                skill_score = 8
            else:
                skill_score = 5   # 不愿意学习+技能不匹配
        score_details['skill_match'] = skill_score

        # 【新增】编程/代码能力评分（20分）- 对AI、软件等行业的关键加成
        coding_score = 0
        coding_industries = ['AI', '人工智能', '大数据', '软件开发', '互联网', '云计算',
                           '网络安全', '物联网', '智能制造', '游戏', '算法', '机器人']
        if any(keyword in industry_name for keyword in ['AI', '人工智能', '算法']):
            # AI类行业：编程能力是核心要求
            if user_data.get('coding_ability') == 'high':
                coding_score = 20  # 强编程能力是AI行业的核心竞争力
            elif user_data.get('coding_ability') == 'medium':
                coding_score = 10  # 中等编程能力可以进入AI应用领域
            else:
                coding_score = 0  # 无编程能力很难进入AI核心
        elif any(keyword in industry_name for keyword in ['软件', '开发', '互联网', '游戏']):
            # 软件开发类：编程能力是基础
            if user_data.get('coding_ability') == 'high':
                coding_score = 15
            elif user_data.get('coding_ability') == 'medium':
                coding_score = 10
            else:
                coding_score = 0
        elif any(keyword in industry_name for keyword in ['数据', '分析', '云计算', '网络安全']):
            # 数据/云服务类：需要一定编程能力
            if user_data.get('coding_ability') == 'high':
                coding_score = 10
            elif user_data.get('coding_ability') == 'medium':
                coding_score = 8
            else:
                coding_score = 0
        score_details['coding_match'] = coding_score

        # 【新增】专业技能/资历评分（20分）- 加强行业大类关联性
        # 核心逻辑：使用 PROFESSION_TO_INDUSTRY_CATEGORY 和 INDUSTRY_CATEGORIES
        # 如果用户的专业技能与行业大类对口，给予高分（类似 category_match 逻辑）
        professional_score = 0
        skill_level = user_data.get('professional_skill', 'none')
        
        # 只有用户有专业技能资历时，才进行评分
        if skill_level != 'none':
            profession = user_data.get('profession_code', '')
            
            # 获取用户职业背景对应的大类列表（与 category_match 使用相同逻辑！）
            user_categories = PROFESSION_TO_INDUSTRY_CATEGORY.get(profession, [])
            
            # 获取该行业所属的大类列表
            industry_categories = INDUSTRY_CATEGORIES.get(industry_name, [])
            if not industry_categories:
                industry_categories = [industry_name]
            
            # 检查是否有大类重叠（与 category_match 完全相同！）
            overlap = set(user_categories) & set(industry_categories)
            
            if overlap:
                # 专业资历与行业大类对口！这是核心竞争力！
                if skill_level == 'senior':
                    professional_score = 20  # 资深专业资历 + 行业对口 = 核心竞争力
                elif skill_level == 'mid':
                    professional_score = 12  # 中级专业资历 + 行业对口 = 有潜力
                elif skill_level == 'junior':
                    professional_score = 5   # 初级专业资历 + 行业对口 = 需要积累
            else:
                # 专业资历与行业大类不对口
                if skill_level == 'senior':
                    professional_score = 8   # 资深但行业不对口 = 有学习能力
                elif skill_level == 'mid':
                    professional_score = 4
                else:
                    professional_score = 0
        
        score_details['professional_match'] = professional_score

        # 行业前景（10分）
        prospect_score = 10
        growth = industry_info.get('growth', '稳定')
        if growth in ['高速增长', '快速增长']:
            prospect_score = 10
        elif growth == '稳定增长':
            prospect_score = 8
        elif growth == '稳健':
            prospect_score = 7
        elif growth == '稳定':
            prospect_score = 6
        elif growth in ['恢复增长', '增长']:
            prospect_score = 5
        else:
            prospect_score = 3  # 探索期等不确定
        score_details['prospect'] = prospect_score
        
        # ========== 【专业点评标签加成】基于专业点评的权重加成 ==========
        bonus_score = 0
        bonus_reasons = []
        bonus_tags = industry_info.get('加分标签', [])
        
        # 1. 低分专属标签 → 用户学历大专以下 → +10分
        if '低分专属' in bonus_tags:
            if user_data['education'] in ['大专以下', '大专']:
                bonus_score += 10
                bonus_reasons.append('低分专属匹配+10')
        
        # 2. 普通家庭标签 → +5分（适合普通家庭是加分项）
        if '普通家庭' in bonus_tags:
            bonus_score += 5
            bonus_reasons.append('普通家庭适配+5')
        
        # 3. 追求稳定标签 → 用户也想稳定 → +5分
        if '追求稳定' in bonus_tags:
            if user_data.get('risk_tolerance') in ['low', 'medium']:
                bonus_score += 5
                bonus_reasons.append('追求稳定匹配+5')
        
        # 4. 高学历标签 → 用户是高学历 → +5分
        if '高学历' in bonus_tags:
            if user_data['education'] in ['硕士', '博士']:
                bonus_score += 5
                bonus_reasons.append('高学历匹配+5')
        
        # 5. 有资源标签 → 用户可能有资源 → +5分
        if '有资源' in bonus_tags:
            bonus_score += 3
            bonus_reasons.append('资源型行业+3')
        
        # 6. 长期主义标签 → 用户年轻 → +5分
        if '长期主义' in bonus_tags:
            if user_data['age'] in ['young', 'mid']:
                bonus_score += 5
                bonus_reasons.append('长期发展匹配+5')
        
        # 应用加成
        if bonus_score > 0:
            score_details['bonus'] = bonus_score
            score_details['bonus_reasons'] = bonus_reasons
            score_details['专业点评'] = industry_info.get('专业点评', '')
        
        # ========== 【用户类型差异化评分】根据用户类型调整评分 ==========
        user_type_bonus = 0
        user_type_reasons = []
        
        # user_type=1: 30-40岁转型群体 → 重点：技能迁移、低门槛、收入维持
        if user_type == 1:
            # 低门槛行业加分（转型者需要快速入门）
            entry_threshold = industry_info.get('入门门槛', '中')
            if entry_threshold == '低':
                user_type_bonus += 15
                user_type_reasons.append('低门槛入门+15')
            elif entry_threshold == '中':
                user_type_bonus += 8
                user_type_reasons.append('中等门槛+8')
            
            # 高薪行业加分（需要维持收入）
            salary = industry_info.get('salary', '中')
            if '高' in salary or '+' in salary:
                user_type_bonus += 10
                user_type_reasons.append('高薪维持收入+10')
            
            # 万金油专业加分（转型者多技能迁移）
            if '万金油' in industry_info.get('就业特点', ''):
                user_type_bonus += 10
                user_type_reasons.append('万金油专业+10')
        
        # user_type=2: 应届/毕业学生 → 重点：长期发展、学习机会、行业前景
        elif user_type == 2:
            # 行业前景好的加分
            growth = industry_info.get('growth', '稳定')
            if growth in ['高速增长', '快速增长']:
                user_type_bonus += 15
                user_type_reasons.append('行业高速增长+15')
            elif growth in ['稳定增长', '稳健']:
                user_type_bonus += 10
                user_type_reasons.append('行业稳定发展+10')
            
            # 高门槛+高学历匹配 = 长期发展好
            edu_req = industry_info.get('学历要求', '不限')
            if '硕士' in edu_req and user_data['education'] in ['硕士', '博士']:
                user_type_bonus += 15
                user_type_reasons.append('高学历+高要求=长期发展好+15')
            
            # 学习机会多的行业加分
            if '持续学习' in industry_info.get('就业特点', '') or '越老越值钱' in industry_info.get('就业特点', ''):
                user_type_bonus += 10
                user_type_reasons.append('长期积累有价值+10')
        
        # user_type=3: 学生家长 → 重点：10-15年后发展、反脆弱、低风险
        elif user_type == 3:
            # 行业长期稳定加分（考虑10-15年后）
            growth = industry_info.get('growth', '稳定')
            if growth in ['高速增长', '稳定增长', '稳健']:
                user_type_bonus += 15
                user_type_reasons.append('10-15年长期稳定+15')
            
            # 反脆弱专业加分（抗风险）
            risk_info = industry_info.get('风险提示', '')
            if '行业整体走下坡路' in risk_info or '谨慎选择' in risk_info:
                user_type_bonus -= 10  # 扣分
                user_type_reasons.append('风险行业-10')
            
            # 央国企/稳定就业加分
            if '央国企' in industry_info.get('就业特点', '') or '铁饭碗' in industry_info.get('就业特点', ''):
                user_type_bonus += 15
                user_type_reasons.append('央国企稳定+15')
            
            # 性别倾向考虑
            gender_tendency = industry_info.get('性别倾向', '')
            if '男生优先' in gender_tendency:
                user_type_bonus += 5
                user_type_reasons.append('男生友好+5')
            elif '女生优先' in gender_tendency:
                user_type_bonus += 5
                user_type_reasons.append('女生友好+5')
        
        # 应用用户类型加成
        if user_type_bonus != 0:
            score_details['user_type_bonus'] = user_type_bonus
            score_details['user_type_reasons'] = user_type_reasons
            score_details['user_type_name'] = {
                1: '30-40岁转型群体',
                2: '应届/毕业学生',
                3: '学生家长'
            }.get(user_type, '未知')
        
        # 计算总分（使用新的评分维度）
        # 行业大类相关性(30) + 学历(20) + 年龄(15) + 经济(10) + 技能(15) + 编程(20) + 专业(20) + 前景(10) + 加成 + 用户类型加成
        total = (score_details['category_match'] +  # 【核心】行业大类相关性
                 score_details['education_match'] + 
                 score_details['age_match'] + 
                 score_details['economic_match'] + 
                 score_details['skill_match'] + 
                 score_details.get('coding_match', 0) +  # 【新增】编程能力
                 score_details.get('professional_match', 0) +  # 【新增】专业技能/资历
                 score_details['prospect'] +
                 bonus_score +
                 user_type_bonus)
        score_details['total'] = total
        
        # 标记是否为短期过渡行业
        is_transition = industry_name in SHORT_TERM_TRANSITION_INDUSTRIES
        score_details['is_transition'] = is_transition
        
        scores[industry_name] = (total, score_details)
    
    # ========== 3. 按分数排序 ==========
    # 【核心逻辑】同类行业优先于跨大类行业
    # 规则：非过渡行业 > 过渡行业；同类 > 相关 > 跨类
    def sort_key(item):
        industry_name, (score, details) = item
        is_transition = details.get('is_transition', False)
        category_match = details.get('category_match', 0)
        
        # 排序优先级：
        # 1. 非过渡行业优先于过渡行业（1 > 0）
        # 2. 在同等优先级下，category_match高的优先（同类 > 相关 > 跨类）
        # 3. 最后按总分
        if is_transition:
            # 过渡行业排后面（优先级0），但内部仍按category_match和score排序
            return (0, category_match, score)
        else:
            # 正常行业优先（优先级1），同类行业排前面
            return (1, category_match, score)
    
    sorted_scores = sorted(scores.items(), key=sort_key, reverse=True)
    
    # 返回排序后的结果（只返回前20个）
    return dict(sorted_scores[:20])


def build_analysis_prompt(user_type: int, answers: list, questions: list) -> str:
    """构建AI分析提示词"""
    from datetime import datetime
    current_year = datetime.now().year
    next_year = current_year + 1
    background_map = {
        # 高学历群体
        'tech_rd': '技术研发类（IT/互联网/制造/建筑等）',
        'tech_prod': '生产制造类（工厂/工艺/质量/供应链）',
        'tech_medical': '医疗健康类（医生/护士/健康管理）',
        'tech_finance': '金融财务类（银行/证券/会计/审计）',
        'tech_edu': '教育培训类（教师/培训/咨询/研究）',
        'market': '市场营销类（销售/运营/市场/BD）',
        'manage': '职能管理类（HR/行政/采购/法务）',
        'media': '媒体创意类（设计/文案/内容/摄影）',
        # 大专以下群体 - 实际工作经历
        'labor': '体力/劳动类（工厂/建筑/搬运/安装/技工）',
        'service': '服务类（餐饮/酒店/美容/快递/外卖/家政）',
        'retail': '销售/零售类（店员/导购/摊贩/客服）',
        'self_emp': '个体经营（小生意/电商/地摊/微商）',
        'driver': '司机/运输类（货车/出租/货运/滴滴）',
        'agri': '农林牧渔类（务农/养殖/林果/渔业）',
        'support': '保安/保洁/物业/仓库类',
        'gig': '自由职业/打零工（没固定工作）'
    }
    user_type_names = {1: "30-40岁的职场转型者", 2: "应届/毕业1-3年的年轻人", 3: "学生家长"}

    parsed = {}
    for q in questions:
        for opt in q.get("options", []):
            val = opt.get("value", "")
            if val in answers:
                parsed[q.get("text", "")] = opt.get("label", val)

    context = "用户是" + user_type_names.get(user_type, "未知群体") + "。"

    # 构建答案详情 - 修复：answers是dict {索引: 答案值}
    answer_details = []
    for q_idx, q in enumerate(questions):
        # 获取用户对这个问题的回答
        user_answer = answers.get(str(q_idx)) or answers.get(q_idx)
        if user_answer:
            # 找到对应的选项label
            opt = next((o for o in q.get("options", []) if o.get("value") == user_answer or o.get("label") == user_answer), None)
            answer_text = opt.get("label", user_answer) if opt else user_answer
            answer_details.append(f"Q{q_idx + 1}: {q.get('text', '')} -> {answer_text}")

    # ========== 家长版：新架构 ==========
    if user_type == 3:
        # 构建精简提示词
        answer_lines = []
        for q_idx, q in enumerate(questions):
            user_answer = answers.get(str(q_idx)) or answers.get(q_idx)
            if user_answer:
                opt = next((o for o in q.get("options", [])
                           if o.get("value") == user_answer or o.get("label") == user_answer), None)
                answer_text = opt.get("label", user_answer) if opt else user_answer
                answer_lines.append(f"Q{q_idx + 1}: {q.get('text', '')} -> {answer_text}")

        user_prompt = f"""用户类型：学生家长（分析对象：孩子）

答题数据：
{chr(10).join(answer_lines)}

请基于以上答题数据，以孩子为分析对象，给出职业方向推荐。"""

    # ========== 30-40岁转型版：也走完整模板 ==========
    # 不再提前返回，让所有用户类型都使用完整模板

    # ========== 应届生版：也走完整模板 ==========
    # 不再提前返回，让所有用户类型都使用完整模板

    # ========== 家长版：追加家长专属指令到 lines_d，不提前返回 ==========
    if user_type == 3:
        # 家长专属指令追加到 lines_d（下面会构建）
        pass
    else:
        # 非家长类型跳过家长处理
        pass

    # 所有用户类型统一使用简洁提示词
    all_industries = list(INDUSTRY_DATABASE.keys())
    industry_sample = ", ".join(all_industries)

    prompt = f"""你是一位资深的职业规划顾问。请基于以下答题数据，输出完整的职业规划报告。

用户类型：{user_type_names.get(user_type, '未知')}
当前年份：{current_year}年
答题数据：
{chr(10).join(answer_details)}

你必须输出一个严格的 JSON 对象，包含以下所有顶级字段（缺一不可）：
summary, macroTrends, persona, recommendedIndustries, risks

各字段约束：
1. summary: 对象，包含 overallScore、recommendedIndustries（仅1个行业）、analysis、result、short
2. macroTrends: 数组，仅1个趋势，包含 trend、outlook（长期看好/中期看好/短期过渡）、period、analysis（需真实数据）
3. persona: 数组，4个对象，每个包含 label 和 value，均为真实内容
4. recommendedIndustries: 数组，仅1个行业，包含 name、outlook、period、matchScore、reason、matchReason、hotRoles、entryTips、salaryRange
5. risks: 数组，2-3个具体风险描述

绝对禁止：
- 使用 XX、xxx、待定、未知、暂无、TBD 等占位符
- 空字符串、空数组、空对象
- 行业名称必须从以下数据库中选择：{industry_sample}

请直接输出 JSON 对象。"""

    # ---- 动态约束：学历、艺术背景（轻量版） ----
    user_edu_raw = None
    user_major_raw = None
    for q_idx, q in enumerate(questions):
        q_text = q.get("text", "")
        ans = answers.get(str(q_idx)) or answers.get(q_idx)
        if "学历" in q_text:
            user_edu_raw = ans
        if "专业" in q_text or "属于" in q_text:
            user_major_raw = ans

    edu = normalize_education(user_edu_raw) if user_edu_raw else ""
    if edu in ["大专以下", "大专"]:
        prompt += "\n**严格约束**：用户学历较低，请勿推荐要求本科及以上学历的行业（如人工智能、软件开发等），优先推荐学历要求为大专以下或不限的行业。"

    if user_major_raw and (user_major_raw in ["arts", "art", "creative"] or "艺术" in str(user_major_raw)):
        prompt += "\n**艺术/创意背景**：请围绕设计、数字艺术、影视、新媒体、游戏、广告创意等领域推荐，勿推荐纯理工技术岗位。"

    return prompt


def build_deep_analysis_prompt(user_type: int, answers: list, questions: list) -> str:
    """构建深度评估版AI分析提示词"""
    from datetime import datetime
    current_year = datetime.now().year

    user_type_names = {
        1: "30-40岁的职场转型者（深度版）",
        2: "应届/毕业1-3年的年轻人（深度版）", 
        3: "学生家长（深度版，分析对象是孩子）"
    }

    # 解析答题数据
    answer_lines = []
    for q_idx, q in enumerate(questions):
        user_answer = answers.get(str(q_idx)) or answers.get(q_idx)
        if user_answer:
            opt = next((o for o in q.get("options", [])
                       if o.get("value") == user_answer or o.get("label") == user_answer), None)
            answer_text = opt.get("label", user_answer) if opt else user_answer
            answer_lines.append(f"Q{q_idx+1}: {q.get('text', '')} -> {answer_text}")

    prompt = f"""你是一位资深的职业规划顾问，请基于以下答题数据，输出一份完整的职业规划报告。

用户类型：{user_type_names.get(user_type, '未知')}
当前年份：{current_year}年
答题数据：
{chr(10).join(answer_lines)}

你必须输出一个严格的 JSON 对象，必须包含以下所有顶级字段（缺一不可）：
aiAnalysis, summary, macroTrends, persona, skillGap, recommendedIndustries, pathways, actionPlan, risks

各模块约束：
1. aiAnalysis: 对象，包含 process（100-150字分析过程）、conclusion（100-150字结论）、confidence（置信度）
2. summary: 对象，包含 overallScore、recommendedIndustries（数组）、analysis、result、short
3. macroTrends: 数组，长度=3，每个元素包含 trend、outlook（长期看好/中期看好/短期过渡）、period、analysis（100-150字，需真实数据）
4. persona: 对象，包含 type、analysis、strengths（数组，2-4个）、limitations（数组，1-3个）
5. skillGap: 数组，长度=3，每个元素包含 industry、analysis、current（数组）、missing（数组）、howToAcquire
6. recommendedIndustries: 数组，长度=3，每个元素包含 name、reason、outlook、period、matchScore、analysis（100-150字）、hotRoles、entryTips、salaryRange
7. pathways: 数组，长度=3，每个元素包含 name、industry、analysis、steps（数组，含 step/timeline/cost）
8. actionPlan: 数组，长度=3，每个元素包含 industry、actions（数组，含 phase/analysis/description）
9. risks: 数组，长度>=3，每个元素包含 type、analysis、description、mitigation

绝对禁止：
- 使用 XX、xxx、待定、未知、暂无、TBD 等占位符
- 空字符串、空数组、空对象
- 行业名称必须真实存在，禁止编造
- 所有数字、薪资、时间必须具体真实
- persona 数组中每个 value 必须是中文自然语言，严禁输出内部代码
- risks 数组中每个元素必须是字符串，不能是对象

请直接输出 JSON 对象，不要用代码块包裹。

行业名称必须真实存在，如：人工智能/大数据, 半导体/芯片, 新能源/储能, 出海/跨境, 医疗健康, 金融科技, 机器人/自动化, 软件开发/互联网, 低空经济/无人机, 碳中和/ESG, 智能制造, 职业教育, 内容创作/新媒体, 养老/健康, 物流/供应链等。禁止编造行业名称。"""

    # ========== 家长特殊处理 ==========
    if user_type == 3:
        prompt += """

【重要】分析对象是孩子，不是家长。必须根据孩子的学习阶段和类型推荐行业，禁止引用家长的职业背景。
理科/工科→推荐AI、机器人、半导体、新能源等；文科/商科→出海、内容创作、金融科技等；艺术/创意→AI设计、数字艺术、新媒体等；职业技术→智能制造、新能源技术、无人机等。"""

    # ---- 动态约束：学历、艺术背景（深度版） ----
    user_edu_raw = None
    user_major_raw = None
    for q_idx, q in enumerate(questions):
        q_text = q.get("text", "")
        ans = answers.get(str(q_idx)) or answers.get(q_idx)
        if "学历" in q_text:
            user_edu_raw = ans
        if "专业" in q_text or "属于" in q_text:
            user_major_raw = ans

    edu = normalize_education(user_edu_raw) if user_edu_raw else ""
    if edu in ["大专以下", "大专"]:
        prompt += "\n**严格约束**：用户学历较低，请勿推荐要求本科及以上学历的行业（如人工智能、软件开发等），优先推荐学历要求为大专以下或不限的行业。"

    if user_major_raw and (user_major_raw in ["arts", "art", "creative"] or "艺术" in str(user_major_raw)):
        prompt += "\n**艺术/创意背景**：请围绕设计、数字艺术、影视、新媒体、游戏、广告创意等领域推荐，勿推荐纯理工技术岗位。"

    return prompt


import requests

# 全局变量：存储最后一次请求的数据（用于本地模式）
_last_request_data = {
    'user_type': None,
    'answers': None,
    'questions': None,
    'report_type': 'light'  # 'light', 'deep', 'vip'
}

def set_request_data(user_type, answers, questions, report_type='light'):
    """设置请求数据（供本地模式使用）"""
    global _last_request_data
    _last_request_data['user_type'] = user_type
    _last_request_data['answers'] = answers
    _last_request_data['questions'] = questions
    _last_request_data['report_type'] = report_type


def generate_local_report_sync(user_type: int, answers: dict, questions: list, report_type: str = 'light') -> str:
    """
    纯本地生成评估报告（不依赖AI）
    基于评分算法+模板生成报告内容
    """
    import json
    from datetime import datetime
    current_year = datetime.now().year
    
    # 1. 调用评分函数获取行业评分
    scored_industries = calculate_industry_scores(user_type, answers, questions)
    
    # 2. 根据报告类型获取top行业数量
    # 轻量版(light)只推荐1个行业，深度版(deep)推荐3个行业
    top_count = 1 if report_type == 'light' else 3
    top_industries = list(scored_industries.items())[:top_count]
    
    # 3. 解析用户数据（保留原始文本，用于显示）
    user_data = {
        'education': None,      # 学历（显示文本）
        'education_code': None,  # 学历（代码，用于评分）
        'age': None,             # 年龄（显示文本）
        'age_code': None,        # 年龄（代码，用于评分）
        'economic_pressure': None,      # 经济压力（显示文本）
        'economic_pressure_code': None, # 经济压力（代码，用于评分）
        'profession': None,      # 职业背景（显示文本）
        'profession_code': None, # 职业背景（代码，用于评分）
        'study_willingness': None,
        'risk_tolerance': None,
    }
    
    # 保存用户选择的具体文本（用于显示）
    user_selection = {}
    
    for q_idx, q in enumerate(questions):
        user_answer = answers.get(str(q_idx)) or answers.get(q_idx)
        if not user_answer:
            continue
        q_text = q.get('text', '')
        
        if '学历' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    user_data['education'] = label  # 保存显示文本
                    user_selection['education'] = label
                    if '博士' in label: 
                        user_data['education_code'] = '博士'
                    elif '硕士' in label: 
                        user_data['education_code'] = '硕士'
                    elif '本科' in label: 
                        user_data['education_code'] = '本科'
                    elif '大专' in label: 
                        user_data['education_code'] = '大专'
                    else:
                        user_data['education_code'] = '大专以下'
                    break
        elif '年龄' in q_text or '岁' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    user_data['age'] = label  # 保存显示文本
                    user_selection['age'] = label
                    if '25' in label or '30' in label or '35' in label:
                        user_data['age_code'] = 'young'
                    elif '40' in label or '45' in label:
                        user_data['age_code'] = 'mid'
                    elif '50' in label:
                        user_data['age_code'] = 'old'
                    break
        elif '经济压力' in q_text or '经济' in q_text:
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    user_data['economic_pressure'] = label  # 保存显示文本
                    user_selection['economic_pressure'] = label
                    if '大' in label or '很高' in label:
                        user_data['economic_pressure_code'] = 'high'
                    elif '中' in label:
                        user_data['economic_pressure_code'] = 'medium'
                    else:
                        user_data['economic_pressure_code'] = 'low'
                    break
        elif any(keyword in q_text for keyword in ['职业', '工作', '从事', '岗位']):
            for opt in q.get('options', []):
                if opt.get('value') == user_answer or opt.get('label') == user_answer:
                    label = opt.get('label', '')
                    code = opt.get('value', user_answer)
                    user_data['profession'] = label  # 保存显示文本
                    user_selection['profession'] = label
                    # 【修复】代码值应该保存原始value（如tech_rd），而不是中文标签
                    user_data['profession_code'] = code
                    break
    
    # 4. 生成报告
    if report_type == 'light':
        return generate_light_report_sync(user_data, top_industries, current_year, user_selection)
    else:
        return generate_deep_report_sync(user_data, top_industries, current_year, user_selection)


def generate_light_report_sync(user_data, top_industries, current_year, user_selection=None):
    """生成轻量版报告（纯本地）"""
    import json
    
    # 确保user_selection存在
    if user_selection is None:
        user_selection = {}
    
    # 短期过渡行业列表
    SHORT_TERM_TRANSITION_INDUSTRIES = [
        '电商运营', '外卖/快递', '出租车/网约车', '直播/短视频',
        '销售/客服', '餐饮服务', '美容/健身', '个体经营/小生意',
        '保险/证券销售', '外贸/跨境电商', '自由职业/自媒体',
    ]
    
    # 推荐行业
    recommended = []
    for industry_name, (score, details) in top_industries:
        industry_info = INDUSTRY_DATABASE.get(industry_name, {})
        
        # 检查是否为短期过渡行业
        is_transition = industry_name in SHORT_TERM_TRANSITION_INDUSTRIES
        
        if is_transition:
            outlook = '短期过渡'
        else:
            outlook = '长期看好' if industry_info.get('growth') in ['高速增长', '快速增长'] else \
                      '中期看好' if industry_info.get('growth') in ['稳定增长', '稳健'] else '短期过渡'
        
        # 过渡行业的说明
        if is_transition:
            reason = f"【短期过渡】该行业包容性强，适合作为转型期的过渡选择"
            match_reason = f"您的{user_data.get('education', '未知')}学历背景，可以在{industry_name}行业快速上手，作为过渡方案"
        else:
            reason = f"多维度评分{score}分，{user_data.get('education', '未知')}学历适配"
            match_reason = f"您的{user_data.get('education', '未知')}学历、{user_data.get('profession', '未知')}背景，与该行业匹配度{score}分"
        
        recommended.append({
            "name": industry_name,
            "outlook": outlook,
            "matchScore": f"{score}分",
            "reason": reason,
            "matchReason": match_reason,
            "isTransition": is_transition,  # 标记是否为过渡行业
            "hotRoles": [f"{role} {industry_info.get('salary', '中')}薪" for role in industry_info.get('hot_roles', [])[:3]],
            "entryTips": f"建议从{industry_info.get('hot_roles', ['相关岗位'])[0]}岗位入手，学习相关技能",
            "salaryRange": f"入职{industry_info.get('salary', '中')}薪 → 3年后提升30-50%",
            "risks": [f"{industry_name}行业需要持续学习，存在技术更新风险"],
            "professionalReview": industry_info.get('专业点评', '该行业暂无专业点评')
        })
    
    # 宏观趋势
    macro_trends = []
    for industry_name, (score, details) in top_industries:
        industry_info = INDUSTRY_DATABASE.get(industry_name, {})
        outlook = '长期看好' if industry_info.get('growth') in ['高速增长', '快速增长'] else \
                  '中期看好' if industry_info.get('growth') in ['稳定增长', '稳健'] else '短期过渡'
        period = '10年以上' if outlook == '长期看好' else '6-8年' if outlook == '中期看好' else '3-5年'
        
        analysis = f"{current_year}年{industry_name}行业"
        trends = industry_info.get('trends', [])
        if trends:
            analysis += f"主要趋势：{'、'.join(trends[:3])}。"
        analysis += f"薪资水平：{industry_info.get('salary', '中')}。增长趋势：{industry_info.get('growth', '稳定')}。"
        analysis += f"热门岗位：{', '.join(industry_info.get('hot_roles', [])[:3])}。"
        
        macro_trends.append({
            "trend": f"{industry_name}行业趋势",
            "outlook": outlook,
            "period": period,
            "analysis": analysis
        })
    
    # 用户画像（使用显示文本，确保不为None）
    # 确保所有值都是字符串，不为 None
    def safe_str(value, default='未填写'):
        if value is None:
            return default
        return str(value)
    
    persona = [
        {"label": "职业背景", "value": safe_str(user_selection.get('profession') or user_data.get('profession'))},
        {"label": "学历层次", "value": safe_str(user_selection.get('education') or user_data.get('education'))},
        {"label": "年龄阶段", "value": safe_str(user_selection.get('age') or user_data.get('age'))},
        {"label": "经济压力", "value": safe_str(user_selection.get('economic_pressure') or user_data.get('economic_pressure'))}
    ]
    
    # 用户画像解读（AI生成格式）
    persona_analysis = f"基于您的个人画像分析：您是一名{user_data.get('profession', '未知')}从业者，拥有{user_data.get('education', '未知')}学历，年龄处于{user_data.get('age', '未知')}阶段，当前经济压力{user_data.get('economic_pressure', '未知')}。"
    persona_analysis += f"结合您的背景，系统为您精选了3个最匹配的行业方向。"
    
    # 将persona_analysis添加到persona中
    persona.append({"label": "画像解读", "value": persona_analysis})
    
    # 风险提示
    risks = []
    for industry_name, (score, details) in top_industries[:2]:
        industry_info = INDUSTRY_DATABASE.get(industry_name, {})
        if industry_info.get('growth') in ['探索期', '下降']:
            risks.append(f"{industry_name}行业存在不确定性，建议谨慎考虑")
        else:
            risks.append(f"{industry_name}需要持续学习，技术更新快")
    
    # 综合评分
    total_score = sum([score for _, (score, _) in top_industries]) // len(top_industries)
    
    report = {
        "summary": {
            "analysis": f"基于您的答题数据，系统进行了多维度分析。职业背景：{user_data.get('profession', '未知')}，学历：{user_data.get('education', '未知')}，经济压力：{user_data.get('economic_pressure', '未知')}。系统从{len(INDUSTRY_DATABASE)}个行业中精选了3个最匹配的方向。",
            "result": f"推荐转型到{recommended[0]['name']}（匹配度{recommended[0]['matchScore']}），其次是{recommended[1]['name']}和{recommended[2]['name']}。",
            "short": f"最适合：{recommended[0]['name']}"
        },
        "macroTrends": macro_trends,
        "persona": persona,
        "recommendedIndustries": recommended,
        "risks": risks[:3]
    }
    
    return json.dumps(report, ensure_ascii=False)


def generate_deep_report_sync(user_data, top_industries, current_year, user_selection=None):
    """生成深度版报告（纯本地）"""
    import json
    
    total_score = sum([score for _, (score, _) in top_industries]) // len(top_industries)
    
    # 推荐行业
    recommended = []
    for industry_name, (score, details) in top_industries:
        industry_info = INDUSTRY_DATABASE.get(industry_name, {})
        outlook = '长期看好' if industry_info.get('growth') in ['高速增长', '快速增长'] else \
                  '中期看好' if industry_info.get('growth') in ['稳定增长', '稳健'] else '短期过渡'
        period = '10年以上' if outlook == '长期看好' else '6-8年' if outlook == '中期看好' else '3-5年'
        
        # 生成匹配理由
        match_reason = f"基于您的{user_data.get('education', '未知')}学历、{user_data.get('age', 'unknown')}年龄阶段、"
        match_reason += f"经济压力{user_data.get('economic_pressure', '未知')}，该行业综合评分{score}分。"
        match_reason += f"学历匹配{details['education_match']}分，年龄匹配{details['age_match']}分，"
        match_reason += f"经济匹配{details['economic_match']}分，技能匹配{details['skill_match']}分。"
        
        recommended.append({
            "name": industry_name,
            "reason": f"多维度评分{score}分，{user_data.get('education')}学历适配",
            "outlook": outlook,
            "period": period,
            "matchScore": f"{score}分",
            "analysis": f"{industry_name}行业{industry_info.get('growth', '稳定')}发展，薪资{industry_info.get('salary', '中')}。{match_reason}",
            "hotRoles": [f"{role} {industry_info.get('salary', '中')}薪" for role in industry_info.get('hot_roles', [])[:3]],
            "entryTips": f"建议从{industry_info.get('hot_roles', ['相关岗位'])[0]}入手，学习{industry_info.get('trends', ['相关技能'])[0]}",
            "salaryRange": f"入职{industry_info.get('salary', '中')}薪 → 3年后{industry_info.get('salary', '中')}薪+30%",
            "risks": [f"技术更新快，需要持续学习", f"行业竞争加剧"],
            "matchReason": match_reason,
            "professionalReview": industry_info.get('专业点评', '该行业暂无专业点评')
        })
    
    # 宏观趋势
    macro_trends = []
    for industry_name, (score, details) in top_industries:
        industry_info = INDUSTRY_DATABASE.get(industry_name, {})
        outlook = '长期看好' if industry_info.get('growth') in ['高速增长', '快速增长'] else \
                  '中期看好' if industry_info.get('growth') in ['稳定增长', '稳健'] else '短期过渡'
        period = '10年以上' if outlook == '长期看好' else '6-8年' if outlook == '中期看好' else '3-5年'
        
        analysis = f"【{current_year}年行业数据】{industry_name}行业规模持续增长，"
        trends = industry_info.get('trends', [])
        if trends:
            analysis += f"主要趋势包括{'、'.join(trends[:3])}。"
        analysis += f"该行业薪资水平为{industry_info.get('salary', '中')}，增长趋势为{industry_info.get('growth', '稳定')}。"
        analysis += f"热门岗位有{len(industry_info.get('hot_roles', []))}个，包括{', '.join(industry_info.get('hot_roles', [])[:3])}。"
        analysis += f"根据用户答题数据，您的背景与该行业匹配度为{score}分。"
        
        macro_trends.append({
            "trend": f"{industry_name}行业趋势",
            "outlook": outlook,
            "period": period,
            "analysis": analysis,
            "icon": "📈" if outlook == "长期看好" else "🚀" if outlook == "中期看好" else "💡"
        })
    
    # 用户画像
    persona = {
        "type": "转型者" if user_data.get('age') == 'mid' else "潜力股" if user_data.get('age') == 'young' else "稳重派",
        "analysis": f"用户为{user_data.get('education', '未知')}学历，职业背景{user_data.get('profession', '未知')}，"
                    f"年龄{user_data.get('age', 'unknown')}阶段，经济压力{user_data.get('economic_pressure', 'unknown')}。",
        "strengths": generate_strengths_local(user_data),
        "limitations": ["需要学习新技能", "转型期收入可能下降", "需要适应新行业文化"],
        "advice": f"建议优先选择{recommended[0]['name']}方向，匹配度最高（{recommended[0]['matchScore']}）"
    }
    
    # 技能差距
    skill_gap = []
    for industry_name, (score, details) in top_industries:
        industry_info = INDUSTRY_DATABASE.get(industry_name, {})
        skill_gap.append({
            "industry": industry_name,
            "analysis": f"当前拥有{user_data.get('profession', '基础')}技能，需要补充{industry_info.get('trends', ['相关'])[0]}技能。",
            "current": [user_data.get('profession', '基础技能')],
            "missing": industry_info.get('trends', ['新技能'])[:3],
            "howToAcquire": f"通过在线课程学习{industry_info.get('trends', ['相关技能'])[0]}，建议3-6个月完成",
            "timeCost": "3-6个月，每周10-15小时，学费3000-8000元"
        })
    
    # 路径规划
    pathways = [
        {
            "analysis": f"路径1：深耕{recommended[0]['name']}方向，从现有背景转型。",
            "steps": [
                {"name": "学习基础", "desc": f"学习{recommended[0]['name']}基础知识"},
                {"name": "做项目", "desc": "在实际项目中应用所学"}
            ],
            "expectedIncome": f"转正后 {industry_info.get('salary', '中')}薪水平",
            "successRate": "70%",
            "cost": "3000-8000元",
            "timeline": "3-6个月"
        }
    ]
    
    # 行动计划
    action_plan = []
    for industry_name, (score, details) in top_industries:
        action_plan.append({
            "industry": industry_name,
            "actions": [
                {"title": "学习基础", "content": f"完成{INDUSTRY_DATABASE.get(industry_name, {}).get('trends', ['基础'])[0]}课程", "timeframe": "1-3个月"},
                {"title": "做项目", "content": f"在{industry_name}领域完成2-3个项目", "timeframe": "3-6个月"}
            ]
        })
    
    # 风险提示
    risks = [
        f"{recommended[0]['name']}需要持续学习，技术更新快",
        f"{recommended[1]['name']}行业竞争可能加剧",
        "转型期收入可能下降20-30%，需做好财务准备"
    ]
    
    # 组装报告
    report = {
        "aiAnalysis": {
            "title": "智能分析报告（纯本地生成）",
            "intro": f"基于您的答题数据，系统进行了深度分析。您的职业背景是{user_data.get('profession', '未知')}，学历为{user_data.get('education', '未知')}。",
            "process": f"【分析过程】1）职业背景解析：您的{user_data.get('profession', '未知')}背景积累了相关技能。2）能力评估：{user_data.get('education', '未知')}学历表明具备良好学习基础。3）资源盘点：经济压力{user_data.get('economic_pressure', '未知')}，可以承受学习投入。4）风险偏好：抗压能力适中，适合稳定型工作。5）趋势匹配：综合评分{total_score}分。",
            "conclusion": f"【结论】综合推荐3个行业：1）{recommended[0]['name']}（{recommended[0]['matchScore']}）；2）{recommended[1]['name']}（{recommended[1]['matchScore']}）；3）{recommended[2]['name']}（{recommended[2]['matchScore']}）。",
            "confidence": f"本报告置信度：{85 if total_score > 70 else 75}%"
        },
        "summary": {
            "overallScore": f"综合匹配度评分：{total_score}分",
            "recommendedIndustries": [name for name, _ in top_industries],
            "analysis": f"【综合分析】基于{len(top_industries)}道题答题数据，从职业背景、学历、技能、经济压力等多维度分析，推荐以上3个行业。",
            "result": f"【深度结论】经过全面分析，推荐3个行业：{top_industries[0][0]}、{top_industries[1][0]}、{top_industries[2][0]}，匹配度分别为{top_industries[0][1][0]}分、{top_industries[1][1][0]}分、{top_industries[2][1][0]}分。",
            "short": f"技术转型最佳：{top_industries[0][0]}"
        },
        "macroTrends": macro_trends,
        "persona": persona,
        "skillGap": skill_gap,
        "recommendedIndustries": recommended,
        "pathways": pathways,
        "actionPlan": action_plan,
        "risks": risks
    }
    
    return json.dumps(report, ensure_ascii=False)


def generate_strengths_local(user_data):
    """生成本地版优势列表"""
    strengths = []
    if user_data.get('education') in ['本科', '硕士', '博士']:
        strengths.append(f"{user_data.get('education')}学历，学习能力强")
    if user_data.get('profession'):
        strengths.append(f"{user_data.get('profession')}背景，积累了相关经验")
    if user_data.get('age') == 'young':
        strengths.append("年龄优势，学习能力强，转型时间充裕")
    elif user_data.get('age') == 'mid':
        strengths.append("经验丰富，抗压能力强")
    strengths.append("有明确职业发展意愿")
    return strengths[:4]


def generate_fallback_response(prompt: str) -> str:
    """生成fallback响应（当AI API不可用时）"""
    # 根据prompt判断是哪种类型的请求
    if '深度评估' in prompt or 'VIP' in prompt:
        # 深度评估版fallback
        import json
        fallback = {
            "aiAnalysis": {
                "intro": "基于您的答题数据，系统进行了深度分析（AI API未配置，此为模拟数据）",
                "process": "【分析过程】\n1）职业背景解析：用户拥有相关行业经验，积累了专业技能和项目管理能力。\n2）能力评估：本科学历表明具备良好的学习基础，学习意愿强，预计可以在6-12个月内掌握新技能。\n3）资源盘点：经济压力中等，家庭支持度良好，可以承受5000-10000元的学习投入。\n4）风险偏好：抗压能力中等，偏好稳定型工作，适合技术管理型岗位。\n5）趋势匹配：结合2026年行业趋势，推荐以下3个行业。",
                "conclusion": "【AI结论】综合推荐3个行业：1）AI应用开发（匹配度85分）；2）数据分析（匹配度80分）；3）企业服务（匹配度78分）。这些行业符合用户的职业背景和技能积累。",
                "confidence": "本报告置信度：75%（AI API未配置，使用模拟数据）"
            },
            "summary": {
                "overallScore": "综合匹配度评分：81分",
                "recommendedIndustries": ["AI应用开发", "数据分析", "企业服务"],
                "analysis": "【综合分析】基于用户答题数据，从职业背景（技术相关）、学历（本科）、技能（编程基础）、经济压力（中等）、抗压能力（良好）等多维度分析，推荐以上3个行业。",
                "result": "【深度结论】经过全面分析，推荐3个行业：AI应用开发、数据分析、企业服务，匹配度分别为85分、80分、78分。建议优先选择AI应用开发方向。",
                "short": "技术转型最佳：AI应用开发"
            },
            "macroTrends": [
                {"trend": "AI应用开发行业趋势", "outlook": "长期看好", "period": "10年以上", "analysis": "2026年AI应用开发市场规模达5000亿元，同比增长35%。全国相关从业人员约200万人，年均薪资18-35万元。"},
                {"trend": "数据分析行业趋势", "outlook": "长期看好", "period": "10年以上", "analysis": "2026年数据分析行业规模达3000亿元，同比增长28%。从业人员约150万人，年均薪资15-30万元。"},
                {"trend": "企业服务行业趋势", "outlook": "中期看好", "period": "6-8年", "analysis": "2026年企业服务岗位需求同比增长20%，平均薪资20-40万元，竞争相对激烈。"}
            ],
            "persona": {
                "analysis": "【个人画像】用户为本科及以上学历，拥有技术背景，年龄30-40岁，有3-5年工作经验。经济压力中等，家庭支持度良好，学习意愿强。",
                "strengths": ["技术基础扎实", "项目管理经验", "学习能力强", "抗压能力良好"],
                "limitations": ["年龄转型压力", "需要补充AI相关技能", "行业转换需要时间成本"]
            },
            "skillGap": [
                {"analysis": "【技能Gap分析】当前拥有编程基础，但缺少AI相关技能。需要补充机器学习、深度学习等技能。", "current": ["编程基础", "项目管理"], "missing": ["机器学习", "深度学习框架"], "howToAcquire": "建议通过Coursera学习吴恩达的机器学习课程，B站观看实践教程。", "timeCost": "6-12个月，每周15小时，学费5000-10000元"},
                {"analysis": "【技能Gap分析】数据分析需要掌握Python数据分析库。", "current": ["SQL基础"], "missing": ["Pandas", "NumPy", "数据可视化"], "howToAcquire": "通过Kaggle竞赛练习，观看B站《Python数据分析全套教程》。", "timeCost": "3-6个月"},
                {"analysis": "【技能Gap分析】企业服务需要补充产品设计、用户研究等技能。", "current": ["技术理解"], "missing": ["产品设计", "用户研究"], "howToAcquire": "阅读《人人都是产品经理》，参加人人都是产品经理网站课程。", "timeCost": "3-6个月"}
            ],
            "recommendedIndustries": [
                {"name": "AI应用开发", "outlook": "长期看好", "analysis": "用户技术背景与AI应用开发高度匹配，转型成功后预期薪资25-45K/月。", "hotRoles": ["AI工程师 25-45K/月", "提示词工程师 20-35K/月"], "entryTips": "先从学习Python机器学习库开始，在Kaggle上做项目。", "salaryRange": "25-45K/月", "risks": ["技术更新快", "需要持续学习"], "matchReason": "技术背景高度匹配", "professionalReview": "该行业暂无专业点评"},
                {"name": "数据分析", "outlook": "长期看好", "analysis": "数据分析技能门槛适中，用户编程基础可以帮助快速上手。", "hotRoles": ["数据分析师 15-30K/月", "商业分析师 18-35K/月"], "entryTips": "掌握Python数据栈，考取CDA数据分析师证书。", "salaryRange": "15-30K/月", "risks": ["竞争加剧"], "matchReason": "编程基础可迁移", "professionalReview": "该行业暂无专业点评"},
                {"name": "企业服务", "outlook": "中期看好", "analysis": "项目管理经验可以迁移到企业服务岗位，需要补充产品设计技能。", "hotRoles": ["企业服务经理 20-40K/月", "AI产品经理 25-50K/月"], "entryTips": "学习产品设计思维，从内部转岗做起。", "salaryRange": "20-40K/月", "risks": ["岗位竞争激烈"], "matchReason": "项目管理经验可迁移", "professionalReview": "该行业暂无专业点评"}
            ],
            "pathways": [
                {"analysis": "路径1：技术深耕路线，从当前技术领域转向AI应用开发。", "steps": [{"name": "学习AI基础", "desc": "学习机器学习、深度学习基础"}, {"name": "做项目", "desc": "在Kaggle或GitHub上做项目"}], "expectedIncome": "转正后 25-45K/月", "successRate": "70%", "cost": "5000-10000元", "timeline": "6-12个月"},
                {"analysis": "路径2：数据转型路线，转向数据分析领域。", "steps": [{"name": "学Python数据栈", "desc": "Pandas、NumPy、Matplotlib"}, {"name": "考证书", "desc": "考取CDA数据分析师"}], "expectedIncome": "转正后 15-30K/月", "successRate": "75%", "cost": "3000-8000元", "timeline": "3-6个月"},
                {"analysis": "路径3：产品管理路线，转向企业服务。", "steps": [{"name": "学产品思维", "desc": "学习产品设计、用户研究"}, {"name": "做原型", "desc": "用Figma做产品原型"}], "expectedIncome": "转正后 20-40K/月", "successRate": "60%", "cost": "2000-5000元", "timeline": "3-6个月"}
            ],
            "actionPlan": [
                {"industry": "AI应用开发", "actions": [{"title": "学习AI基础", "content": "完成Coursera机器学习课程", "timeframe": "1-3个月"}, {"title": "做项目", "content": "在Kaggle上完成3个项目", "timeframe": "3-6个月"}]},
                {"industry": "数据分析", "actions": [{"title": "学Python数据栈", "content": "B站全套教程+实战", "timeframe": "1-3个月"}, {"title": "考证书", "content": "CDA数据分析师", "timeframe": "3-6个月"}]},
                {"industry": "企业服务", "actions": [{"title": "学产品思维", "content": "阅读《人人都是产品经理》", "timeframe": "1个月"}, {"title": "做原型", "content": "用Figma做产品原型", "timeframe": "2-3个月"}]}
            ],
            "risks": ["AI技术更新快，需要持续学习", "数据分析岗位竞争加剧", "企业服务岗位要求较高"]
        }
        return json.dumps(fallback, ensure_ascii=False)
    else:
        # 轻量版fallback
        return '{"summary": {"analysis": "AI API未配置，使用模拟数据", "result": "推荐转型到AI方向", "short": "AI方向最适合"}, "macroTrends": [{"trend": "AI应用", "outlook": "长期看好", "analysis": "AI应用行业发展迅速"}], "persona": [{"label": "技能", "value": "编程基础"}], "recommendedIndustries": [{"name": "AI应用", "outlook": "长期看好"}], "risks": ["需要学习新技术"]}'

def call_ai_api_sync(prompt: str) -> str:
    """同步调用AI API（支持本地模式）"""

    # 默认禁用本地模式，使用真实API（智谱AI），除非明确设置 USE_LOCAL_MODE=true
    env_mode = os.getenv('USE_LOCAL_MODE', '').lower()
    use_local = env_mode == 'true'  # 默认False，除非明确设为true
    print(f"[DEBUG] USE_LOCAL_MODE = {use_local}, 环境变量值: {os.getenv('USE_LOCAL_MODE', '未设置(默认禁用)')}")
    if use_local:
        # 纯本地模式 - 使用全局变量中的请求数据
        global _last_request_data
        if _last_request_data['user_type'] is not None:
            print("使用纯本地模式生成报告...")
            return generate_local_report_sync(
                _last_request_data['user_type'],
                _last_request_data['answers'],
                _last_request_data['questions'],
                _last_request_data['report_type']
            )
        else:
            print("警告：本地模式已启用，但请求数据未设置，使用fallback")
            return generate_fallback_response(prompt)
    
    api_config = None
    
    if ZHIPU_API_KEY:
        api_config = {
            "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "model": "glm-4-flash",
            "key": ZHIPU_API_KEY,
            "type": "openai"
        }
    elif ARK_API_KEY:
        api_config = {
            "url": "https://ark.cn-beijing.volces.com/api/v3/responses",
            "model": "ep-20260412151056-zt555",
            "key": ARK_API_KEY,
            "type": "ark_v3"
        }
    elif DEEPSEEK_API_KEY:
        api_config = {
            "url": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "key": DEEPSEEK_API_KEY,
            "type": "openai"
        }
    elif OPENAI_API_KEY:
        api_config = {
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o-mini",
            "key": OPENAI_API_KEY,
            "type": "openai"
        }
    
    if not api_config:
        return generate_fallback_response(prompt)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_config['key']}"
    }
    
    try:
        if api_config.get("type") == "ark_v3":
            payload = {
                "model": api_config["model"],
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"你是一位专业的职业发展顾问。请用JSON格式回复。\n\n{prompt}"
                            }
                        ]
                    }
                ],
                "max_tokens": 8000,
                "temperature": 0.7
            }
            r = requests.post(api_config["url"], headers=headers, json=payload, timeout=(10, 300))
            r.raise_for_status()
            data = r.json()
            return data["output"][0]["content"][0]["text"]
        else:
            payload = {
                "model": api_config["model"],
                "messages": [
                    {"role": "system", "content": "你是一位专业的职业发展顾问。请用JSON格式回复。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 8000
            }
            r = httpx.post(api_config["url"], headers=headers, json=payload, timeout=httpx.Timeout(300.0, connect=10.0), trust_env=False)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI API调用失败: {e}")
        return generate_fallback_response(prompt)

async def call_ai_api(prompt: str) -> dict:
    """调用AI API（自动选择可用的服务商）"""
    print(f"[AI-API] ===== 开始调用 AI API =====")
    print(f"[AI-API] 时间戳: {time.time()}")
    
    # 优先级: 智谱AI > 豆包 ARK > DeepSeek > OpenAI
    api_config = None
    
    if ZHIPU_API_KEY:
        # 智谱AI - ¥0.1/百万tokens，国内可访问
        api_config = {
            "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "model": "glm-4-flash",
            "key": ZHIPU_API_KEY,
            "type": "openai"
        }
        print(f"[AI-API] 使用智谱AI (ZhipuAI)")
    elif ARK_API_KEY:
        # 豆包 ARK API v3 - 使用 /api/v3/responses 接口
        api_config = {
            "url": "https://ark.cn-beijing.volces.com/api/v3/responses",
            "model": "ep-20260412151056-zt555",  # 使用端点ID
            "key": ARK_API_KEY,
            "type": "ark_v3"
        }
        print(f"[AI-API] 使用豆包 ARK API v3")
    elif DEEPSEEK_API_KEY:
        # DeepSeek - ¥1/百万tokens
        api_config = {
            "url": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "key": DEEPSEEK_API_KEY,
            "type": "openai"
        }
        print(f"[AI-API] 使用 DeepSeek API")
    elif OPENAI_API_KEY:
        # OpenAI - 较贵
        api_config = {
            "url": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o-mini",
            "key": OPENAI_API_KEY,
            "type": "openai"
        }
        print(f"[AI-API] 使用 OpenAI API")
    
    if not api_config:
        print(f"[AI-API] ❌ 没有可用的 AI API 配置！")
        return None
    
    print(f"[AI-API] API URL: {api_config['url']}")
    print(f"[AI-API] 模型: {api_config['model']}")
    print(f"[AI-API] 提示词长度: {len(prompt)} 字符")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_config['key']}"
    }
    
    if api_config.get("type") == "ark_v3":
        # 豆包 ARK v3 API 格式
        payload = {
            "model": api_config["model"],
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"你是一位专业的职业发展顾问。请用JSON格式回复。\n\n{prompt}"
                        }
                    ]
                }
            ],
            "max_tokens": 8000,
            "temperature": 0.7
        }
        try:
            print(f"[AI-API] 发送请求到豆包 ARK v3...")
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0), trust_env=False) as client:
                response = await client.post(api_config["url"], headers=headers, json=payload)
                print(f"[AI-API] 响应状态码: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                print(f"[AI-API] ✅ 豆包 ARK 调用成功")
                return data["output"][0]["content"][0]["text"]
        except Exception as e:
            print(f"[AI-API] ❌ 豆包 ARK 调用失败: {type(e).__name__}: {e}")
            return None
    else:
        # OpenAI 兼容格式
        payload = {
            "model": api_config["model"],
            "messages": [
                {"role": "system", "content": "你是一位专业的职业发展顾问。请用JSON格式回复。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 8000
        }
        try:
            print(f"[AI-API] 发送请求到 OpenAI 兼容 API...")
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0), trust_env=False) as client:
                response = await client.post(api_config["url"], headers=headers, json=payload)
                print(f"[AI-API] 响应状态码: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                print(f"[AI-API] ✅ API 调用成功")
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AI-API] ❌ API 调用失败: {type(e).__name__}: {e}")
            return None

def parse_json_response(content: str) -> dict:
    """解析AI返回的JSON"""
    
    # 尝试提取JSON代码块
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = content
    
    # 尝试直接解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # 尝试查找JSON对象的开始和结束
    try:
        # 找第一个 {
        start = json_str.find('{')
        if start != -1:
            # 尝试找到匹配的 }
            json_part = json_str[start:]
            # 尝试逐步扩展直到能解析
            for i in range(len(json_part), 0, -1):
                try:
                    result = json.loads(json_part[:i])
                    # 检查是否包含必要的字段
                    if 'summary' in result or 'recommendedIndustries' in result:
                        return result
                except:
                    continue
    except:
        pass
    
    # 如果所有尝试都失败，返回错误信息
    return {
        "summary": {"analysis": "解析失败", "result": content[:500], "short": "请重试"},
        "macroTrends": [],
        "persona": [],
        "recommendedIndustries": [],
        "risks": ["数据解析失败，请重试"],
        "keyInsight": "请重试"
    }

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    """AI职业分析API（轻量版 - 带完全匹配缓存 + 后台异步生成）"""
    import time

    try:
        # 答案数据清洗
        cleaned_answers = clean_answers(request.questions, request.answers, str(request.userType))
        request = AnalysisRequest(
            userType=request.userType,
            answers=cleaned_answers,
            questions=request.questions,
            version=getattr(request, 'version', 'light')
        )

        # 【修复】设置请求数据供本地模式使用
        set_request_data(request.userType, request.answers, request.questions, 'light')

        # ========== 【完美流程】极短锁读缓存 → 有缓存立即返回 ==========
        cache_key = generate_cache_key(request.answers)
        cached_result, cache_hit, _ = get_cache(
            request.answers, 
            version="light", 
            user_type=request.userType
        )
        
        if cache_hit and cached_result:
            print(f"[CACHE HIT] light_{request.userType} - {cache_key[:8]}...")
            return cached_result
        print(f"[CACHE MISS] light_{request.userType} - {cache_key[:8]}...")
        
        # ========== 无缓存 → 检查是否正在生成中 ==========
        if is_generating(cache_key):
            print(f"[GENERATING] light_{request.userType} - {cache_key[:8]}... 等待后台生成")
            return {
                "status": "generating",
                "message": "正在生成分析报告，请稍候（约10-30秒）后刷新重试",
                "cacheKey": cache_key,
                "version": "light"
            }
        
        # ========== 未在生成 → 启动后台任务 + 立即返回 ==========
        print(f"[START BG] light_{request.userType} - {cache_key[:8]}...")
        start_generating(cache_key)
        
        # 启动后台异步生成（不等待完成）
        asyncio.create_task(
            generate_ai_background(
                request.userType, 
                request.answers, 
                request.questions, 
                "light", 
                cache_key
            )
        )
        
        # 立即返回给用户（无需等待AI生成）
        return {
            "status": "generating",
            "message": "正在生成分析报告，请稍候（约10-30秒）后刷新重试",
            "cacheKey": cache_key,
            "version": "light"
        }
        
    except httpx.HTTPStatusError as e:
        return {"error": f"AI服务错误: {e.response.status_code}", "fallback": True}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "fallback": True}

@app.get("/api/analyze/poll/{cache_key}")
async def poll_light_analysis(cache_key: str):
    """轮询轻量版分析结果"""
    # 检查缓存中是否有结果
    cached_result, cache_hit, _ = get_cache_by_key(cache_key, version="light")
    
    if cache_hit and cached_result:
        return {"status": "completed", "analysis": cached_result}
    
    # 检查是否还在生成中
    if is_generating(cache_key):
        return {
            "status": "generating",
            "message": "正在生成中，请稍候...",
            "cacheKey": cache_key
        }
    
    return {"status": "not_found", "message": "未找到对应的分析任务"}

@app.get("/api/analyze-deep/poll/{cache_key}")
async def poll_deep_analysis(cache_key: str):
    """轮询深度版分析结果"""
    # 检查缓存中是否有结果
    cached_result, cache_hit, _ = get_cache_by_key(cache_key, version="deep")
    
    if cache_hit and cached_result:
        return {"status": "completed", "analysis": cached_result}
    
    # 检查是否还在生成中
    if is_generating(cache_key):
        return {
            "status": "generating",
            "message": "正在生成中，请稍候...",
            "cacheKey": cache_key
        }
    
    return {"status": "not_found", "message": "未找到对应的分析任务"}

@app.get("/api/analyze-vip/poll/{cache_key}")
async def poll_vip_analysis(cache_key: str):
    """轮询VIP版分析结果"""
    # 检查缓存中是否有结果
    cached_result, cache_hit, _ = get_cache_by_key(cache_key, version="vip")
    
    if cache_hit and cached_result:
        cached_result['_isVip'] = True
        return {"status": "completed", "analysis": cached_result}
    
    # 检查是否还在生成中
    if is_generating(cache_key):
        return {
            "status": "generating",
            "message": "正在生成中，请稍候...",
            "cacheKey": cache_key
        }
    
    return {"status": "not_found", "message": "未找到对应的分析任务"}

@app.post("/api/analyze-deep")
async def analyze_deep(request: AnalysisRequest):
    """深度评估版AI职业分析API（带完全匹配缓存 + 后台异步生成）"""

    try:
        # 答案数据清洗
        cleaned_answers = clean_answers(request.questions, request.answers, str(request.userType))
        request = AnalysisRequest(
            userType=request.userType,
            answers=cleaned_answers,
            questions=request.questions,
            version=getattr(request, 'version', 'deep')
        )

        # 【修复】设置请求数据供本地模式使用
        set_request_data(request.userType, request.answers, request.questions, 'deep')

        # ========== 【完美流程】极短锁读缓存 → 有缓存立即返回 ==========
        cache_key = generate_cache_key(request.answers)
        cached_result, cache_hit, _ = get_cache(
            request.answers, 
            version="deep", 
            user_type=request.userType
        )
        
        if cache_hit and cached_result:
            print(f"[CACHE HIT] deep_{request.userType} - {cache_key[:8]}...")
            return {"analysis": cached_result}
        print(f"[CACHE MISS] deep_{request.userType} - {cache_key[:8]}...")
        
        # ========== 无缓存 → 检查是否正在生成中 ==========
        if is_generating(cache_key):
            print(f"[GENERATING] deep_{request.userType} - {cache_key[:8]}... 等待后台生成")
            return {
                "status": "generating",
                "message": "正在生成深度分析报告，请稍候（约30-60秒）后刷新重试",
                "cacheKey": cache_key,
                "version": "deep"
            }
        
        # ========== 未在生成 → 启动后台任务 + 立即返回 ==========
        print(f"[START BG] deep_{request.userType} - {cache_key[:8]}...")
        start_generating(cache_key)
        
        # 启动后台异步生成（不等待完成），使用请求中的 version 参数
        asyncio.create_task(
            generate_ai_background(
                request.userType, 
                request.answers, 
                request.questions, 
                request.version,  # 使用请求中的 version（deep 或 vip）
                cache_key
            )
        )
        
        # 立即返回给用户（无需等待AI生成）
        return {
            "status": "generating",
            "message": "正在生成深度分析报告，请稍候（约30-60秒）后刷新重试",
            "cacheKey": cache_key,
            "version": "deep"
        }
        
    except httpx.HTTPStatusError as e:
        return {"error": f"AI服务错误: {e.response.status_code}", "fallback": True}
    except Exception as e:
        return {"error": str(e), "fallback": True}

@app.post("/api/analyze-vip")
async def analyze_vip(request: Request):
    """VIP深度评估版AI职业分析API（流程与深度版统一，带完全匹配缓存 + 后台异步生成）"""
    
    try:
        # 获取请求数据
        data = await request.json()
        user_type = int(data.get('userType', 0))  # 强制转int，避免缓存键匹配失败
        answers = data.get('answers', {})
        questions = data.get('questions', [])
        
        # 答案数据清洗
        answers = clean_answers(questions, answers, str(user_type))
        
        # 【修复】设置请求数据供本地模式使用
        set_request_data(user_type, answers, questions, 'vip')
        
        # ========== 【完美流程】极短锁读缓存 → 有缓存立即返回 ==========
        cache_key = generate_cache_key(answers)
        cached_result, cache_hit, _ = get_cache(
            answers, 
            version="vip", 
            user_type=user_type
        )
        
        if cache_hit and cached_result:
            print(f"[CACHE HIT] vip_{user_type} - {cache_key[:8]}...")
            cached_result['_isVip'] = True
            return cached_result
        print(f"[CACHE MISS] vip_{user_type} - {cache_key[:8]}...")
        
        # ========== 无缓存 → 检查是否正在生成中 ==========
        if is_generating(cache_key):
            print(f"[GENERATING] vip_{user_type} - {cache_key[:8]}... 等待后台生成")
            return {
                "status": "generating",
                "message": "正在生成VIP深度分析报告，请稍候（约30-60秒）后刷新重试",
                "cacheKey": cache_key,
                "version": "vip"
            }
        
        # ========== 未在生成 → 启动后台任务 + 立即返回 ==========
        print(f"[START BG] vip_{user_type} - {cache_key[:8]}...")
        start_generating(cache_key)
        
        # 启动后台异步生成（不等待完成）
        asyncio.create_task(
            generate_ai_background(
                user_type, 
                answers, 
                questions, 
                "vip", 
                cache_key
            )
        )
        
        # 立即返回给用户（无需等待AI生成）
        return {
            "status": "generating",
            "message": "正在生成VIP深度分析报告，请稍候（约30-60秒）后刷新重试",
            "cacheKey": cache_key,
            "version": "vip"
        }
        
    except httpx.HTTPStatusError as e:
        return {"error": f"AI服务错误: {e.response.status_code}", "fallback": True}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "fallback": True}

def build_vip_analysis_prompt(user_type, answers, questions, scoring_info=""):
    """构建VIP深度分析提示词"""
    from datetime import datetime
    current_year = datetime.now().year

    user_type_names = {
        1: "30-40岁的职场转型者（VIP深度版）",
        2: "应届/毕业1-3年的年轻人（VIP深度版）",
        3: "学生家长（VIP深度版，分析对象是孩子）"
    }

    # 解析答题数据
    answer_lines = []
    for q_idx, q in enumerate(questions):
        user_answer = answers.get(str(q_idx)) or answers.get(q_idx)
        if user_answer:
            opt = next((o for o in q.get("options", [])
                       if o.get("value") == user_answer or o.get("label") == user_answer), None)
            answer_text = opt.get("label", user_answer) if opt else user_answer
            answer_lines.append(f"Q{q_idx+1}: {q.get('text', '')} -> {answer_text}")

    prompt = f"""你是一位资深的职业规划顾问，请基于以下答题数据，输出一份完整的VIP职业规划报告。

用户类型：{user_type_names.get(user_type, '未知')}
当前年份：{current_year}年
答题数据：
{chr(10).join(answer_lines)}

你必须输出一个严格的 JSON 对象，必须包含以下所有顶级字段（缺一不可）：
aiAnalysis, summary, macroTrends, persona, skillGap, recommendedIndustries, pathways, actionPlan, risks

各模块约束：
1. aiAnalysis: 对象，包含 process（100-150字分析过程）、conclusion（100-150字结论）、confidence（置信度）
2. summary: 对象，包含 overallScore、recommendedIndustries（数组）、analysis、result、short
3. macroTrends: 数组，长度=3，每个元素包含 trend、outlook（长期看好/中期看好/短期过渡）、period、analysis（100-150字，需真实数据）
4. persona: 对象，包含 type、analysis、strengths（数组，2-4个）、limitations（数组，1-3个）
5. skillGap: 数组，长度=3，每个元素包含 industry、analysis、current（数组）、missing（数组）、howToAcquire
6. recommendedIndustries: 数组，长度=3，每个元素包含 name、reason、outlook、period、matchScore、analysis（100-150字）、hotRoles、entryTips、salaryRange
7. pathways: 数组，长度=3，每个元素包含 name、industry、analysis、steps（数组，含 step/timeline/cost）
8. actionPlan: 数组，长度=3，每个元素包含 industry、actions（数组，含 phase/analysis/description）
9. risks: 数组，长度>=3，每个元素包含 type、analysis、description、mitigation

绝对禁止：
- 使用 XX、xxx、待定、未知、暂无、TBD 等占位符
- 空字符串、空数组、空对象
- 行业名称必须真实存在，禁止编造
- 所有数字、薪资、时间必须具体真实
- persona 数组中每个 value 必须是中文自然语言，严禁输出内部代码
- risks 数组中每个元素必须是字符串，不能是对象

请直接输出 JSON 对象，不要用代码块包裹。

行业名称必须真实存在，如：人工智能/大数据, 半导体/芯片, 新能源/储能, 出海/跨境, 医疗健康, 金融科技, 机器人/自动化, 软件开发/互联网, 低空经济/无人机, 碳中和/ESG, 智能制造, 职业教育, 内容创作/新媒体, 养老/健康, 物流/供应链等。禁止编造行业名称。"""

    # ========== 家长特殊处理 ==========
    if user_type == 3:
        prompt += """

【重要】分析对象是孩子，不是家长。必须根据孩子的学习阶段和类型推荐行业，禁止引用家长的职业背景。
理科/工科→推荐AI、机器人、半导体、新能源等；文科/商科→出海、内容创作、金融科技等；艺术/创意→AI设计、数字艺术、新媒体等；职业技术→智能制造、新能源技术、无人机等。"""
    
    return prompt


import uuid
import msvcrt
import time

# VIP咨询数据存储
VIP_CONSULTS_FILE = Path(__file__).parent / "vip_consults.json"
VIP_LOCK_FILE = Path(__file__).parent / "vip_consults.lock"

class FileLock:
    """跨平台文件锁（Windows/macOS/Linux）"""
    
    def __init__(self, lock_file: Path, timeout: float = 10.0):
        self.lock_file = lock_file
        self.timeout = timeout
        self._fd = None
        self._acquired = False
    
    def acquire(self) -> bool:
        """获取文件锁，返回是否成功"""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                # Windows: 使用msvcrt的独占锁
                import sys
                if sys.platform == 'win32':
                    # 创建锁文件
                    self._fd = open(self.lock_file, 'w')
                    # 尝试锁定（独占模式）
                    msvcrt.locking(self._fd.fileno(), msvcrt.LK_NBLCK, 1)
                    self._acquired = True
                    return True
                else:
                    # Unix系统使用fcntl
                    import fcntl
                    self._fd = open(self.lock_file, 'w')
                    fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._acquired = True
                    return True
            except (IOError, OSError):
                # 锁定失败，稍等后重试
                if self._fd:
                    try:
                        self._fd.close()
                    except:
                        pass
                    self._fd = None
                time.sleep(0.05)  # 50ms后重试
        
        return False
    
    def release(self):
        """释放文件锁"""
        if self._acquired and self._fd:
            try:
                import sys
                if sys.platform == 'win32':
                    msvcrt.locking(self._fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
                self._fd.close()
            except:
                pass
            finally:
                self._fd = None
                self._acquired = False
        
        # 清理锁文件
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except:
            pass
    
    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"获取文件锁超时: {self.lock_file}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


def load_vip_consults() -> list:
    """加载VIP咨询数据（带文件锁）"""
    lock = FileLock(VIP_LOCK_FILE, timeout=10.0)
    try:
        if lock.acquire():
            if VIP_CONSULTS_FILE.exists():
                try:
                    return json.loads(VIP_CONSULTS_FILE.read_text(encoding="utf-8"))
                except:
                    return []
            return []
        return []
    finally:
        lock.release()


def save_vip_consults(consults: list):
    """保存VIP咨询数据（带文件锁）"""
    lock = FileLock(VIP_LOCK_FILE, timeout=10.0)
    try:
        if lock.acquire():
            VIP_CONSULTS_FILE.write_text(
                json.dumps(consults, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
    finally:
        lock.release()


def delete_vip_consult(consult_id: str) -> bool:
    """删除VIP咨询记录（带文件锁和重试机制）"""
    # 重试机制：最多尝试3次，每次间隔0.5秒
    for attempt in range(3):
        lock = FileLock(VIP_LOCK_FILE, timeout=3.0)  # 每次尝试最多3秒
        try:
            if lock.acquire():
                consults = []
                if VIP_CONSULTS_FILE.exists():
                    try:
                        consults = json.loads(VIP_CONSULTS_FILE.read_text(encoding="utf-8"))
                    except:
                        return False
                
                original_len = len(consults)
                # 使用宽松类型比较（JSON中ID可能是数字或字符串）
                consult_id_str = str(consult_id)
                consults = [c for c in consults if str(c.get("id")) != consult_id_str]
                
                if len(consults) == original_len:
                    return False  # 未找到记录
                
                VIP_CONSULTS_FILE.write_text(
                    json.dumps(consults, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                return True
            # 获取锁失败，等待后重试
            time.sleep(0.5)
        finally:
            try:
                lock.release()
            except:
                pass
    return False  # 3次尝试后仍然失败

# ==================== VIP咨询管理API ====================

@app.get("/api/vip/consults")
async def get_vip_consults():
    """获取所有VIP咨询记录"""
    consults = load_vip_consults()
    # 按时间倒序排列
    consults.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return consults

@app.get("/api/vip/consult/{consult_id}")
async def get_vip_consult(consult_id: str):
    """获取指定VIP咨询记录"""
    consults = load_vip_consults()
    for consult in consults:
        # 使用宽松类型比较（JSON中ID可能是数字或字符串）
        if str(consult.get("id")) == str(consult_id):
            return consult
    raise HTTPException(status_code=404, detail="咨询记录不存在")

class VipConsultRequest(BaseModel):
    email: str
    answers: dict = {}
    answerTexts: dict = {}  # 答案显示文本
    consultQuestions: list = []
    userType: str = ""
    questions: list = []

@app.post("/api/vip/consult")
async def create_vip_consult(request: VipConsultRequest):
    """提交VIP咨询"""
    consults = load_vip_consults()
    
    new_consult = {
        "id": str(uuid.uuid4())[:8],
        "email": request.email,
        "answers": request.answers,
        "answerTexts": request.answerTexts,  # 保存答案显示文本
        "consultQuestions": request.consultQuestions,
        "userType": request.userType,
        "questions": request.questions,
        "reportData": {},
        "createdAt": datetime.now().timestamp()
    }
    
    consults.append(new_consult)
    save_vip_consults(consults)
    
    return {
        "success": True,
        "id": new_consult["id"],
        "message": "咨询已提交"
    }

@app.put("/api/vip/consult/{consult_id}/report")
async def save_vip_report(consult_id: str, request: Request):
    """保存VIP咨询的AI报告数据"""
    consults = load_vip_consults()
    body = await request.json()
    
    # 使用宽松类型比较（JSON中ID可能是数字或字符串）
    consult_id_str = str(consult_id)
    for i, consult in enumerate(consults):
        if str(consult.get("id")) == consult_id_str:
            consults[i]["reportData"] = body.get("reportData", {})
            consults[i]["updatedAt"] = datetime.now().timestamp()
            save_vip_consults(consults)
            return {"success": True, "message": "报告已保存"}
    
    raise HTTPException(status_code=404, detail="咨询记录不存在")

@app.delete("/api/vip/consult/{consult_id}")
async def delete_vip_consult_api(consult_id: str):
    """删除VIP咨询记录（带文件锁，防止并发冲突）"""
    # 使用新的带锁删除函数
    if delete_vip_consult(consult_id):
        return {"success": True, "message": "已删除"}
    raise HTTPException(status_code=404, detail="咨询记录不存在")

@app.put("/api/vip/consult/{consult_id}/read")
async def update_vip_read_status(consult_id: str, request: Request):
    """更新VIP咨询的已阅/未阅状态"""
    consults = load_vip_consults()
    body = await request.json()
    is_read = body.get("isRead", False)
    
    # 查找并更新记录
    found = False
    for consult in consults:
        if str(consult.get("id", "")) == str(consult_id):
            consult["isRead"] = is_read
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    
    # 保存更新
    if save_vip_consults(consults):
        return {"success": True, "isRead": is_read}
    raise HTTPException(status_code=500, detail="保存失败")

# ==================== 支付API ====================

# 支付配置
PAYMENT_CONFIG = {
    "deep": {
        "name": "深度趣味测试版",
        "price": 9.9,
        "description": "25-30道有趣测试题 + 趣味测试结果 + 趋势探索 + 趣味提示"
    },
    "vip": {
        "name": "VIP趣味体验版",
        "price": 19.9,
        "description": "深度趣味测试全部功能 + 趣味问答 + AI趣味解读"
    }
}

# 抖音支付商户配置（从环境变量读取，上线前必须在云托管配置）
DOUYIN_MERCHANT_ID = os.getenv("DOUYIN_MERCHANT_ID", "")
DOUYIN_APP_ID = os.getenv("DOUYIN_APP_ID", "")

# 支持拆分密钥（解决环境变量字符超限问题）
def load_combined_env(prefix: str, default: str = "") -> str:
    """合并多个环境变量为一个字符串"""
    result = []
    i = 1
    while True:
        key = f"{prefix}{i}"
        value = os.getenv(key, "")
        if not value:
            break
        result.append(value)
        i += 1
    if result:
        return "".join(result)
    # 尝试直接读取完整变量
    return os.getenv(prefix.rstrip("1"), default)

DOUYIN_APP_PRIVATE_KEY = load_combined_env("DOUYIN_PRIVATE_KEY", "")
DOUYIN_PLATFORM_PUBLIC_KEY = load_combined_env("DOUYIN_PUBLIC_KEY", "")
DOUYIN_PAYMENT_CALLBACK_URL = os.getenv("DOUYIN_PAYMENT_CALLBACK_URL", "")

class PaymentCreateRequest(BaseModel):
    version: str  # "deep" 或 "vip"
    device_id: str = ""

@app.post("/api/payment/create")
async def create_payment(request: PaymentCreateRequest):
    """创建支付订单"""
    version = request.version
    if version not in PAYMENT_CONFIG:
        raise HTTPException(status_code=400, detail="无效的版本类型")
    
    config = PAYMENT_CONFIG[version]
    
    # 创建订单
    order_id = f"{version.upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
    
    conn, cursor = db_execute('''
        INSERT INTO payments (order_id, version, amount, payment_method, status, device_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (order_id, version, config["price"], "wechat", "pending", request.device_id))
    conn.commit()
    conn.close()
    
    # 生成支付二维码URL（模拟）- 实际接入微信/支付宝时替换
    qr_data = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={order_id}"
    
    return {
        "order_id": order_id,
        "version": version,
        "amount": config["price"],
        "name": config["name"],
        "description": config["description"],
        "qr_code_url": qr_data,
        "status": "pending",
        "next_step": "select_identity"   # 支付后跳转：选择用户身份
    }

@app.get("/api/payment/status/{order_id}")
async def get_payment_status(order_id: str):
    """查询支付状态"""
    conn, cursor = db_execute(
        "SELECT order_id, version, amount, status, created_at, paid_at FROM payments WHERE order_id = ?",
        (order_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return {
        "order_id": row[0],
        "version": row[1],
        "amount": row[2],
        "status": row[3],
        "created_at": row[4],
        "paid_at": row[5]
    }

@app.post("/api/payment/simulate")
async def simulate_payment(request: Request):
    """模拟支付成功（用于测试）"""
    body = await request.json()
    order_id = body.get("order_id")
    
    if not order_id:
        raise HTTPException(status_code=400, detail="缺少order_id")
    
    conn, cursor = db_execute('''
        UPDATE payments 
        SET status = 'paid', paid_at = ?
        WHERE order_id = ? AND status = 'pending'
    ''', (datetime.now().timestamp(), order_id))
    changes = cursor.rowcount
    conn.commit()
    conn.close()
    
    if changes == 0:
        raise HTTPException(status_code=404, detail="订单不存在或已支付")
    
    return {"success": True, "message": "模拟支付成功"}

@app.get("/api/payment/check/{order_id}")
async def check_payment(order_id: str):
    """检查订单是否已支付（用于前端轮询）"""
    conn, cursor = db_execute("SELECT status, version FROM payments WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    status, version = row
    
    if status == "paid":
        # 已支付，返回访问令牌和跳转指令
        return {
            "paid": True,
            "version": version,
            "token": f"PAID_{order_id}",  # 前端可使用此token验证支付状态
            "redirect": f"/{version}-select-identity"  # 跳转到对应版本的身份选择页
        }
    else:
        return {
            "paid": False,
            "version": version,
            "token": None
        }

@app.get("/api/payment/config")
async def get_payment_config():
    """获取支付配置信息"""
    return PAYMENT_CONFIG

# ==================== 抖音小程序支付API ====================

import base64
import hashlib
import hmac
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def generate_douyin_sign(params: dict, private_key: str) -> str:
    """生成抖音支付签名"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if v is not None and v != ""])
    try:
        private_key_obj = serialization.load_pem_private_key(
            private_key.encode('utf-8'),
            password=None
        )
        signature = private_key_obj.sign(
            sign_str.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        print(f"[签名错误] {e}")
        return ""

def verify_douyin_sign(params: dict, sign: str, public_key: str) -> bool:
    """验证抖音支付签名"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if k != "sign" and v is not None and v != ""])
    try:
        public_key_obj = serialization.load_pem_public_key(
            public_key.encode('utf-8')
        )
        public_key_obj.verify(
            base64.b64decode(sign),
            sign_str.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"[验签错误] {e}")
        return False

class DouyinPaymentCreateRequest(BaseModel):
    version: str  # "deep" 或 "vip"
    amount: int  # 金额（分）
    subject: str  # 商品描述
    device_id: str = ""
    out_order_no: str = ""

@app.post("/api/douyin-payment/create-order")
async def create_douyin_payment(request: DouyinPaymentCreateRequest):
    """创建抖音小程序支付订单"""
    version = request.version
    if version not in PAYMENT_CONFIG:
        raise HTTPException(status_code=400, detail="无效的版本类型")
    
    config = PAYMENT_CONFIG[version]
    
    # 创建订单号（使用传入的或自动生成）
    order_id = request.out_order_no or f"{version.upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
    
    # 保存订单到数据库
    conn, cursor = db_execute('''
        INSERT INTO payments (order_id, version, amount, payment_method, status, device_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (order_id, version, request.amount / 100.0, "douyin", "pending", request.device_id))
    conn.commit()
    conn.close()
    
    # 检查是否配置了真实支付
    if not DOUYIN_MERCHANT_ID or not DOUYIN_APP_ID or not DOUYIN_APP_PRIVATE_KEY:
        # 没有配置，返回模拟模式
        return {
            "code": 0,
            "order_id": order_id,
            "order_token": f"TOK_{order_id}",
            "amount": request.amount,
            "message": "订单创建成功（模拟模式）"
        }
    
    # 真实抖音支付 - 调用预下单接口
    try:
        import requests
        timestamp = str(int(datetime.now().timestamp()))
        nonce_str = uuid.uuid4().hex[:16]
        
        # 构建请求参数
        params = {
            "app_id": DOUYIN_APP_ID,
            "out_order_no": order_id,
            "total_amount": request.amount,
            "subject": request.subject,
            "body": config["description"],
            "valid_time": "3600",
            "notify_url": DOUYIN_PAYMENT_CALLBACK_URL,
            "timestamp": timestamp,
            "nonce_str": nonce_str,
        }
        
        # 生成签名
        sign = generate_douyin_sign(params, DOUYIN_APP_PRIVATE_KEY)
        params["sign"] = sign
        params["sign_type"] = "SHA256"
        
        # 调用预下单接口
        url = "https://developer.toutiao.com/api/apps/ecpay/v1/create_order"
        response = requests.post(url, json=params, timeout=10)
        result = response.json()
        
        if result.get("code") == 0:
            return {
                "code": 0,
                "order_id": order_id,
                "order_token": result.get("data", {}).get("order_token", ""),
                "amount": request.amount,
                "message": "订单创建成功"
            }
        else:
            print(f"[抖音支付] 预下单失败: {result}")
            return {
                "code": result.get("code", 500),
                "order_id": order_id,
                "order_token": "",
                "amount": request.amount,
                "message": result.get("msg", "订单创建失败")
            }
    except Exception as e:
        print(f"[抖音支付] 错误: {e}")
        return {
            "code": 500,
            "order_id": order_id,
            "order_token": "",
            "amount": request.amount,
            "message": "服务器错误"
        }

# ==================== 抖音支付回调接口 ====================

@app.post("/api/douyin-payment/callback")
async def douyin_payment_callback(request: Request):
    """抖音支付回调 - 接收支付成功通知并更新订单"""
    try:
        body = await request.json()
        print(f"[支付回调] 收到通知: {json.dumps(body, ensure_ascii=False)[:200]}")
        
        # 验证签名
        sign = body.get("sign", "")
        if DOUYIN_PLATFORM_PUBLIC_KEY and sign:
            if not verify_douyin_sign(body, sign, DOUYIN_PLATFORM_PUBLIC_KEY):
                print(f"[支付回调] ❌ 签名验证失败")
                return {"code": 1, "msg": "签名验证失败"}
        
        order_id = body.get("out_order_no") or body.get("order_id")
        trade_no = body.get("trade_no", "")
        pay_time = body.get("pay_time", int(time.time()))
        
        if not order_id:
            return {"code": 1, "msg": "缺少订单号"}
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE payments SET status = 'paid', paid_at = ?, metadata = ? WHERE order_id = ? AND status = 'pending'",
            (pay_time, json.dumps(body), order_id)
        )
        conn.commit()
        conn.close()
        
        print(f"[支付回调] ✅ 订单 {order_id} 已标记为已支付")
        return {"code": 0, "msg": "success"}
        
    except Exception as e:
        print(f"[支付回调] ❌ 处理失败: {e}")
        return {"code": 1, "msg": str(e)}

# ==================== 数据质量监控API ====================

@app.get("/api/data-quality/invalid-answers")
async def get_invalid_answers(limit: int = 100):
    """查询最近的非法答案记录（数据质量监控）"""
    conn, cursor = db_execute(
        "SELECT id, q_index, q_text, original_value, corrected_value, user_type, created_at FROM invalid_answer_records ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "q_index": r[1], "q_text": r[2],
            "original_value": r[3], "corrected_value": r[4],
            "user_type": r[5], "created_at": r[6]
        }
        for r in rows
    ]

# ==================== 健康检查API ====================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "has_api_key": bool(ZHIPU_API_KEY or ARK_API_KEY or DEEPSEEK_API_KEY or OPENAI_API_KEY)
    }

@app.get("/")
async def root():
    """返回HTML页面"""
    html_path = Path(__file__).parent / "career-planner.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return {"message": "career-planner.html not found"}

@app.get("/vip-admin")
async def vip_admin():
    """返回VIP管理页面"""
    print("Serving vip-admin.html...")
    html_path = Path(__file__).parent / "vip-admin.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return {"message": "vip-admin.html not found"}

@app.get("/api/version")
async def version():
    return {"version": "2026-05-01-vip-fix", "has_vip_admin": True}

if __name__ == "__main__":
    import uvicorn
    
    # 检查可用的API
    available_apis = []
    if ZHIPU_API_KEY:
        available_apis.append("智谱AI")
    if ARK_API_KEY:
        available_apis.append("豆包")
    if DEEPSEEK_API_KEY:
        available_apis.append("DeepSeek")
    if OPENAI_API_KEY:
        available_apis.append("OpenAI")
    
    print(f"\n{'='*50}")
    print(f"Career Planner - AI Career Planning Service")
    print(f"{'='*50}")
    port = int(os.getenv("PORT", "8000"))
    print(f"Server starting on port {port}...")
    print(f"AI API: {('/'.join(available_apis)) if available_apis else 'Not configured'}")
    print(f"Industry DB: Loaded ({len(INDUSTRY_DATABASE)} industries)")
    print(f"{'='*50}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


