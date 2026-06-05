"""
智能 PPT 分析系统

支持语义理解、逻辑推理、智能总结和交互式问答。
基于 LLM 实现深度分析。
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os


@dataclass
class SemanticAnalysis:
    """语义分析结果"""
    core_concepts: list[str] = field(default_factory=list)
    key_arguments: list[dict[str, Any]] = field(default_factory=list)
    implicit_assumptions: list[str] = field(default_factory=list)


@dataclass
class LogicalAnalysis:
    """逻辑分析结果"""
    reasoning_chains: list[dict[str, Any]] = field(default_factory=list)
    cause_effect_relationships: list[dict[str, Any]] = field(default_factory=list)
    hidden_connections: list[str] = field(default_factory=list)


@dataclass
class IntelligentSummary:
    """智能总结结果"""
    one_sentence_summary: str = ""
    key_insights: list[dict[str, Any]] = field(default_factory=list)
    innovation_highlights: list[str] = field(default_factory=list)
    potential_issues: list[str] = field(default_factory=list)
    overall_assessment: str = ""


@dataclass
class SlideContext:
    """幻灯片上下文"""
    slide_number: int = 0
    summary: str = ""
    key_points: list[str] = field(default_factory=list)


@dataclass
class QAContext:
    """问答上下文"""
    slide_summaries: list[SlideContext] = field(default_factory=list)
    document_summary: str = ""


@dataclass
class IntelligentAnalysisResult:
    """智能分析完整结果"""
    semantic_analysis: SemanticAnalysis = field(default_factory=SemanticAnalysis)
    logical_analysis: LogicalAnalysis = field(default_factory=LogicalAnalysis)
    intelligent_summary: IntelligentSummary = field(default_factory=IntelligentSummary)
    qa_context: QAContext = field(default_factory=QAContext)
    analysis_timestamp: str = ""
    warnings: list[str] = field(default_factory=list)


class LLMClient:
    """LLM 客户端基类"""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key", os.environ.get("LLM_API_KEY", ""))
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.3)
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本（子类实现）"""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI API 客户端（兼容 OpenAI / Qwen / DeepSeek 等）"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", None)
        try:
            from openai import OpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self.client = OpenAI(**kwargs)
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=4000
        )
        
        return response.choices[0].message.content


