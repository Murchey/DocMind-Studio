#!/usr/bin/env python3
"""
Knowledge Base Manager — 增量知识库管理

支持三种模式：
  init       — 首次全量构建知识库
  update     — 增量更新（检测新增/变更/删除的文档）
  status     — 显示当前知识库状态和差异预览
"""

import argparse
import hashlib
import json
import shutil
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
        "documents": {},           # id → {source_file, content_hash, added_at, updated_at}
        "change_log": [],          # 每次变更记录
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
    
    # 从 manifest 构建"当前文档"集合
    current_ids = {}
    for doc in manifest_docs:
        if doc.get("status") != "success":
            continue
        source = doc.get("source_file", "")
        summary_json = doc.get("summary_json", "")
        if not summary_json:
            continue
        
        # 计算 content_hash（从 summary.json 中提取摘要内容做哈希）
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
    
    # 分类
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
            changed[doc_id] = {
                **info,
                "old_hash": state_docs[doc_id].get("content_hash"),
            }
        else:
            unchanged[doc_id] = info
    
    return {
        "new": new,
        "changed": changed,
        "unchanged": unchanged,
        "removed": removed,
    }


def _make_doc_id(source_file: str) -> str:
    """从文件名生成文档 ID"""
    stem = Path(source_file).stem
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in stem)
    return f"doc_{safe}"


# ─────────────────────────────────────────────────────────────
# 关键词/概念索引合并
# ─────────────────────────────────────────────────────────────

def _merge_keywords(
    existing_index: dict,
    new_summaries: list[dict],
    removed_ids: set,
):
    """
    增量合并关键词索引。
    existing_index: 现有的 keywords/index.json 内容
    new_summaries: 新增/变更文档的 summary.json 列表 [{"id": ..., "summary": {...}}, ...]
    removed_ids: 待删除的文档 ID 集合
    """
    keywords_map = {}
    
    # 保留未变更文档的现有关键词数据
    for kw_entry in existing_index.get("keywords", []):
        kw_name = kw_entry["keyword"]
        # 只保留不属于已删除文档的关键词关联
        docs = [d for d in kw_entry.get("documents", []) if d.get("id") not in removed_ids]
        if docs:
            keywords_map[kw_name] = {
                "total_frequency": sum(d.get("frequency", 0) for d in docs),
                "document_count": len(docs),
                "documents": docs,
            }
    
    # 合并新文档的关键词
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
            km["documents"].append({
                "id": doc_id,
                "frequency": freq,
                "relevance": relevance,
            })
    
    # 构建输出
    keywords_list = []
    for kw_name, data in sorted(keywords_map.items(), key=lambda x: -x[1]["total_frequency"]):
        keywords_list.append({
            "keyword": kw_name,
            **data,
            "detail_link": f"keywords/{kw_name}.json",
        })
    
    return {
        "generated_at": _ts(),
        "total_keywords": len(keywords_list),
        "keywords": keywords_list,
    }


def _merge_concepts(
    existing_index: dict,
    new_summaries: list[dict],
    removed_ids: set,
):
    """增量合并概念索引（逻辑同 keywords）"""
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
    
    concepts_list = []
    for c_name, data in sorted(concepts_map.items(), key=lambda x: -x[1]["importance"]):
        concepts_list.append({
            "concept": c_name,
            **data,
            "detail_link": f"concepts/{c_name}.json",
        })
    
    return {
        "generated_at": _ts(),
        "total_concepts": len(concepts_list),
        "concepts": concepts_list,
    }


def _merge_toc(existing_toc: dict, new_summaries: list[dict], removed_ids: set):
    """增量合并目录结构"""
    existing_entries = {e.get("id"): e for e in existing_toc.get("toc", [])}
    
    # 移除已删除的
    for rid in removed_ids:
        existing_entries.pop(rid, None)
    
    # 添加/更新新的
    for item in new_summaries:
        doc_id = item["id"]
        summary = item.get("summary", {})
        existing_entries[doc_id] = {
            "id": doc_id,
            "title": summary.get("title", ""),
            "source_file": summary.get("source_file", ""),
            "sections": summary.get("sections", []),
        }
    
    toc_list = list(existing_entries.values())
    return {
        "generated_at": _ts(),
        "document_count": len(toc_list),
        "toc": toc_list,
    }


# ─────────────────────────────────────────────────────────────
# 主命令
# ─────────────────────────────────────────────────────────────

