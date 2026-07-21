#!/usr/bin/env python3
"""
Knowledge Base Manager — 增量知识库管理（v2 多源版）

支持五种模式：
  init       — 首次全量构建知识库
  update     — 增量更新（检测新增/变更/删除的文档）
  register   — 跨 Agent 注册（任意 Agent 输出元数据注册到知识库）
  status     — 显示当前知识库状态和差异预览
  query      — 查询知识库（关键词/实体/文档）
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────

def _ts() -> str:
    """ISO 8601 时间戳（含时区）"""
    return datetime.now(timezone.utc).isoformat()


def _hash_file(path: Path) -> str:
    """计算文件的 SHA256 哈希"""
    if not path.exists():
        return ""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _hash_content(content: dict) -> str:
    """对 content.json 内容计算稳定哈希（按 key 排序）"""
    raw = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict:
    """安全加载 JSON，不存在返回 {}"""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    """保存 JSON，使用 indent=2, ensure_ascii=False"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────
# 实体/关系提取（从 content.json）
# ─────────────────────────────────────────────────────────────

# 中文人名常见姓氏（前 100 高频）
_COMMON_SURNAMES = set(
    "王李张刘陈杨黄赵周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅"
    "沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白"
    "崔康毛邱秦江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文庞樊兰殷施陶洪翟安颜"
    "倪严牛温芦季俞鲁葛伍韦申尤毕聂丛焦向柳邢骆"
)