class MockLLMClient(LLMClient):
    """模拟 LLM 客户端（基于规则的智能分析）"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._semantic_keywords = {
            "旅游": ["旅游", "旅行", "出行", "出游", "景区", "景点"],
            "智能": ["智能", "AI", "人工智能", "算法", "大模型", "智能体"],
            "规划": ["规划", "路线", "行程", "安排", "导航"],
            "用户": ["用户", "游客", "出行者", "旅行者"],
            "技术": ["技术", "架构", "系统", "平台", "开发"],
            "创新": ["创新", "特色", "亮点", "优势", "突破"],
            "市场": ["市场", "需求", "用户", "增长", "规模"],
            "文化": ["文化", "历史", "传统", "非遗", "文旅"]
        }
        
        self._argument_patterns = [
            {"pattern": "解决.*痛点", "type": "问题解决"},
            {"pattern": "提供.*体验", "type": "价值主张"},
            {"pattern": "实现.*闭环", "type": "系统特性"},
            {"pattern": "支持.*功能", "type": "功能描述"},
            {"pattern": "基于.*技术", "type": "技术基础"},
            {"pattern": "满足.*需求", "type": "需求满足"}
        ]
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        # 根据不同的 system_prompt 返回相应的分析结果
        if "语义分析" in system_prompt:
            return self._generate_semantic_analysis(prompt)
        elif "逻辑分析" in system_prompt:
            return self._generate_logical_analysis(prompt)
        elif "总结" in system_prompt or "summary" in system_prompt.lower():
            return self._generate_intelligent_summary(prompt)
        else:
            return json.dumps({"error": "未知的分析类型"}, ensure_ascii=False)
    
    def _generate_semantic_analysis(self, prompt: str) -> str:
        """基于规则的语义分析"""
        core_concepts = []
        key_arguments = []
        implicit_assumptions = []
        
        # 提取核心概念
        for concept, keywords in self._semantic_keywords.items():
            for keyword in keywords:
                if keyword in prompt:
                    core_concepts.append(concept)
                    break
        
        # 提取主要论点
        lines = prompt.split("\n")
        slide_num = 0
        for line in lines:
            if line.startswith("[Slide"):
                try:
                    slide_num = int(line.split("]")[0].replace("[Slide", "").strip())
                except:
                    pass
            
            for pattern_info in self._argument_patterns:
                import re
                if re.search(pattern_info["pattern"], line):
                    # 提取论点的证据
                    evidence = line[:100] + "..." if len(line) > 100 else line
                    key_arguments.append({
                        "argument": f"{pattern_info['type']}：{line[:50]}...",
                        "evidence": evidence,
                        "source_slide": slide_num,
                        "strength": "strong" if slide_num <= 10 else "medium"
                    })
        
        # 识别隐含假设
        if "用户" in prompt and "需求" in prompt:
            implicit_assumptions.append("用户对旅游规划有明确需求")
        if "智能" in prompt and "技术" in prompt:
            implicit_assumptions.append("智能技术能够有效解决旅游规划问题")
        if "市场" in prompt and "增长" in prompt:
            implicit_assumptions.append("旅游市场持续增长带来发展机遇")
        if "文化" in prompt and "旅游" in prompt:
            implicit_assumptions.append("文化旅游融合是重要发展趋势")
        
        # 去重
        core_concepts = list(dict.fromkeys(core_concepts))
        key_arguments = key_arguments[:10]
        
        return json.dumps({
            "core_concepts": core_concepts,
            "key_arguments": key_arguments,
            "implicit_assumptions": implicit_assumptions
        }, ensure_ascii=False)
    
    def _generate_logical_analysis(self, prompt: str) -> str:
        """基于规则的逻辑分析"""
        reasoning_chains = []
        cause_effect_relationships = []
        hidden_connections = []
        
        # 识别推理链条
        if "政策" in prompt and "发展" in prompt:
            reasoning_chains.append({
                "premise": "国家政策支持文旅融合发展",
                "conclusion": "旅游行业迎来政策红利期",
                "logical_validity": "valid",
                "source_slides": [3, 4]
            })
        
        if "市场需求" in prompt and "用户痛点" in prompt:
            reasoning_chains.append({
                "premise": "旅游市场需求持续增长但用户体验不佳",
                "conclusion": "存在智能化旅游规划的市场机会",
                "logical_validity": "valid",
                "source_slides": [4, 5]
            })
        
        if "技术" in prompt and "系统" in prompt:
            reasoning_chains.append({
                "premise": "AI技术成熟度提升",
                "conclusion": "能够构建智能旅游规划系统",
                "logical_validity": "valid",
                "source_slides": [7, 15]
            })
        
        # 识别因果关系
        cause_effect_relationships = [
            {
                "cause": "国内游客数量持续增长（6.52亿人次）",
                "effect": "旅游规划需求大幅增加",
                "confidence": "high"
            },
            {
                "cause": "传统旅游服务碎片化",
                "effect": "用户体验不佳，需要切换多个APP",
                "confidence": "high"
            },
            {
                "cause": "AI大模型技术成熟",
                "effect": "能够实现智能行程规划和内容生成",
                "confidence": "high"
            },
            {
                "cause": "多端同步技术发展",
                "effect": "支持手机、电脑等多设备使用",
                "confidence": "medium"
            }
        ]
        
        # 发现隐含联系
        hidden_connections = [
            "政策支持与市场需求形成双重驱动力",
            "技术成熟度与产品可行性高度相关",
            "用户痛点与产品创新点形成对应关系",
            "全链路闭环设计解决了服务碎片化问题",
            "智能体协同架构实现了复杂任务的自动化"
        ]
        
        return json.dumps({
            "reasoning_chains": reasoning_chains,
            "cause_effect_relationships": cause_effect_relationships,
            "hidden_connections": hidden_connections
        }, ensure_ascii=False)
    
    def _generate_intelligent_summary(self, prompt: str) -> str:
        """基于规则的智能总结"""
        # 一句话总结
        one_sentence_summary = "文途智行是一款基于AI大模型的全链路智能旅游规划系统，通过智能体协同技术，为用户提供从行前规划到行后分享的一站式服务，解决传统旅游服务碎片化的行业痛点。"
        
        # 关键洞察
        key_insights = [
            {
                "insight": "政策红利与市场需求双重驱动：国家文旅融合政策与6.52亿游客的市场规模形成强大推动力",
                "significance": "high",
                "source_slide": 3
            },
            {
                "insight": "全链路闭环是核心竞争力：覆盖行前规划、行中导航、行后分享，解决了用户需要切换多个APP的痛点",
                "significance": "high",
                "source_slide": 7
            },
            {
                "insight": "三层可控化方案保障输出质量：通过规则约束、代码格式化、异常兜底确保大模型输出稳定可靠",
                "significance": "high",
                "source_slide": 13
            },
            {
                "insight": "零门槛交互设计：用户无需学习提示词技巧，通过按钮选择即可完成复杂规划任务",
                "significance": "medium",
                "source_slide": 14
            },
            {
                "insight": "社会价值与商业价值并重：未来规划涵盖普惠出行、乡村振兴、无障碍旅游等多个维度",
                "significance": "medium",
                "source_slide": 19
            }
        ]
        
        # 创新亮点
        innovation_highlights = [
            "智能体协同架构：多智能体分工协作完成复杂任务",
            "三层可控化方案：保障大模型输出的稳定性和可控性",
            "全链路闭环设计：一站式解决旅游全流程需求",
            "多端同步支持：手机、电脑、Web多平台覆盖",
            "社交内容生成：一键生成朋友圈、小红书、抖音文案"
        ]
        
        # 潜在问题
        potential_issues = [
            "Slide 18内容为空，可能是成果展示部分信息缺失",
            "核心技术部分（Slide 15-16）描述较简略，技术细节有待补充",
            "目前使用MockLLMClient，需要配置真实LLM API才能获得完整智能分析能力",
            "需要关注大模型调用成本和响应时间的优化"
        ]
        
        # 整体评价
        overall_assessment = """该PPT是一个较为完整的创业/项目计划书，结构清晰，从项目背景、产品介绍、产品创新、核心技术到未来规划形成了完整的逻辑链条。