def cmd_init(
    kb_dir: Path,
    summary_dir: Path,
    manifest_path: Path,
):
    """
    首次全量构建知识库。
    输入：doc-content-analysis 的 summary/manifest.json
    输出：knowledge-base/ 完整目录
    """
    manifest = _load_json(manifest_path)
    if manifest.get("status") != "completed":
        print(f"[ERROR] manifest status is '{manifest.get('status')}', expected 'completed'", file=sys.stderr)
        sys.exit(1)
    
    docs = manifest.get("documents", [])
    success_docs = [d for d in docs if d.get("status") == "success"]
    
    if not success_docs:
        print("[INFO] No successful documents to process. Creating empty knowledge base.")
    
    # 初始化目录
    kb_dir.mkdir(parents=True, exist_ok=True)
    (kb_dir / "documents").mkdir(exist_ok=True)
    (kb_dir / "keywords").mkdir(exist_ok=True)
    (kb_dir / "concepts").mkdir(exist_ok=True)
    
    # 初始化状态
    state = _init_state(kb_dir)
    state_docs = {}
    
    # 收集所有 summary
    all_summaries = []
    for doc in success_docs:
        sum_path = Path(doc.get("summary_json", ""))
        if not sum_path.is_absolute():
            sum_path = summary_dir / sum_path
        summary = _load_json(sum_path)
        if not summary:
            continue
        
        doc_id = summary.get("id", _make_doc_id(doc.get("source_file", "")))
        all_summaries.append({"id": doc_id, "doc": doc, "summary": summary})
        
        # 写 documents/<id>.json
        doc_index = {
            **summary,
            "related_documents": [],
        }
        _save_json(kb_dir / "documents" / f"{doc_id}.json", doc_index)
        
        state_docs[doc_id] = {
            "source_file": doc.get("source_file", ""),
            "content_hash": _hash_content(summary),
            "title": summary.get("title", ""),
            "added_at": _ts(),
            "updated_at": _ts(),
        }
    
    # 构建关键词索引
    kw_index = _merge_keywords({"keywords": []}, all_summaries, set())
    _save_json(kb_dir / "keywords" / "index.json", kw_index)
    
    # 构建概念索引
    c_index = _merge_concepts({"concepts": []}, all_summaries, set())
    _save_json(kb_dir / "concepts" / "index.json", c_index)
    
    # 构建目录
    toc = _merge_toc({"toc": []}, all_summaries, set())
    _save_json(kb_dir / "toc.json", toc)
    
    # 构建 kb-manifest.json
    kb_manifest = _build_kb_manifest(kb_dir, state_docs, kw_index, c_index, all_summaries, state)
    _save_json(kb_dir / "kb-manifest.json", kb_manifest)
    
    # 写状态
    state["documents"] = state_docs
    state["document_count"] = len(state_docs)
    state["keyword_count"] = kw_index["total_keywords"]
    state["concept_count"] = c_index["total_concepts"]
    state["updated_at"] = _ts()
    state["change_log"].append({
        "action": "init",
        "timestamp": _ts(),
        "documents_added": len(state_docs),
        "message": "首次全量构建",
    })
    _save_json(kb_dir / ".kb_state.json", state)
    
    print(f"[OK] Knowledge base initialized: {len(state_docs)} documents, {kw_index['total_keywords']} keywords, {c_index['total_concepts']} concepts")
    return kb_dir