# 学术术语模式
_TERM_PATTERNS = [
    re.compile(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+"),              # 英文术语: Historical Materialism
    re.compile(r"[\u4e00-\u9fff]{2,6}(?:观|论|说|学|主义|思想|理论|方法|原则|范畴|概念)"),  # 中文术语
    re.compile(r"《[^》]{2,20}》"),                                # 书名号: 《资本论》
]


def _extract_entities_from_paragraphs(paragraphs: list) -> dict:
    """从段落文本中提取实体（人名、术语、书名）"""
    entities = {"persons": [], "terms": [], "works": []}
    person_count = {}
    term_count = {}
    work_count = {}

    for para in paragraphs:
        text = para.get("text", "")
        if not text:
            continue

        # 提取人名（中文：姓 + 1-2 字名）
        for i, ch in enumerate(text):
            if ch in _COMMON_SURNAMES and i + 1 < len(text):
                # 检查后续 1-2 个字符是否像名字
                for name_len in [2, 3]:
                    candidate = text[i:i + name_len]
                    if len(candidate) >= 2 and all(
                        "\u4e00" <= c <= "\u9fff" for c in candidate[1:]
                    ):
                        # 排除常见非人名词组
                        if not any(kw in candidate for kw in ["中国", "人民", "社会", "国家", "历史", "哲学", "科学"]):
                            person_count[candidate] = person_count.get(candidate, 0) + 1

        # 提取术语
        for pattern in _TERM_PATTERNS:
            for match in pattern.finditer(text):
                term = match.group().strip()
                if 2 <= len(term) <= 20:
                    term_count[term] = term_count.get(term, 0) + 1

        # 提取书名号内容
        for match in re.finditer(r"《([^》]+)》", text):
            work = match.group(1)
            if 2 <= len(work) <= 20:
                work_count[work] = work_count.get(work, 0) + 1

    # 过滤低频实体
    entities["persons"] = [
        {"name": name, "count": count}
        for name, count in sorted(person_count.items(), key=lambda x: -x[1])
        if count >= 2
    ][:30]

    entities["terms"] = [
        {"name": term, "count": count}
        for term, count in sorted(term_count.items(), key=lambda x: -x[1])
        if count >= 2
    ][:50]

    entities["works"] = [
        {"name": work, "count": count}
        for work, count in sorted(work_count.items(), key=lambda x: -x[1])
        if count >= 1
    ][:30]

    return entities


def _extract_entities_from_summary(summary: dict) -> dict:
    """从 summary.json 提取实体"""
    # 优先使用段落级提取
    paragraphs = summary.get("paragraphs", [])
    if paragraphs:
        return _extract_entities_from_paragraphs(paragraphs)

    # 回退：从文本内容提取
    text = summary.get("content", "") or summary.get("text", "")
    if text:
        return _extract_entities_from_paragraphs([{"text": text}])

    return {"persons": [], "terms": [], "works": []}


def _build_entity_index(existing_index: dict, new_entries: list, removed_ids: set) -> dict:
    """增量合并实体索引"""
    entities_map = {}

    # 保留未删除文档的实体
    for entity_type in ["persons", "terms", "works"]:
        for entry in existing_index.get(entity_type, []):
            name = entry["name"]
            docs = [d for d in entry.get("documents", []) if d.get("id") not in removed_ids]
            if docs:
                key = f"{entity_type}:{name}"
                entities_map[key] = {
                    "name": name,
                    "type": entity_type,
                    "total_count": sum(d.get("count", 0) for d in docs),
                    "document_count": len(docs),
                    "documents": docs,
                }

    # 合并新文档的实体
    for item in new_entries:
        doc_id = item["id"]
        entities = item.get("entities", {})
        for entity_type in ["persons", "terms", "works"]:
            for entry in entities.get(entity_type, []):
                name = entry["name"]
                count = entry.get("count", 1)
                key = f"{entity_type}:{name}"
                if key not in entities_map:
                    entities_map[key] = {
                        "name": name,
                        "type": entity_type,
                        "total_count": 0,
                        "document_count": 0,
                        "documents": [],
                    }
                e = entities_map[key]
                e["total_count"] += count
                e["document_count"] += 1
                e["documents"].append({"id": doc_id, "count": count})

    # 按类型分组输出
    result = {"persons": [], "terms": [], "works": []}
    for key, data in sorted(entities_map.items(), key=lambda x: -x[1]["total_count"]):
        etype = data["type"]
        result[etype].append({
            "name": data["name"],
            "total_count": data["total_count"],
            "document_count": data["document_count"],
            "documents": data["documents"],
        })

    return {
        "generated_at": _ts(),
        "total_persons": len(result["persons"]),
        "total_terms": len(result["terms"]),
        "total_works": len(result["works"]),
        "persons": result["persons"],
        "terms": result["terms"],
        "works": result["works"],
    }


def _build_relation_index(existing_index: dict, new_entries: list, removed_ids: set) -> dict:
    """构建/增量合并关系索引（共同引用、术语重叠）"""
    relations_map = {}

    # 保留未删除的关系
    for rel in existing_index.get("relations", []):
        key = f"{rel['source']}::{rel['target']}::{rel['type']}"
        if rel["source"] not in removed_ids and rel["target"] not in removed_ids:
            relations_map[key] = rel

    # 从新文档对中计算关系
    all_docs = {}
    for item in new_entries:
        all_docs[item["id"]] = item.get("entities", {})

    # 也加载未变更文档的实体
    for doc_path in existing_index.get("_doc_entities", {}):
        pass  # 由调用方提供

    doc_ids = list(all_docs.keys())
    for i in range(len(doc_ids)):
        for j in range(i + 1, len(doc_ids)):
            id_a, id_b = doc_ids[i], doc_ids[j]
            ent_a = all_docs[id_a]
            ent_b = all_docs[id_b]

            # 计算共享术语
            terms_a = {e["name"] for e in ent_a.get("terms", [])}
            terms_b = {e["name"] for e in ent_b.get("terms", [])}
            shared_terms = terms_a & terms_b

            if shared_terms:
                key = f"{id_a}::{id_b}::shared_terms"
                relations_map[key] = {
                    "source": id_a,
                    "target": id_b,
                    "type": "shared_terms",
                    "weight": len(shared_terms),
                    "details": list(shared_terms)[:10],
                }

            # 计算共享书名引用
            works_a = {e["name"] for e in ent_a.get("works", [])}
            works_b = {e["name"] for e in ent_b.get("works", [])}
            shared_works = works_a & works_b

            if shared_works:
                key = f"{id_a}::{id_b}::shared_works"
                relations_map[key] = {
                    "source": id_a,
                    "target": id_b,
                    "type": "shared_works",
                    "weight": len(shared_works),
                    "details": list(shared_works)[:10],
                }

    relations_list = sorted(relations_map.values(), key=lambda x: -x.get("weight", 0))

    return {
        "generated_at": _ts(),
        "total_relations": len(relations_list),
        "relations": relations_list,
    }


# ─────────────────────────────────────────────────────────────
# .kb_state.json 结构
# ─────────────────────────────────────────────────────────────

def _init_state(kb_dir: Path) -> dict:
    """初始化知识库状态文件"""
    return {
        "version": 1,
        "created_at": _ts(),
        "updated_at": _ts(),
        "document_count": 0,
        "keyword_count": 0,
        "concept_count": 0,
        "entity_count": 0,
        "relation_count": 0,
        "sources": {},           # agent_name → {manifest_path, last_update, doc_count}
        "documents": {},         # id → {source_file, source_agent, content_hash, added_at, updated_at}
        "change_log": [],
    }


# ─────────────────────────────────────────────────────────────
# 文档差异检测
# ─────────────────────────────────────────────────────────────

def _diff_documents(
    manifest_docs: list,
    state: dict,
    summary_dir: Path,
) -> dict:
    """
    对比 manifest 中的文档与 state 中已记录的文档，
    返回 {new, changed, unchanged, removed}
    """
    state_docs = state.get("documents", {})

    current_ids = {}
    for doc in manifest_docs:
        if doc.get("status") != "success":
            continue
        source = doc.get("source_file", "")
        summary_json = doc.get("summary_json", "")
        if not summary_json:
            continue

        sum_path = Path(summary_json)
        if not sum_path.is_absolute():
            sum_path = summary_dir / summary_json
        sum_data = _load_json(sum_path)
        content_hash = _hash_content(sum_data)

        doc_id = sum_data.get("id", _make_doc_id(source))
        current_ids[doc_id] = {
            "source_file": source,
            "content_hash": content_hash,
        }

    new = {}
    changed = {}
    unchanged = {}
    removed = {}

    for doc_id in state_docs:
        if doc_id not in current_ids:
            removed[doc_id] = state_docs[doc_id]

    for doc_id, info in current_ids.items():
        if doc_id not in state_docs:
            new[doc_id] = info
        elif state_docs[doc_id].get("content_hash") != info["content_hash"]:
            changed[doc_id] = {**info, "old_hash": state_docs[doc_id].get("content_hash")}
        else:
            unchanged[doc_id] = info

    return {"new": new, "changed": changed, "unchanged": unchanged, "removed": removed}


def _make_doc_id(source_file: str) -> str:
    """从文件名生成文档 ID"""
    stem = Path(source_file).stem
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in stem)
    return f"doc_{safe}"