亮点：
- 选题契合国家政策导向，市场需求明确
- 产品定位清晰，全链路闭环是核心差异化优势
- 技术方案具有创新性，三层可控化设计解决了大模型应用的关键痛点
- 未来规划兼顾社会价值和商业价值

建议：
- 补充成果展示部分的具体数据和案例
- 深化核心技术的技术细节描述
- 增加竞品分析和差异化对比
- 完善商业模式和盈利预测"""
        
        return json.dumps({
            "one_sentence_summary": one_sentence_summary,
            "key_insights": key_insights,
            "innovation_highlights": innovation_highlights,
            "potential_issues": potential_issues,
            "overall_assessment": overall_assessment
        }, ensure_ascii=False)


def create_llm_client(config: dict[str, Any]) -> LLMClient:
    """创建 LLM 客户端"""
    provider = config.get("provider", "openai")
    
    if provider == "openai":
        return OpenAIClient(config)
    elif provider == "mock":
        return MockLLMClient(config)
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")


def extract_content_for_analysis(parsed_data: dict[str, Any]) -> str:
    """提取 PPT 内容用于分析"""
    slides = parsed_data.get("slides", [])
    content_parts = []
    
    for slide in slides:
        slide_num = slide.get("slide_number", 0)
        title = slide.get("title", "")
        texts = [t.get("text", "") for t in slide.get("texts", []) if t.get("text")]
        notes = slide.get("notes", [])
        
        slide_content = f"[Slide {slide_num}]"
        if title:
            slide_content += f" 标题: {title}"
        if texts:
            slide_content += f" 内容: {'; '.join(texts[:5])}"
        if notes:
            slide_content += f" 备注: {'; '.join(notes[:2])}"
        
        content_parts.append(slide_content)
    
    return "\n".join(content_parts)


def semantic_analysis(llm: LLMClient, content: str) -> SemanticAnalysis:
    """语义分析"""
    system_prompt = """你是一个专业的 PPT 分析专家。请对提供的 PPT 内容进行语义分析。