def cmd_update(
    kb_dir: Path,
    summary_dir: Path,
    manifest_path: Path,
):
    """
    增量更新知识库。
    检测新增/变更/删除的文档，只处理差异部分。
    """
    state_path = kb_dir / ".kb_state.json"
    if not state_path.exists():
        print("[INFO] No existing .kb_state.json found. Falling back to init mode.")
        return cmd_init(kb_dir, summary_dir, manifest_path)
    
    state = _load_json(state_path)
    manifest = _load_json(manifest_path)
    
    if manifest.get("status") != "completed":
        print(f"[ERROR] manifest status is '{manifest.get('status')}', expected 'completed'", file=sys.stderr)
        sys.exit(1)
    
    docs = manifest.get("documents", [])
    success_docs = [d for d in docs if d.get("status") == "success"]
    
    # 差异检测
    diff = _diff_documents(success_docs, state, summary_dir)
    
    new_count = len(diff["new"])
    changed_count = len(diff["changed"])
    removed_count = len(diff["removed"])
    unchanged_count = len(diff["unchanged"])
    
    if new_count == 0 and changed_count == 0 and removed_count == 0:
        print("[INFO] No changes detected. Knowledge base is up to date.")
        return kb_dir
    
    print(f"[INFO] Changes detected: +{new_count} new, ~{changed_count} changed, -{removed_count} removed, ={unchanged_count} unchanged")
    
    # 收集需要处理的文档
    all_update_ids = set(diff["new"]) | set(diff["changed"])
    removed_ids = set(diff["removed"])
    unchanged_ids = set(diff["unchanged"])
    
    # 读取所有新增/变更文档的 summary
    new_summaries = []
    state_docs = dict(state.get("documents", {}))
    
    for doc in success_docs:
        doc_id = None
        sum_path = Path(doc.get("summary_json", ""))
        if not sum_path.is_absolute():
            sum_path = summary_dir / sum_path
        
        if sum_path.exists():
            summary = _load_json(sum_path)
            doc_id = summary.get("id", _make_doc_id(doc.get("source_file", "")))
        else:
            continue
        
        if doc_id in all_update_ids:
            new_summaries.append({"id": doc_id, "doc": doc, "summary": summary})
            # 写/更新 documents/<id>.json
            doc_index = {
                **summary,
                "related_documents": _find_related(summary, state_docs, doc_id),
            }
            _save_json(kb_dir / "documents" / f"{doc_id}.json", doc_index)
            
            # 更新 state
            state_docs[doc_id] = {
                "source_file": doc.get("source_file", ""),
                "content_hash": diff["new"].get(doc_id, diff["changed"].get(doc_id, {})).get("content_hash", ""),
                "title": summary.get("title", ""),
                "added_at": state_docs.get(doc_id, {}).get("added_at", _ts()),
                "updated_at": _ts(),
            }
    
    # 从 state 中移除已删除的文档
    for rid in removed_ids:
        state_docs.pop(rid, None)
        # 清理对应的 document json
        doc_path = kb_dir / "documents" / f"{rid}.json"
        if doc_path.exists():
            doc_path.unlink()
    
    # 增量合并关键词索引
    existing_kw = _load_json(kb_dir / "keywords" / "index.json")
    kw_index = _merge_keywords(existing_kw, new_summaries, removed_ids)
    _save_json(kb_dir / "keywords" / "index.json", kw_index)
    
    # 增量合并概念索引
    existing_c = _load_json(kb_dir / "concepts" / "index.json")
    c_index = _merge_concepts(existing_c, new_summaries, removed_ids)
    _save_json(kb_dir / "concepts" / "index.json", c_index)
    
    # 增量合并目录
    existing_toc = _load_json(kb_dir / "toc.json")
    toc = _merge_toc(existing_toc, new_summaries, removed_ids)
    _save_json(kb_dir / "toc.json", toc)
    
    # 更新跨文档关联
    _update_related_all(kb_dir, state_docs, new_summaries, all_update_ids)
    
    # 更新 kb-manifest
    kb_manifest = _build_kb_manifest(kb_dir, state_docs, kw_index, c_index, new_summaries, state)
    _save_json(kb_dir / "kb-manifest.json", kb_manifest)
    
    # 更新状态
    state["document_count"] = len(state_docs)
    state["keyword_count"] = kw_index["total_keywords"]
    state["concept_count"] = c_index["total_concepts"]
    state["version"] += 1
    state["documents"] = state_docs
    state["updated_at"] = _ts()
    
    parts = []
    if new_count: parts.append(f"+{new_count} added")
    if changed_count: parts.append(f"~{changed_count} updated")
    if removed_count: parts.append(f"-{removed_count} removed")
    
    state["change_log"].append({
        "action": "update",
        "version": state["version"],
        "timestamp": _ts(),
        "new_count": new_count,
        "changed_count": changed_count,
        "removed_count": removed_count,
        "message": ", ".join(parts),
    })
    _save_json(state_path, state)
    
    print(f"[OK] Knowledge base updated to v{state['version']}: {', '.join(parts)}")
    return kb_dir


def cmd_status(kb_dir: Path, summary_dir: Path, manifest_path: Path):
    """显示当前知识库状态和待处理的差异"""
    state_path = kb_dir / ".kb_state.json"
    if not state_path.exists():
        print("[STATUS] Knowledge base not yet initialized. Run 'init' first.")
        return
    
    state = _load_json(state_path)
    manifest = _load_json(manifest_path)
    docs = manifest.get("documents", [])
    success_docs = [d for d in docs if d.get("status") == "success"]
    
    diff = _diff_documents(success_docs, state, summary_dir)
    
    print(f"Knowledge Base Status (v{state['version']})")
    print(f"  Documents: {state['document_count']} total")
    print(f"  Keywords:  {state['keyword_count']}")
    print(f"  Concepts:  {state['concept_count']}")
    print(f"  Last updated: {state.get('updated_at', 'N/A')}")
    print()
    print("Pending Changes:")
    print(f"  + New:     {len(diff['new'])} document(s)")
    for doc_id, info in diff['new'].items():
        print(f"      - {doc_id} ({info.get('source_file', '?')})")
    print(f"  ~ Changed: {len(diff['changed'])} document(s)")
    for doc_id, info in diff['changed'].items():
        print(f"      - {doc_id} ({info.get('source_file', '?')})")
    print(f"  - Removed: {len(diff['removed'])} document(s)")
    for doc_id, info in diff['removed'].items():
        print(f"      - {doc_id} ({info.get('source_file', '?')})")
    print(f"  = Unchanged: {len(diff['unchanged'])} document(s)")
    
    if len(diff['new']) == 0 and len(diff['changed']) == 0 and len(diff['removed']) == 0:
        print("\n  Knowledge base is up to date.")