# ─────────────────────────────────────────────────────────────
# 关键词/概念索引合并（保留 v1 逻辑）
# ─────────────────────────────────────────────────────────────

def _merge_keywords(existing_index: dict, new_summaries: list, removed_ids: set):
    """增量合并关键词索引"""
    keywords_map = {}
    for kw_entry in existing_index.get("keywords", []):
        kw_name = kw_entry["keyword"]
        docs = [d for d in kw_entry.get("documents", []) if d.get("id") not in removed_ids]
        if docs:
            keywords_map[kw_name] = {
                "total_frequency": sum(d.get("frequency", 0) for d in docs),
                "document_count": len(docs),
                "documents": docs,
            }
    for item in new_summaries:
        doc_id = item["id"]
        summary = item.get("summary", {})
        for kw_entry in summary.get("keywords", []):
            kw_name = kw_entry["keyword"]
            freq = kw_entry.get("frequency", 0)
            relevance = kw_entry.get("relevance", 0)
            if kw_name not in keywords_map:
                keywords_map[kw_name] = {"total_frequency": 0, "document_count": 0, "documents": []}
            km = keywords_map[kw_name]
            km["total_frequency"] += freq
            km["document_count"] += 1
            km["documents"].append({"id": doc_id, "frequency": freq, "relevance": relevance})
    keywords_list = [
        {"keyword": kw_name, **data, "detail_link": f"keywords/{kw_name}.json"}
        for kw_name, data in sorted(keywords_map.items(), key=lambda x: -x[1]["total_frequency"])
    ]
    return {"generated_at": _ts(), "total_keywords": len(keywords_list), "keywords": keywords_list}


def _merge_concepts(existing_index: dict, new_summaries: list, removed_ids: set):
    """增量合并概念索引"""
    concepts_map = {}
    for c_entry in existing_index.get("concepts", []):
        c_name = c_entry["concept"]
        docs = [d for d in c_entry.get("documents", []) if d not in removed_ids]
        if docs:
            concepts_map[c_name] = {
                "definition": c_entry.get("definition", ""),
                "importance": c_entry.get("importance", 0),
                "document_count": len(docs),
                "documents": docs,
            }
    for item in new_summaries:
        doc_id = item["id"]
        summary = item.get("summary", {})
        for c_entry in summary.get("concepts", []):
            c_name = c_entry.get("concept", c_entry.get("name", ""))
            if not c_name:
                continue
            if c_name not in concepts_map:
                concepts_map[c_name] = {"definition": "", "importance": 0, "document_count": 0, "documents": []}
            cm = concepts_map[c_name]
            cm["definition"] = c_entry.get("definition", cm["definition"])
            cm["importance"] = max(cm["importance"], c_entry.get("importance", 0))
            cm["document_count"] += 1
            if doc_id not in cm["documents"]:
                cm["documents"].append(doc_id)
    concepts_list = [
        {"concept": c_name, **data, "detail_link": f"concepts/{c_name}.json"}
        for c_name, data in sorted(concepts_map.items(), key=lambda x: -x[1]["importance"])
    ]
    return {"generated_at": _ts(), "total_concepts": len(concepts_list), "concepts": concepts_list}


def _merge_toc(existing_toc: dict, new_summaries: list, removed_ids: set):
    """增量合并目录结构"""
    existing_entries = {e.get("id"): e for e in existing_toc.get("toc", [])}
    for rid in removed_ids:
        existing_entries.pop(rid, None)
    for item in new_summaries:
        doc_id = item["id"]
        summary = item.get("summary", {})
        existing_entries[doc_id] = {
            "id": doc_id,
            "title": summary.get("title", ""),
            "source_file": summary.get("source_file", ""),
            "source_agent": summary.get("source_agent", ""),
            "sections": summary.get("sections", []),
        }
    toc_list = list(existing_entries.values())
    return {"generated_at": _ts(), "document_count": len(toc_list), "toc": toc_list}