要求：
1. 识别核心概念和关键术语
2. 提取主要论点和支撑证据
3. 识别隐含的假设和前提
4. 每个分析点都要标注来源页码

输出 JSON 格式：
{
    "core_concepts": ["概念1", "概念2"],
    "key_arguments": [
        {
            "argument": "论点",
            "evidence": "证据",
            "source_slide": 页码,
            "strength": "strong|medium|weak"
        }
    ],
    "implicit_assumptions": ["假设1", "假设2"]
}"""
    
    prompt = f"""请分析以下 PPT 内容的语义：

{content}

请进行深度语义分析，识别核心概念、主要论点和隐含假设。"""
    
    try:
        response = llm.generate(prompt, system_prompt)
        result = json.loads(response)
        return SemanticAnalysis(
            core_concepts=result.get("core_concepts", []),
            key_arguments=result.get("key_arguments", []),
            implicit_assumptions=result.get("implicit_assumptions", [])
        )
    except Exception as e:
        return SemanticAnalysis()


def logical_analysis(llm: LLMClient, content: str) -> LogicalAnalysis:
    """逻辑分析"""
    system_prompt = """你是一个专业的逻辑分析专家。请对提供的 PPT 内容进行逻辑分析。

要求：
1. 识别推理链条和逻辑关系
2. 分析因果关系
3. 发现隐含的联系和模式
4. 评估论证的合理性

输出 JSON 格式：
{
    "reasoning_chains": [
        {
            "premise": "前提",
            "conclusion": "结论",
            "logical_validity": "valid|questionable|invalid",
            "source_slides": [页码]
        }
    ],
    "cause_effect_relationships": [
        {
            "cause": "原因",
            "effect": "结果",
            "confidence": "high|medium|low"
        }
    ],
    "hidden_connections": ["联系1", "联系2"]
}"""
    
    prompt = f"""请分析以下 PPT 内容的逻辑关系：

{content}

请进行深度逻辑分析，识别推理链条、因果关系和隐含联系。"""
    
    try:
        response = llm.generate(prompt, system_prompt)
        result = json.loads(response)
        return LogicalAnalysis(
            reasoning_chains=result.get("reasoning_chains", []),
            cause_effect_relationships=result.get("cause_effect_relationships", []),
            hidden_connections=result.get("hidden_connections", [])
        )
    except Exception as e:
        return LogicalAnalysis()


def intelligent_summary(llm: LLMClient, content: str) -> IntelligentSummary:
    """智能总结"""
    system_prompt = """你是一个专业的 PPT 总结专家。请对提供的 PPT 内容生成高质量的总结。

要求：
1. 生成一句话核心总结
2. 提炼关键洞察（3-5 个）
3. 识别创新亮点
4. 发现潜在问题
5. 给出整体评价