# ─────────────────────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────────────────────

def _build_kb_manifest(
    kb_dir: Path,
    state_docs: dict,
    kw_index: dict,
    c_index: dict,
    summaries: list[dict],
    state: dict,
) -> dict:
    """构建 kb-manifest.json"""
    doc_list = []
    for doc_id, info in state_docs.items():
        doc_list.append({
            "id": doc_id,
            "title": info.get("title", ""),
            "source_file": info.get("source_file", ""),
            "added_at": info.get("added_at", ""),
            "updated_at": info.get("updated_at", ""),
            "content_hash": info.get("content_hash", ""),
            "index_link": f"documents/{doc_id}.json",
        })
    
    # top keywords (前 20)
    top_kw = sorted(kw_index.get("keywords", []), key=lambda x: -x.get("total_frequency", 0))[:20]
    
    # top concepts (前 20)
    top_c = sorted(c_index.get("concepts", []), key=lambda x: -x.get("importance", 0))[:20]
    
    return {
        "version": state.get("version", 1),
        "name": "knowledge-base",
        "generated_at": _ts(),
        "document_count": len(state_docs),
        "keyword_count": kw_index.get("total_keywords", 0),
        "concept_count": c_index.get("total_concepts", 0),
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
    """在新文档的 summary 中查找与已有文档的关联"""
    new_kw = {k["keyword"] for k in summary.get("keywords", [])}
    related = []
    for doc_id, info in state_docs.items():
        if doc_id == exclude_id:
            continue
        # 简单策略：共享关键词数 > 0 即关联
        info_kw = set(info.get("keywords", []))
        shared = new_kw & info_kw
        if shared:
            related.append({
                "id": doc_id,
                "relation": "共享关键词",
                "shared_keywords": list(shared)[:5],
            })
    return related[:10]


def _update_related_all(
    kb_dir: Path,
    state_docs: dict,
    new_summaries: list[dict],
    update_ids: set,
):
    """更新所有受影响文档的 related_documents 字段"""
    # 为新增/变更文档计算关联
    new_docs_map = {s["id"]: s["summary"] for s in new_summaries}
    
    # 更新未变更文档的关联（它们可能引用到新增文档）
    for doc_id, info in state_docs.items():
        if doc_id in update_ids:
            continue  # 已处理
        doc_path = kb_dir / "documents" / f"{doc_id}.json"
        if not doc_path.exists():
            continue
        doc_index = _load_json(doc_path)
        doc_kw = {k["keyword"] for k in doc_index.get("keywords", [])}
        
        # 检查与新增文档的关联
        related = list(doc_index.get("related_documents", []))
        existing_rel_ids = {r.get("id") for r in related}
        for ns in new_summaries:
            nid = ns["id"]
            if nid in existing_rel_ids:
                continue
            nkw = {k["keyword"] for k in ns["summary"].get("keywords", [])}
            shared = doc_kw & nkw
            if shared:
                related.append({
                    "id": nid,
                    "relation": "共享关键词",
                    "shared_keywords": list(shared)[:5],
                })
        
        if related != doc_index.get("related_documents", []):
            doc_index["related_documents"] = related[:15]
            _save_json(doc_path, doc_index)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Manager — 增量知识库管理")
    sub = parser.add_subparsers(dest="command", required=True)
    
    # init
    p_init = sub.add_parser("init", help="首次全量构建知识库")
    p_init.add_argument("kb_dir", type=Path, help="知识库输出目录（如 knowledge-base/）")
    p_init.add_argument("summary_dir", type=Path, help="doc-content-analysis 的 summary 目录")
    p_init.add_argument("manifest", type=Path, help="manifest.json 路径")
    
    # update
    p_up = sub.add_parser("update", help="增量更新知识库")
    p_up.add_argument("kb_dir", type=Path)
    p_up.add_argument("summary_dir", type=Path)
    p_up.add_argument("manifest", type=Path)
    
    # status
    p_st = sub.add_parser("status", help="显示知识库状态和差异预览")
    p_st.add_argument("kb_dir", type=Path)
    p_st.add_argument("summary_dir", type=Path)
    p_st.add_argument("manifest", type=Path)
    
    args = parser.parse_args()
    
    if args.command == "init":
        cmd_init(args.kb_dir, args.summary_dir, args.manifest)
    elif args.command == "update":
        cmd_update(args.kb_dir, args.summary_dir, args.manifest)
    elif args.command == "status":
        cmd_status(args.kb_dir, args.summary_dir, args.manifest)


if __name__ == "__main__":
    main()