# ─────────────────────────────────────────────────────────────
# 主命令
# ─────────────────────────────────────────────────────────────

def cmd_init(kb_dir: Path, summary_dir: Path, manifest_path: Path, agent_name: str = "doc-content-analysis"):
    """首次全量构建知识库"""
    manifest = _load_json(manifest_path)
    if manifest.get("status") != "completed":
        print(f"[ERROR] manifest status is '{manifest.get('status')}', expected 'completed'", file=sys.stderr)
        sys.exit(1)

    docs = manifest.get("documents", [])
    success_docs = [d for d in docs if d.get("status") == "success"]

    if not success_docs:
        print("[INFO] No successful documents to process. Creating empty knowledge base.")

    # 初始化目录
    for d in ["documents", "keywords", "concepts", "entities", "relations"]:
        (kb_dir / d).mkdir(parents=True, exist_ok=True)

    state = _init_state(kb_dir)
    state_docs = {}

    all_summaries = []
    all_entity_entries = []

    for doc in success_docs:
        sum_path = Path(doc.get("summary_json", ""))
        if not sum_path.is_absolute():
            sum_path = summary_dir / sum_path
        summary = _load_json(sum_path)
        if not summary:
            continue

        doc_id = summary.get("id", _make_doc_id(doc.get("source_file", "")))
        summary["source_agent"] = agent_name
        all_summaries.append({"id": doc_id, "doc": doc, "summary": summary})

        # 提取实体
        entities = _extract_entities_from_summary(summary)
        all_entity_entries.append({"id": doc_id, "entities": entities})

        # 写 documents/<id>.json（含实体）
        doc_index = {**summary, "entities": entities, "related_documents": []}
        _save_json(kb_dir / "documents" / f"{doc_id}.json", doc_index)

        state_docs[doc_id] = {
            "source_file": doc.get("source_file", ""),
            "source_agent": agent_name,
            "content_hash": _hash_content(summary),
            "title": summary.get("title", ""),
            "added_at": _ts(),
            "updated_at": _ts(),
        }

    # 构建索引
    kw_index = _merge_keywords({"keywords": []}, all_summaries, set())
    _save_json(kb_dir / "keywords" / "index.json", kw_index)

    c_index = _merge_concepts({"concepts": []}, all_summaries, set())
    _save_json(kb_dir / "concepts" / "index.json", c_index)

    entity_index = _build_entity_index({}, all_entity_entries, set())
    _save_json(kb_dir / "entities" / "index.json", entity_index)

    relation_index = _build_relation_index({}, all_entity_entries, set())
    _save_json(kb_dir / "relations" / "index.json", relation_index)

    toc = _merge_toc({"toc": []}, all_summaries, set())
    _save_json(kb_dir / "toc.json", toc)

    # 构建 kb-manifest.json
    kb_manifest = _build_kb_manifest(kb_dir, state_docs, kw_index, c_index, entity_index, state)
    _save_json(kb_dir / "kb-manifest.json", kb_manifest)

    # 写状态
    state["documents"] = state_docs
    state["document_count"] = len(state_docs)
    state["keyword_count"] = kw_index["total_keywords"]
    state["concept_count"] = c_index["total_concepts"]
    state["entity_count"] = entity_index["total_persons"] + entity_index["total_terms"] + entity_index["total_works"]
    state["relation_count"] = relation_index["total_relations"]
    state["sources"] = {agent_name: {"manifest_path": str(manifest_path), "last_update": _ts(), "doc_count": len(state_docs)}}
    state["updated_at"] = _ts()
    state["change_log"].append({
        "action": "init",
        "timestamp": _ts(),
        "agent": agent_name,
        "documents_added": len(state_docs),
        "message": f"首次全量构建 (agent={agent_name})",
    })
    _save_json(kb_dir / ".kb_state.json", state)

    print(f"[OK] Knowledge base initialized: {len(state_docs)} docs, {kw_index['total_keywords']} keywords, {c_index['total_concepts']} concepts, {entity_index['total_persons']} persons, {relation_index['total_relations']} relations")
    return kb_dir