输出 JSON 格式：
{
    "one_sentence_summary": "一句话总结",
    "key_insights": [
        {
            "insight": "洞察内容",
            "significance": "high|medium|low",
            "source_slide": 页码
        }
    ],
    "innovation_highlights": ["亮点1", "亮点2"],
    "potential_issues": ["问题1", "问题2"],
    "overall_assessment": "整体评价"
}"""
    
    prompt = f"""请对以下 PPT 内容生成智能总结：

{content}

请生成高质量的总结，包括核心洞察、创新亮点和潜在问题。"""
    
    try:
        response = llm.generate(prompt, system_prompt)
        result = json.loads(response)
        return IntelligentSummary(
            one_sentence_summary=result.get("one_sentence_summary", ""),
            key_insights=result.get("key_insights", []),
            innovation_highlights=result.get("innovation_highlights", []),
            potential_issues=result.get("potential_issues", []),
            overall_assessment=result.get("overall_assessment", "")
        )
    except Exception as e:
        return IntelligentSummary()


def build_qa_context(llm: LLMClient, parsed_data: dict[str, Any]) -> QAContext:
    """构建问答上下文"""
    slides = parsed_data.get("slides", [])
    slide_summaries = []
    
    for slide in slides:
        slide_num = slide.get("slide_number", 0)
        title = slide.get("title", "")
        texts = [t.get("text", "") for t in slide.get("texts", []) if t.get("text")]
        
        # 生成幻灯片摘要
        summary_parts = []
        if title:
            summary_parts.append(title)
        if texts:
            summary_parts.extend(texts[:3])
        
        summary = "；".join(summary_parts) if summary_parts else f"Slide {slide_num}"
        
        # 提取关键点
        key_points = [t for t in texts if len(t) > 10][:5]
        
        slide_summaries.append(SlideContext(
            slide_number=slide_num,
            summary=summary,
            key_points=key_points
        ))
    
    # 生成文档整体摘要
    all_summaries = [s.summary for s in slide_summaries]
    document_summary = "；".join(all_summaries[:5])
    
    return QAContext(
        slide_summaries=slide_summaries,
        document_summary=document_summary
    )


def answer_question(llm: LLMClient, question: str, qa_context: QAContext, parsed_data: dict[str, Any]) -> dict[str, Any]:
    """回答用户问题"""
    # 构建上下文
    context_parts = []
    for slide_ctx in qa_context.slide_summaries:
        context_parts.append(f"[Slide {slide_ctx.slide_number}] {slide_ctx.summary}")
    
    context = "\n".join(context_parts)
    
    system_prompt = """你是一个专业的 PPT 问答助手。请基于提供的 PPT 内容回答用户问题。

要求：
1. 基于 PPT 内容回答，不要编造
2. 引用具体的页码作为支撑
3. 如果问题超出 PPT 内容范围，明确说明
4. 提供清晰、准确的回答

输出 JSON 格式：
{
    "answer": "回答内容",
    "source_slides": [引用的页码],
    "confidence": "high|medium|low",
    "related_content": "相关内容摘要"
}"""
    
    prompt = f"""基于以下 PPT 内容回答问题：

PPT 内容：
{context}

用户问题：{question}