def cmd_update(kb_dir: Path, summary_dir: Path, manifest_path: Path, agent_name: str = "doc-content-analysis"):
    """增量更新知识库"""
    state_path = kb_dir / ".kb_state.json"
    if not state_path.exists():
        print("[INFO] No existing .kb_state.json found. Falling back to init mode.")
        return cmd_init(kb_dir, summary_dir, manifest_path, agent_name)

    state = _load_json(state_path)
    manifest = _load_json(manifest_path)

    if manifest.get("status") != "completed":
        print(f"[ERROR] manifest status is '{manifest.get('status')}', expected 'completed'", file=sys.stderr)
        sys.exit(1)

    docs = manifest.get("documents", [])
    success_docs = [d for d in docs if d.get("status") == "success"]

    diff = _diff_documents(success_docs, state, summary_dir)
    new_count = len(diff["new"])
    changed_count = len(diff["changed"])
    removed_count = len(diff["removed"])
    unchanged_count = len(diff["unchanged"])

    if new_count == 0 and changed_count == 0 and removed_count == 0:
        print("[INFO] No changes detected. Knowledge base is up to date.")
        return kb_dir

    print(f"[INFO] Changes detected: +{new_count} new, ~{changed_count} changed, -{removed_count} removed, ={unchanged_count} unchanged")

    all_update_ids = set(diff["new"]) | set(diff["changed"])
    removed_ids = set(diff["removed"])

    new_summaries = []
    all_entity_entries = []
    state_docs = dict(state.get("documents", {}))

    for doc in success_docs:
        sum_path = Path(doc.get("summary_json", ""))
        if not sum_path.is_absolute():
            sum_path = summary_dir / sum_path
        if not sum_path.exists():
            continue
        summary = _load_json(sum_path)
        doc_id = summary.get("id", _make_doc_id(doc.get("source_file", "")))

        if doc_id in all_update_ids:
            summary["source_agent"] = agent_name
            new_summaries.append({"id": doc_id, "doc": doc, "summary": summary})

            entities = _extract_entities_from_summary(summary)
            all_entity_entries.append({"id": doc_id, "entities": entities})

            doc_index = {**summary, "entities": entities, "related_documents": _find_related(summary, state_docs, doc_id)}
            _save_json(kb_dir / "documents" / f"{doc_id}.json", doc_index)

            state_docs[doc_id] = {
                "source_file": doc.get("source_file", ""),
                "source_agent": agent_name,
                "content_hash": diff["new"].get(doc_id, diff["changed"].get(doc_id, {})).get("content_hash", ""),
                "title": summary.get("title", ""),
                "added_at": state_docs.get(doc_id, {}).get("added_at", _ts()),
                "updated_at": _ts(),
            }

    for rid in removed_ids:
        state_docs.pop(rid, None)
        doc_path = kb_dir / "documents" / f"{rid}.json"
        if doc_path.exists():
            doc_path.unlink()

    # 增量合并所有索引
    existing_kw = _load_json(kb_dir / "keywords" / "index.json")
    kw_index = _merge_keywords(existing_kw, new_summaries, removed_ids)
    _save_json(kb_dir / "keywords" / "index.json", kw_index)

    existing_c = _load_json(kb_dir / "concepts" / "index.json")
    c_index = _merge_concepts(existing_c, new_summaries, removed_ids)
    _save_json(kb_dir / "concepts" / "index.json", c_index)

    existing_entities = _load_json(kb_dir / "entities" / "index.json")
    entity_index = _build_entity_index(existing_entities, all_entity_entries, removed_ids)
    _save_json(kb_dir / "entities" / "index.json", entity_index)

    existing_relations = _load_json(kb_dir / "relations" / "index.json")
    relation_index = _build_relation_index(existing_relations, all_entity_entries, removed_ids)
    _save_json(kb_dir / "relations" / "index.json", relation_index)

    existing_toc = _load_json(kb_dir / "toc.json")
    toc = _merge_toc(existing_toc, new_summaries, removed_ids)
    _save_json(kb_dir / "toc.json", toc)

    _update_related_all(kb_dir, state_docs, new_summaries, all_update_ids)

    kb_manifest = _build_kb_manifest(kb_dir, state_docs, kw_index, c_index, entity_index, state)
    _save_json(kb_dir / "kb-manifest.json", kb_manifest)

    # 更新状态
    state["document_count"] = len(state_docs)
    state["keyword_count"] = kw_index["total_keywords"]
    state["concept_count"] = c_index["total_concepts"]
    state["entity_count"] = entity_index["total_persons"] + entity_index["total_terms"] + entity_index["total_works"]
    state["relation_count"] = relation_index["total_relations"]
    state["version"] += 1
    state["documents"] = state_docs

    # 更新 sources
    if agent_name not in state.get("sources", {}):
        state.setdefault("sources", {})[agent_name] = {}
    state["sources"][agent_name]["last_update"] = _ts()
    state["sources"][agent_name]["doc_count"] = len([d for d in state_docs.values() if d.get("source_agent") == agent_name])

    state["updated_at"] = _ts()

    parts = []
    if new_count: parts.append(f"+{new_count} added")
    if changed_count: parts.append(f"~{changed_count} updated")
    if removed_count: parts.append(f"-{removed_count} removed")

    state["change_log"].append({
        "action": "update",
        "version": state["version"],
        "timestamp": _ts(),
        "agent": agent_name,
        "new_count": new_count,
        "changed_count": changed_count,
        "removed_count": removed_count,
        "message": ", ".join(parts),
    })
    _save_json(state_path, state)

    print(f"[OK] Knowledge base updated to v{state['version']}: {', '.join(parts)}")
    return kb_dir