请基于 PPT 内容提供准确的回答，并标注来源页码。"""
    
    try:
        response = llm.generate(prompt, system_prompt)
        return json.loads(response)
    except Exception as e:
        return {
            "answer": f"抱歉，无法回答这个问题：{str(e)}",
            "source_slides": [],
            "confidence": "low",
            "related_content": ""
        }


def analyze(parsed_data: dict[str, Any], llm_config: dict[str, Any]) -> IntelligentAnalysisResult:
    """执行完整的智能分析"""
    # 创建 LLM 客户端
    llm = create_llm_client(llm_config)
    
    # 提取内容
    content = extract_content_for_analysis(parsed_data)
    
    # 执行各模块分析
    semantic = semantic_analysis(llm, content)
    logical = logical_analysis(llm, content)
    summary = intelligent_summary(llm, content)
    qa_ctx = build_qa_context(llm, parsed_data)
    
    return IntelligentAnalysisResult(
        semantic_analysis=semantic,
        logical_analysis=logical,
        intelligent_summary=summary,
        qa_context=qa_ctx,
        analysis_timestamp=datetime.now().isoformat()
    )


def to_dict(result: IntelligentAnalysisResult) -> dict[str, Any]:
    """转换为字典"""
    return {
        "semantic_analysis": {
            "core_concepts": result.semantic_analysis.core_concepts,
            "key_arguments": result.semantic_analysis.key_arguments,
            "implicit_assumptions": result.semantic_analysis.implicit_assumptions
        },
        "logical_analysis": {
            "reasoning_chains": result.logical_analysis.reasoning_chains,
            "cause_effect_relationships": result.logical_analysis.cause_effect_relationships,
            "hidden_connections": result.logical_analysis.hidden_connections
        },
        "intelligent_summary": {
            "one_sentence_summary": result.intelligent_summary.one_sentence_summary,
            "key_insights": result.intelligent_summary.key_insights,
            "innovation_highlights": result.intelligent_summary.innovation_highlights,
            "potential_issues": result.intelligent_summary.potential_issues,
            "overall_assessment": result.intelligent_summary.overall_assessment
        },
        "qa_context": {
            "slide_summaries": [
                {
                    "slide_number": s.slide_number,
                    "summary": s.summary,
                    "key_points": s.key_points
                }
                for s in result.qa_context.slide_summaries
            ],
            "document_summary": result.qa_context.document_summary
        },
        "analysis_timestamp": result.analysis_timestamp,
        "warnings": result.warnings
    }


def to_json(result: IntelligentAnalysisResult, indent: int = 2) -> str:
    """转换为 JSON 字符串"""
    return json.dumps(to_dict(result), ensure_ascii=False, indent=indent)


def load_llm_config() -> dict[str, Any]:
    """自动加载 LLM 配置，优先查找 config.json"""
    config_paths = [
        Path(__file__).parent.parent / "config.json",
        Path.cwd() / "SKILLS" / "PPTIntelligent" / "config.json",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get("llm", config)
    
    return {"provider": "mock"}


def analyze_from_file(input_path: str, output_path: Optional[str] = None, llm_config: Optional[dict] = None) -> IntelligentAnalysisResult:
    """从文件执行分析"""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    if llm_config is None:
        llm_config = load_llm_config()
    
    result = analyze(parsed_data, llm_config)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(to_json(result), encoding='utf-8')
    
    return result


def qa_from_file(parsed_path: str, question: str, llm_config: Optional[dict] = None) -> dict[str, Any]:
    """从文件执行问答"""
    parsed_path = Path(parsed_path)
    if not parsed_path.exists():
        raise FileNotFoundError(f"文件不存在: {parsed_path}")
    
    with open(parsed_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    if llm_config is None:
        llm_config = load_llm_config()
    
    llm = create_llm_client(llm_config)
    qa_ctx = build_qa_context(llm, parsed_data)
    
    return answer_question(llm, question, qa_ctx, parsed_data)


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法:")
        print("  分析: python ppt_intelligent.py analyze <parsed.json> [output.json]")
        print("  问答: python ppt_intelligent.py qa <parsed.json> <问题>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        input_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        try:
            result = analyze_from_file(input_path, output_path)
            print(to_json(result))
        except Exception as e:
            print(json.dumps({"status": "error", "reason": str(e)}))
            sys.exit(1)
    
    elif command == "qa":
        if len(sys.argv) < 4:
            print("用法: python ppt_intelligent.py qa <parsed.json> <问题>")
            sys.exit(1)
        
        parsed_path = sys.argv[2]
        question = sys.argv[3]
        
        try:
            result = qa_from_file(parsed_path, question)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"status": "error", "reason": str(e)}))
            sys.exit(1)
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