def cmd_register(kb_dir: Path, agent_name: str, manifest_path: Path, summary_dir: Path = None):
    """
    跨 Agent 注册：任意 Agent 将其输出元数据注册到知识库。
    不要求标准 manifest.json 格式，只需包含文档列表。
    """
    kb_dir.mkdir(parents=True, exist_ok=True)

    state_path = kb_dir / ".kb_state.json"
    if not state_path.exists():
        print("[INFO] Knowledge base not initialized. Creating new one.")

    manifest = _load_json(manifest_path)

    # 支持两种 manifest 格式：
    # 1. 标准 doc-content-analysis 格式（含 documents[].status/summary_json）
    # 2. 通用格式（直接包含文档列表）
    docs = manifest.get("documents", [])
    if not docs:
        # 通用格式：manifest 本身就是一个文档描述
        docs = [manifest] if manifest.get("title") or manifest.get("source_file") else []

    success_docs = [d for d in docs if d.get("status", "success") == "success"]
    if not success_docs:
        success_docs = docs  # 通用格式无 status 字段

    state = _load_json(state_path) if state_path.exists() else _init_state(kb_dir)

    state_docs = dict(state.get("documents", {}))
    new_count = 0

    for doc in success_docs:
        source = doc.get("source_file", doc.get("file_name", ""))
        summary_json = doc.get("summary_json", "")

        # 尝试加载 summary
        summary = {}
        if summary_json:
            sum_path = Path(summary_json)
            if summary_dir and not sum_path.is_absolute():
                sum_path = summary_dir / sum_path
            if sum_path.exists():
                summary = _load_json(sum_path)

        # 从 summary 或 doc 中构建文档条目
        doc_id = summary.get("id", _make_doc_id(source)) if summary else _make_doc_id(source)
        title = summary.get("title", doc.get("title", "")) if summary else doc.get("title", "")
        content_hash = _hash_content(summary) if summary else _hash_content(doc)

        # 跳过已存在且未变更的
        if doc_id in state_docs and state_docs[doc_id].get("content_hash") == content_hash:
            continue

        summary_data = {**summary} if summary else {**doc}
        summary_data["source_agent"] = agent_name

        # 提取实体
        entities = _extract_entities_from_summary(summary_data) if summary else {"persons": [], "terms": [], "works": []}

        # 写 documents/<id>.json
        doc_index = {**summary_data, "entities": entities, "related_documents": []}
        _save_json(kb_dir / "documents" / f"{doc_id}.json", doc_index)

        state_docs[doc_id] = {
            "source_file": source,
            "source_agent": agent_name,
            "content_hash": content_hash,
            "title": title,
            "added_at": state_docs.get(doc_id, {}).get("added_at", _ts()),
            "updated_at": _ts(),
        }
        new_count += 1

    if new_count == 0:
        print(f"[INFO] No new documents from agent '{agent_name}' to register.")
        return

    # 更新索引
    all_entity_entries = []
    for doc_id in list(state_docs.keys()):
        doc_path = kb_dir / "documents" / f"{doc_id}.json"
        if doc_path.exists():
            d = _load_json(doc_path)
            all_entity_entries.append({"id": doc_id, "entities": d.get("entities", {})})

    # 重建实体和关系索引（简化：全量重建）
    entity_index = _build_entity_index({}, all_entity_entries, set())
    _save_json(kb_dir / "entities" / "index.json", entity_index)

    relation_index = _build_relation_index({}, all_entity_entries, set())
    _save_json(kb_dir / "relations" / "index.json", relation_index)

    # 更新状态
    state["documents"] = state_docs
    state["document_count"] = len(state_docs)
    state["entity_count"] = entity_index["total_persons"] + entity_index["total_terms"] + entity_index["total_works"]
    state["relation_count"] = relation_index["total_relations"]

    if agent_name not in state.get("sources", {}):
        state.setdefault("sources", {})[agent_name] = {}
    state["sources"][agent_name]["last_update"] = _ts()
    state["sources"][agent_name]["doc_count"] = len([d for d in state_docs.values() if d.get("source_agent") == agent_name])

    state["version"] = state.get("version", 0) + 1
    state["updated_at"] = _ts()
    state["change_log"].append({
        "action": "register",
        "version": state["version"],
        "timestamp": _ts(),
        "agent": agent_name,
        "documents_added": new_count,
        "message": f"Agent '{agent_name}' registered {new_count} documents",
    })
    _save_json(state_path, state)

    # 更新 kb-manifest
    existing_kw = _load_json(kb_dir / "keywords" / "index.json")
    existing_c = _load_json(kb_dir / "concepts" / "index.json")
    kb_manifest = _build_kb_manifest(kb_dir, state_docs, existing_kw, existing_c, entity_index, state)
    _save_json(kb_dir / "kb-manifest.json", kb_manifest)

    print(f"[OK] Agent '{agent_name}' registered {new_count} documents to knowledge base (v{state['version']})")


def cmd_status(kb_dir: Path, summary_dir: Path = None, manifest_path: Path = None):
    """显示当前知识库状态"""
    state_path = kb_dir / ".kb_state.json"
    if not state_path.exists():
        print("[STATUS] Knowledge base not yet initialized. Run 'init' first.")
        return

    state = _load_json(state_path)
    print(f"Knowledge Base Status (v{state['version']})")
    print(f"  Documents:  {state['document_count']}")
    print(f"  Keywords:   {state.get('keyword_count', 0)}")
    print(f"  Concepts:   {state.get('concept_count', 0)}")
    print(f"  Entities:   {state.get('entity_count', 0)}")
    print(f"  Relations:  {state.get('relation_count', 0)}")
    print(f"  Last updated: {state.get('updated_at', 'N/A')}")
    print()

    # 显示数据来源
    sources = state.get("sources", {})
    if sources:
        print("  Data Sources:")
        for agent, info in sources.items():
            print(f"    - {agent}: {info.get('doc_count', '?')} docs (last: {info.get('last_update', 'N/A')})")
        print()

    # 如果提供了 manifest，显示差异
    if manifest_path and manifest_path.exists():
        manifest = _load_json(manifest_path)
        docs = manifest.get("documents", [])
        success_docs = [d for d in docs if d.get("status") == "success"]
        if summary_dir:
            diff = _diff_documents(success_docs, state, summary_dir)
            print("  Pending Changes:")
            print(f"    + New:      {len(diff['new'])}")
            print(f"    ~ Changed:  {len(diff['changed'])}")
            print(f"    - Removed:  {len(diff['removed'])}")
            print(f"    = Unchanged: {len(diff['unchanged'])}")

    # 最近变更日志
    log = state.get("change_log", [])
    if log:
        print(f"\n  Recent Changes (last {min(5, len(log))}):")
        for entry in log[-5:]:
            print(f"    [{entry.get('action', '?')}] {entry.get('message', '')} ({entry.get('timestamp', '')[:19]})")


def cmd_query(kb_dir: Path, query_type: str, query_text: str):
    """查询知识库"""
    if query_type == "keywords":
        index = _load_json(kb_dir / "keywords" / "index.json")
        matches = [k for k in index.get("keywords", []) if query_text.lower() in k["keyword"].lower()]
        print(f"Found {len(matches)} keyword matches:")
        for k in matches[:10]:
            print(f"  - {k['keyword']}: {k['document_count']} docs, freq={k['total_frequency']}")

    elif query_type == "entities":
        index = _load_json(kb_dir / "entities" / "index.json")
        for etype in ["persons", "terms", "works"]:
            matches = [e for e in index.get(etype, []) if query_text.lower() in e["name"].lower()]
            if matches:
                print(f"\n{etype}:")
                for e in matches[:10]:
                    print(f"  - {e['name']}: {e['document_count']} docs, count={e['total_count']}")

    elif query_type == "documents":
        state = _load_json(kb_dir / ".kb_state.json")
        matches = [
            info for doc_id, info in state.get("documents", {}).items()
            if query_text.lower() in info.get("title", "").lower() or query_text.lower() in doc_id.lower()
        ]
        print(f"Found {len(matches)} document matches:")
        for m in matches[:10]:
            print(f"  - {m.get('title', '?')} (agent={m.get('source_agent', '?')})")

    elif query_type == "relations":
        index = _load_json(kb_dir / "relations" / "index.json")
        matches = [
            r for r in index.get("relations", [])
            if query_text in r.get("source", "") or query_text in r.get("target", "")
        ]
        print(f"Found {len(matches)} relation matches:")
        for r in matches[:10]:
            print(f"  - {r['source']} ↔ {r['target']} ({r['type']}, weight={r['weight']})")


# ─────────────────────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────────────────────

def _build_kb_manifest(kb_dir, state_docs, kw_index, c_index, entity_index, state):
    """构建 kb-manifest.json"""
    doc_list = []
    for doc_id, info in state_docs.items():
        doc_list.append({
            "id": doc_id,
            "title": info.get("title", ""),
            "source_file": info.get("source_file", ""),
            "source_agent": info.get("source_agent", ""),
            "added_at": info.get("added_at", ""),
            "updated_at": info.get("updated_at", ""),
            "content_hash": info.get("content_hash", ""),
            "index_link": f"documents/{doc_id}.json",
        })

    top_kw = sorted(kw_index.get("keywords", []), key=lambda x: -x.get("total_frequency", 0))[:20]
    top_c = sorted(c_index.get("concepts", []), key=lambda x: -x.get("importance", 0))[:20]

    return {
        "format_version": "2.0",
        "version": state.get("version", 1),
        "name": "knowledge-base",
        "generated_at": _ts(),
        "document_count": len(state_docs),
        "keyword_count": kw_index.get("total_keywords", 0),
        "concept_count": c_index.get("total_concepts", 0),
        "entity_count": entity_index.get("total_persons", 0) + entity_index.get("total_terms", 0) + entity_index.get("total_works", 0),
        "relation_count": entity_index.get("total_relations", 0) if isinstance(entity_index, dict) else 0,
        "sources": list(state.get("sources", {}).keys()),
        "documents": doc_list,
        "top_keywords": [
            {"keyword": k["keyword"], "document_count": k["document_count"], "total_frequency": k["total_frequency"]}
            for k in top_kw
        ],
        "top_concepts": [
            {"concept": c["concept"], "document_count": c["document_count"], "importance": c["importance"]}
            for c in top_c
        ],
        "change_log": state.get("change_log", [])[-5:],
    }


def _find_related(summary: dict, state_docs: dict, exclude_id: str) -> list:
    """查找关联文档"""
    new_kw = {k["keyword"] for k in summary.get("keywords", [])}
    related = []
    for doc_id, info in state_docs.items():
        if doc_id == exclude_id:
            continue
        info_kw = set(info.get("keywords", []))
        shared = new_kw & info_kw
        if shared:
            related.append({"id": doc_id, "relation": "共享关键词", "shared_keywords": list(shared)[:5]})
    return related[:10]


def _update_related_all(kb_dir, state_docs, new_summaries, update_ids):
    """更新所有受影响文档的 related_documents"""
    new_docs_map = {s["id"]: s["summary"] for s in new_summaries}
    for doc_id, info in state_docs.items():
        if doc_id in update_ids:
            continue
        doc_path = kb_dir / "documents" / f"{doc_id}.json"
        if not doc_path.exists():
            continue
        doc_index = _load_json(doc_path)
        doc_kw = {k["keyword"] for k in doc_index.get("keywords", [])}
        related = list(doc_index.get("related_documents", []))
        existing_rel_ids = {r.get("id") for r in related}
        for ns in new_summaries:
            nid = ns["id"]
            if nid in existing_rel_ids:
                continue
            nkw = {k["keyword"] for k in ns["summary"].get("keywords", [])}
            shared = doc_kw & nkw
            if shared:
                related.append({"id": nid, "relation": "共享关键词", "shared_keywords": list(shared)[:5]})
        if related != doc_index.get("related_documents", []):
            doc_index["related_documents"] = related[:15]
            _save_json(doc_path, doc_index)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Manager v2 — 多源增量知识库管理")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="首次全量构建知识库")
    p_init.add_argument("kb_dir", type=Path)
    p_init.add_argument("summary_dir", type=Path)
    p_init.add_argument("manifest", type=Path)
    p_init.add_argument("--agent", default="doc-content-analysis", help="来源 Agent 名称")

    # update
    p_up = sub.add_parser("update", help="增量更新知识库")
    p_up.add_argument("kb_dir", type=Path)
    p_up.add_argument("summary_dir", type=Path)
    p_up.add_argument("manifest", type=Path)
    p_up.add_argument("--agent", default="doc-content-analysis", help="来源 Agent 名称")

    # register（新增）
    p_reg = sub.add_parser("register", help="跨 Agent 注册输出元数据到知识库")
    p_reg.add_argument("kb_dir", type=Path)
    p_reg.add_argument("agent_name", type=str, help="注册的 Agent 名称")
    p_reg.add_argument("manifest", type=Path, help="Agent 输出的 manifest.json 路径")
    p_reg.add_argument("--summary-dir", type=Path, default=None, help="summary 目录（可选）")

    # status
    p_st = sub.add_parser("status", help="显示知识库状态")
    p_st.add_argument("kb_dir", type=Path)
    p_st.add_argument("--summary-dir", type=Path, default=None)
    p_st.add_argument("--manifest", type=Path, default=None)

    # query（新增）
    p_q = sub.add_parser("query", help="查询知识库")
    p_q.add_argument("kb_dir", type=Path)
    p_q.add_argument("query_type", choices=["keywords", "entities", "documents", "relations"])
    p_q.add_argument("query_text", type=str)

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args.kb_dir, args.summary_dir, args.manifest, args.agent)
    elif args.command == "update":
        cmd_update(args.kb_dir, args.summary_dir, args.manifest, args.agent)
    elif args.command == "register":
        cmd_register(args.kb_dir, args.agent_name, args.manifest, args.summary_dir)
    elif args.command == "status":
        cmd_status(args.kb_dir, args.summary_dir, args.manifest)
    elif args.command == "query":
        cmd_query(args.kb_dir, args.query_type, args.query_text)


if __name__ == "__main__":
    main()
