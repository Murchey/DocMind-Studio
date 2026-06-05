import os
import json
import yaml
import webbrowser
import threading
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file
from format_manager import FormatManager

app = Flask(__name__)
manager = FormatManager()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="title">格式配置管理器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: relative;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .language-switcher {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.2);
            padding: 8px 12px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .language-switcher:hover {
            background: rgba(255,255,255,0.3);
        }
        .language-switcher svg {
            width: 18px;
            height: 18px;
        }
        .language-switcher select {
            background: transparent;
            border: none;
            color: white;
            font-size: 14px;
            cursor: pointer;
            outline: none;
        }
        .language-switcher select option {
            background: #333;
            color: white;
        }
        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        .sidebar {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: fit-content;
            position: sticky;
            top: 20px;
        }
        .sidebar h3 {
            margin-bottom: 15px;
            color: #667eea;
            font-size: 16px;
        }
        .config-list {
            list-style: none;
        }
        .config-item {
            padding: 12px 15px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .config-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        .config-item.active {
            background: #667eea;
            color: white;
        }
        .config-item .badge {
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 10px;
            background: rgba(0,0,0,0.1);
        }
        .config-item.active .badge {
            background: rgba(255,255,255,0.2);
        }
        .editor-panel {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .editor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        .editor-header h2 {
            color: #333;
            font-size: 20px;
        }
        .btn-group {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd6;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background: #c82333;
        }
        .btn-outline {
            background: transparent;
            border: 1px solid #667eea;
            color: #667eea;
        }
        .btn-outline:hover {
            background: #667eea;
            color: white;
        }
        .section {
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #555;
            font-size: 13px;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102,126,234,0.2);
        }
        .form-group textarea {
            min-height: 80px;
            resize: vertical;
        }
        .form-group .help-text {
            font-size: 11px;
            color: #888;
            margin-top: 3px;
        }
        .actions-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: white;
            border-radius: 10px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .modal-header h3 {
            font-size: 18px;
            color: #333;
        }
        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #888;
        }
        .modal-close:hover {
            color: #333;
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 6px;
            color: white;
            font-size: 14px;
            z-index: 2000;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .notification.success {
            background: #28a745;
        }
        .notification.error {
            background: #dc3545;
        }
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
        .empty-state svg {
            width: 60px;
            height: 60px;
            margin-bottom: 15px;
            opacity: 0.5;
        }
        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
            flex-wrap: wrap;
        }
        .tab {
            padding: 8px 16px;
            background: #f8f9fa;
            border: none;
            border-radius: 4px 4px 0 0;
            cursor: pointer;
            font-size: 13px;
            color: #666;
            transition: all 0.2s;
        }
        .tab.active {
            background: #667eea;
            color: white;
        }
        .tab:hover:not(.active) {
            background: #e9ecef;
        }
        .yaml-preview {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.5;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 data-i18n="headerTitle">📝 格式配置管理器</h1>
            <p data-i18n="headerDesc">管理学术论文、公文和文档的格式模板配置</p>
            <div class="language-switcher">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
                <select id="languageSelect" onchange="changeLanguage(this.value)">
                    <option value="zh">中文</option>
                    <option value="en">English</option>
                </select>
            </div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <h3 data-i18n="configList">配置列表</h3>
                <ul class="config-list" id="configList"></ul>
                <div style="margin-top: 15px;">
                    <button class="btn btn-outline" style="width: 100%;" onclick="showNewConfigModal()">
                        <span data-i18n="newConfig">+ 新建配置</span>
                    </button>
                </div>
                <div style="margin-top: 10px;">
                    <button class="btn btn-outline" style="width: 100%;" onclick="showImportModal()">
                        <span data-i18n="importConfig">📁 导入配置</span>
                    </button>
                </div>
            </div>
            
            <div class="editor-panel" id="editorPanel">
                <div class="empty-state" id="emptyState">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    <h3 data-i18n="selectConfig">选择一个配置开始编辑</h3>
                    <p data-i18n="selectConfigDesc">从左侧列表选择一个配置，或创建新配置</p>
                </div>
                
                <div id="editorContent" style="display: none;">
                    <div class="editor-header">
                        <h2 id="editorTitle" data-i18n="editConfig">配置编辑</h2>
                        <div class="btn-group">
                            <button class="btn btn-secondary" onclick="showYamlPreview()">
                                <span data-i18n="previewYaml">预览 YAML</span>
                            </button>
                            <button class="btn btn-success" onclick="saveConfig()">
                                <span data-i18n="save">💾 保存</span>
                            </button>
                            <button class="btn btn-primary" onclick="showSaveAsModal()">
                                <span data-i18n="saveAs">另存为</span>
                            </button>
                            <button class="btn btn-danger" onclick="deleteConfig()">
                                <span data-i18n="delete">🗑️ 删除</span>
                            </button>
                        </div>
                    </div>
                    
                    <div class="tabs">
                        <button class="tab active" onclick="switchTab('basic')" data-i18n="tabBasic">基本信息</button>
                        <button class="tab" onclick="switchTab('page')" data-i18n="tabPage">页面设置</button>
                        <button class="tab" onclick="switchTab('heading')" data-i18n="tabHeading">标题样式</button>
                        <button class="tab" onclick="switchTab('body')" data-i18n="tabBody">正文格式</button>
                        <button class="tab" onclick="switchTab('table')" data-i18n="tabTable">表格格式</button>
                        <button class="tab" onclick="switchTab('footnote')" data-i18n="tabFootnote">脚注格式</button>
                        <button class="tab" onclick="switchTab('other')" data-i18n="tabOther">其他设置</button>
                    </div>
                    
                    <div id="tabContent"></div>
                    
                    <div class="actions-bar">
                        <button class="btn btn-outline" onclick="resetConfig()">
                            <span data-i18n="reset">重置修改</span>
                        </button>
                        <div class="btn-group">
                            <button class="btn btn-secondary" onclick="showYamlPreview()">
                                <span data-i18n="previewYaml">预览 YAML</span>
                            </button>
                            <button class="btn btn-success" onclick="saveConfig()">
                                <span data-i18n="save">💾 保存</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="newConfigModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 data-i18n="newConfigTitle">新建配置</h3>
                <button class="modal-close" onclick="closeModal('newConfigModal')">&times;</button>
            </div>
            <div class="form-group">
                <label data-i18n="configName">配置名称</label>
                <input type="text" id="newConfigName" placeholder="my_custom_config">
            </div>
            <div class="form-group">
                <label data-i18n="baseTemplate">基于模板</label>
                <select id="baseTemplate">
                    <option value="chinese_academic" data-i18n="chineseAcademic">中文学术论文</option>
                    <option value="english_academic" data-i18n="englishAcademic">英文论文</option>
                    <option value="empty" data-i18n="emptyTemplate">空白模板</option>
                </select>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="closeModal('newConfigModal')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createNewConfig()" data-i18n="create">创建</button>
            </div>
        </div>
    </div>
    
    <div class="modal" id="saveAsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 data-i18n="saveAsTitle">另存为</h3>
                <button class="modal-close" onclick="closeModal('saveAsModal')">&times;</button>
            </div>
            <div class="form-group">
                <label data-i18n="newConfigName">新配置名称</label>
                <input type="text" id="saveAsName" placeholder="输入新名称">
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="closeModal('saveAsModal')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="saveAsConfig()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
    <div class="modal" id="importModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 data-i18n="importTitle">导入配置</h3>
                <button class="modal-close" onclick="closeModal('importModal')">&times;</button>
            </div>
            <div class="form-group">
                <label data-i18n="configName">配置名称</label>
                <input type="text" id="importName" placeholder="留空则使用文件名">
            </div>
            <div class="form-group">
                <label data-i18n="yamlContent">YAML 文件内容</label>
                <textarea id="importContent" rows="10" placeholder="粘贴 YAML 内容..."></textarea>
            </div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="closeModal('importModal')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="importConfig()" data-i18n="import">导入</button>
            </div>
        </div>
    </div>
    
    <div class="modal" id="yamlPreviewModal">
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header">
                <h3 data-i18n="yamlPreviewTitle">YAML 预览</h3>
                <button class="modal-close" onclick="closeModal('yamlPreviewModal')">&times;</button>
            </div>
            <div class="yaml-preview" id="yamlPreviewContent"></div>
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-primary" onclick="closeModal('yamlPreviewModal')" data-i18n="close">关闭</button>
            </div>
        </div>
    </div>
    
    <script>
        // Language translations
        const translations = {
            zh: {
                title: '格式配置管理器',
                headerTitle: '📝 格式配置管理器',
                headerDesc: '管理学术论文、公文和文档的格式模板配置',
                configList: '配置列表',
                newConfig: '+ 新建配置',
                importConfig: '📁 导入配置',
                selectConfig: '选择一个配置开始编辑',
                selectConfigDesc: '从左侧列表选择一个配置，或创建新配置',
                editConfig: '配置编辑',
                previewYaml: '预览 YAML',
                save: '💾 保存',
                saveAs: '另存为',
                delete: '🗑️ 删除',
                tabBasic: '基本信息',
                tabPage: '页面设置',
                tabHeading: '标题样式',
                tabBody: '正文格式',
                tabTable: '表格格式',
                tabFootnote: '脚注格式',
                tabOther: '其他设置',
                reset: '重置修改',
                newConfigTitle: '新建配置',
                configName: '配置名称',
                baseTemplate: '基于模板',
                chineseAcademic: '中文学术论文',
                englishAcademic: '英文论文',
                emptyTemplate: '空白模板',
                cancel: '取消',
                create: '创建',
                saveAsTitle: '另存为',
                newConfigName: '新配置名称',
                importTitle: '导入配置',
                yamlContent: 'YAML 文件内容',
                import: '导入',
                yamlPreviewTitle: 'YAML 预览',
                close: '关闭',
                // Form labels
                templateName: '模板名称',
                description: '描述',
                standard: '标准',
                pageSize: '页面大小',
                marginTop: '上边距 (cm)',
                marginBottom: '下边距 (cm)',
                marginLeft: '左边距 (cm)',
                marginRight: '右边距 (cm)',
                level1Heading: '一级标题',
                level2Heading: '二级标题',
                level3Heading: '三级标题',
                font: '字体',
                fontSize: '字号 (pt)',
                bold: '加粗',
                alignment: '对齐',
                center: '居中',
                left: '左对齐',
                yes: '是',
                no: '否',
                fontConfig: '字体配置',
                chineseFont: '中文字体',
                chineseFontSize: '中文正文字号 (pt)',
                englishFont: '英文字体',
                englishFontSize: '英文正文字号 (pt)',
                headingFont: '标题字体',
                paragraphFormat: '段落格式',
                lineSpacing: '行距',
                singleSpacing: '单倍行距',
                spacing15: '1.5倍行距',
                doubleSpacing: '双倍行距',
                firstLineIndent: '首行缩进 (字符)',
                justify: '两端对齐',
                spacingBefore: '段前间距 (pt)',
                spacingAfter: '段后间距 (pt)',
                tableFormat: '表格格式',
                borderStyle: '边框样式',
                threeLine: '三线表',
                single: '单线',
                none: '无边框',
                headerFontSize: '表头字号 (pt)',
                cellFontSize: '单元格字号 (pt)',
                footnoteFormat: '脚注格式',
                enableFootnote: '启用脚注处理',
                chineseFontSize2: '中文字号 (pt)',
                englishFontSize2: '英文字号 (pt)',
                numberingFormat: '编号格式',
                circled: '带圈数字',
                arabic: '阿拉伯数字',
                roman: '罗马数字',
                restartPerPage: '每页重新编号',
                protectionSettings: '保护设置',
                protectFormulas: '保护公式',
                protectImages: '保护图片',
                protectTables: '保护表格',
                // Messages
                configSaved: '配置已保存',
                configSavedAs: '配置已另存为',
                configCreated: '配置已创建',
                configDeleted: '配置已删除',
                configImported: '配置已导入',
                configReset: '配置已重置',
                confirmDelete: '确定要删除配置',
                cannotOverwrite: '不能覆盖内置配置',
                error: '错误',
                success: '成功'
            },
            en: {
                title: 'Format Configuration Manager',
                headerTitle: '📝 Format Configuration Manager',
                headerDesc: 'Manage format template configurations for academic papers, official documents, and technical reports',
                configList: 'Configuration List',
                newConfig: '+ New Configuration',
                importConfig: '📁 Import Configuration',
                selectConfig: 'Select a configuration to edit',
                selectConfigDesc: 'Select a configuration from the left list, or create a new one',
                editConfig: 'Edit Configuration',
                previewYaml: 'Preview YAML',
                save: '💾 Save',
                saveAs: 'Save As',
                delete: '🗑️ Delete',
                tabBasic: 'Basic Info',
                tabPage: 'Page Settings',
                tabHeading: 'Heading Styles',
                tabBody: 'Body Format',
                tabTable: 'Table Format',
                tabFootnote: 'Footnote Format',
                tabOther: 'Other Settings',
                reset: 'Reset Changes',
                newConfigTitle: 'New Configuration',
                configName: 'Configuration Name',
                baseTemplate: 'Based on Template',
                chineseAcademic: 'Chinese Academic',
                englishAcademic: 'English Academic',
                emptyTemplate: 'Empty Template',
                cancel: 'Cancel',
                create: 'Create',
                saveAsTitle: 'Save As',
                newConfigName: 'New Configuration Name',
                importTitle: 'Import Configuration',
                yamlContent: 'YAML File Content',
                import: 'Import',
                yamlPreviewTitle: 'YAML Preview',
                close: 'Close',
                // Form labels
                templateName: 'Template Name',
                description: 'Description',
                standard: 'Standard',
                pageSize: 'Page Size',
                marginTop: 'Top Margin (cm)',
                marginBottom: 'Bottom Margin (cm)',
                marginLeft: 'Left Margin (cm)',
                marginRight: 'Right Margin (cm)',
                level1Heading: 'Heading Level 1',
                level2Heading: 'Heading Level 2',
                level3Heading: 'Heading Level 3',
                font: 'Font',
                fontSize: 'Font Size (pt)',
                bold: 'Bold',
                alignment: 'Alignment',
                center: 'Center',
                left: 'Left',
                yes: 'Yes',
                no: 'No',
                fontConfig: 'Font Configuration',
                chineseFont: 'Chinese Font',
                chineseFontSize: 'Chinese Body Size (pt)',
                englishFont: 'English Font',
                englishFontSize: 'English Body Size (pt)',
                headingFont: 'Heading Font',
                paragraphFormat: 'Paragraph Format',
                lineSpacing: 'Line Spacing',
                singleSpacing: 'Single Spacing',
                spacing15: '1.5x Spacing',
                doubleSpacing: 'Double Spacing',
                firstLineIndent: 'First Line Indent (chars)',
                justify: 'Justify',
                spacingBefore: 'Spacing Before (pt)',
                spacingAfter: 'Spacing After (pt)',
                tableFormat: 'Table Format',
                borderStyle: 'Border Style',
                threeLine: 'Three-line',
                single: 'Single',
                none: 'None',
                headerFontSize: 'Header Font Size (pt)',
                cellFontSize: 'Cell Font Size (pt)',
                footnoteFormat: 'Footnote Format',
                enableFootnote: 'Enable Footnote',
                chineseFontSize2: 'Chinese Size (pt)',
                englishFontSize2: 'English Size (pt)',
                numberingFormat: 'Numbering Format',
                circled: 'Circled',
                arabic: 'Arabic',
                roman: 'Roman',
                restartPerPage: 'Restart Per Page',
                protectionSettings: 'Protection Settings',
                protectFormulas: 'Protect Formulas',
                protectImages: 'Protect Images',
                protectTables: 'Protect Tables',
                // Messages
                configSaved: 'Configuration saved',
                configSavedAs: 'Configuration saved as',
                configCreated: 'Configuration created',
                configDeleted: 'Configuration deleted',
                configImported: 'Configuration imported',
                configReset: 'Configuration reset',
                confirmDelete: 'Are you sure to delete configuration',
                cannotOverwrite: 'Cannot overwrite builtin configuration',
                error: 'Error',
                success: 'Success'
            }
        };
        
        let currentLang = localStorage.getItem('language') || 'zh';
        let currentConfig = null;
        let currentConfigName = null;
        let originalConfig = null;
        
        function t(key) {
            return translations[currentLang][key] || key;
        }
        
        function changeLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('language', lang);
            applyTranslations();
        }
        
        function applyTranslations() {
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) {
                    el.textContent = translations[currentLang][key];
                }
            });
            document.title = t('title');
            document.getElementById('languageSelect').value = currentLang;
            
            // Refresh tab content if config is loaded
            if (currentConfig) {
                const activeTab = document.querySelector('.tab.active');
                if (activeTab) {
                    const tabName = activeTab.getAttribute('onclick').match(/'(\\w+)'/)[1];
                    switchTab(tabName);
                }
            }
        }
        
        async function loadConfigs() {
            const response = await fetch('/api/configs');
            const configs = await response.json();
            
            const list = document.getElementById('configList');
            list.innerHTML = configs.map(config => `
                <li class="config-item ${currentConfigName === config.name ? 'active' : ''}" 
                    onclick="loadConfig('${config.name}')">
                    <span>${config.name}</span>
                    <span class="badge">${config.type}</span>
                </li>
            `).join('');
        }
        
        async function loadConfig(name) {
            const response = await fetch(`/api/configs/${name}`);
            const config = await response.json();
            
            currentConfig = config;
            currentConfigName = name;
            originalConfig = JSON.parse(JSON.stringify(config));
            
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('editorContent').style.display = 'block';
            document.getElementById('editorTitle').textContent = `${t('editConfig')}: ${name}`;
            
            switchTab('basic');
            loadConfigs();
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            const content = document.getElementById('tabContent');
            content.innerHTML = getTabContent(tab);
        }
        
        function getTabContent(tab) {
            if (!currentConfig) return '';
            
            switch(tab) {
                case 'basic':
                    return `
                        <div class="section">
                            <div class="section-title">${t('tabBasic')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('templateName')}</label>
                                    <input type="text" value="${currentConfig.metadata?.name || ''}" 
                                           onchange="updateConfig('metadata.name', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('description')}</label>
                                    <input type="text" value="${currentConfig.metadata?.description || ''}"
                                           onchange="updateConfig('metadata.description', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('standard')}</label>
                                    <input type="text" value="${currentConfig.metadata?.standard || ''}"
                                           onchange="updateConfig('metadata.standard', this.value)">
                                </div>
                            </div>
                        </div>
                    `;
                case 'page':
                    return `
                        <div class="section">
                            <div class="section-title">${t('tabPage')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('pageSize')}</label>
                                    <select onchange="updateConfig('page.size', this.value)">
                                        <option value="A4" ${currentConfig.page?.size === 'A4' ? 'selected' : ''}>A4</option>
                                        <option value="Letter" ${currentConfig.page?.size === 'Letter' ? 'selected' : ''}>Letter</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('marginTop')}</label>
                                    <input type="number" step="0.1" value="${currentConfig.page?.margin_top || 2.54}"
                                           onchange="updateConfig('page.margin_top', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('marginBottom')}</label>
                                    <input type="number" step="0.1" value="${currentConfig.page?.margin_bottom || 2.54}"
                                           onchange="updateConfig('page.margin_bottom', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('marginLeft')}</label>
                                    <input type="number" step="0.1" value="${currentConfig.page?.margin_left || 3.17}"
                                           onchange="updateConfig('page.margin_left', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('marginRight')}</label>
                                    <input type="number" step="0.1" value="${currentConfig.page?.margin_right || 2.54}"
                                           onchange="updateConfig('page.margin_right', parseFloat(this.value))">
                                </div>
                            </div>
                        </div>
                    `;
                case 'heading':
                    return `
                        <div class="section">
                            <div class="section-title">${t('level1Heading')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('font')}</label>
                                    <input type="text" value="${currentConfig.heading?.level1?.font || ''}"
                                           onchange="updateConfig('heading.level1.font', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('fontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.heading?.level1?.size || 16}"
                                           onchange="updateConfig('heading.level1.size', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('bold')}</label>
                                    <select onchange="updateConfig('heading.level1.bold', this.value === 'true')">
                                        <option value="true" ${currentConfig.heading?.level1?.bold ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.heading?.level1?.bold ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('alignment')}</label>
                                    <select onchange="updateConfig('heading.level1.alignment', this.value)">
                                        <option value="center" ${currentConfig.heading?.level1?.alignment === 'center' ? 'selected' : ''}>${t('center')}</option>
                                        <option value="left" ${currentConfig.heading?.level1?.alignment === 'left' ? 'selected' : ''}>${t('left')}</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="section">
                            <div class="section-title">${t('level2Heading')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('font')}</label>
                                    <input type="text" value="${currentConfig.heading?.level2?.font || ''}"
                                           onchange="updateConfig('heading.level2.font', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('fontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.heading?.level2?.size || 14}"
                                           onchange="updateConfig('heading.level2.size', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('bold')}</label>
                                    <select onchange="updateConfig('heading.level2.bold', this.value === 'true')">
                                        <option value="true" ${currentConfig.heading?.level2?.bold ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.heading?.level2?.bold ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('alignment')}</label>
                                    <select onchange="updateConfig('heading.level2.alignment', this.value)">
                                        <option value="left" ${currentConfig.heading?.level2?.alignment === 'left' ? 'selected' : ''}>${t('left')}</option>
                                        <option value="center" ${currentConfig.heading?.level2?.alignment === 'center' ? 'selected' : ''}>${t('center')}</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="section">
                            <div class="section-title">${t('level3Heading')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('font')}</label>
                                    <input type="text" value="${currentConfig.heading?.level3?.font || ''}"
                                           onchange="updateConfig('heading.level3.font', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('fontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.heading?.level3?.size || 12}"
                                           onchange="updateConfig('heading.level3.size', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('bold')}</label>
                                    <select onchange="updateConfig('heading.level3.bold', this.value === 'true')">
                                        <option value="true" ${currentConfig.heading?.level3?.bold ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.heading?.level3?.bold ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('alignment')}</label>
                                    <select onchange="updateConfig('heading.level3.alignment', this.value)">
                                        <option value="left" ${currentConfig.heading?.level3?.alignment === 'left' ? 'selected' : ''}>${t('left')}</option>
                                        <option value="center" ${currentConfig.heading?.level3?.alignment === 'center' ? 'selected' : ''}>${t('center')}</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    `;
                case 'body':
                    return `
                        <div class="section">
                            <div class="section-title">${t('fontConfig')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('chineseFont')}</label>
                                    <input type="text" value="${currentConfig.fonts?.chinese?.family || ''}"
                                           onchange="updateConfig('fonts.chinese.family', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('chineseFontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.fonts?.chinese?.size || 12}"
                                           onchange="updateConfig('fonts.chinese.size', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('englishFont')}</label>
                                    <input type="text" value="${currentConfig.fonts?.english?.family || ''}"
                                           onchange="updateConfig('fonts.english.family', this.value)">
                                </div>
                                <div class="form-group">
                                    <label>${t('englishFontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.fonts?.english?.size || 12}"
                                           onchange="updateConfig('fonts.english.size', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('headingFont')}</label>
                                    <input type="text" value="${currentConfig.fonts?.heading?.family || ''}"
                                           onchange="updateConfig('fonts.heading.family', this.value)">
                                </div>
                            </div>
                        </div>
                        <div class="section">
                            <div class="section-title">${t('paragraphFormat')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('lineSpacing')}</label>
                                    <select onchange="updateConfig('paragraph.line_spacing', this.value)">
                                        <option value="1" ${currentConfig.paragraph?.line_spacing === 1 ? 'selected' : ''}>${t('singleSpacing')}</option>
                                        <option value="1.5" ${currentConfig.paragraph?.line_spacing === 1.5 ? 'selected' : ''}>${t('spacing15')}</option>
                                        <option value="2" ${currentConfig.paragraph?.line_spacing === 2 ? 'selected' : ''}>${t('doubleSpacing')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('firstLineIndent')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.paragraph?.first_indent || 2}"
                                           onchange="updateConfig('paragraph.first_indent', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('alignment')}</label>
                                    <select onchange="updateConfig('paragraph.alignment', this.value)">
                                        <option value="justify" ${currentConfig.paragraph?.alignment === 'justify' ? 'selected' : ''}>${t('justify')}</option>
                                        <option value="left" ${currentConfig.paragraph?.alignment === 'left' ? 'selected' : ''}>${t('left')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('spacingBefore')}</label>
                                    <input type="number" step="1" value="${currentConfig.paragraph?.spacing_before || 0}"
                                           onchange="updateConfig('paragraph.spacing_before', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('spacingAfter')}</label>
                                    <input type="number" step="1" value="${currentConfig.paragraph?.spacing_after || 0}"
                                           onchange="updateConfig('paragraph.spacing_after', parseFloat(this.value))">
                                </div>
                            </div>
                        </div>
                    `;
                case 'table':
                    return `
                        <div class="section">
                            <div class="section-title">${t('tableFormat')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('borderStyle')}</label>
                                    <select onchange="updateConfig('table.border', this.value)">
                                        <option value="three-line" ${currentConfig.table?.border === 'three-line' ? 'selected' : ''}>${t('threeLine')}</option>
                                        <option value="single" ${currentConfig.table?.border === 'single' ? 'selected' : ''}>${t('single')}</option>
                                        <option value="none" ${currentConfig.table?.border === 'none' ? 'selected' : ''}>${t('none')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('headerFontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.table?.header_font_size || 10.5}"
                                           onchange="updateConfig('table.header_font_size', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('cellFontSize')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.table?.cell_font_size || 10.5}"
                                           onchange="updateConfig('table.cell_font_size', parseFloat(this.value))">
                                </div>
                            </div>
                        </div>
                    `;
                case 'footnote':
                    return `
                        <div class="section">
                            <div class="section-title">${t('footnoteFormat')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('enableFootnote')}</label>
                                    <select onchange="updateConfig('footnote.enabled', this.value === 'true')">
                                        <option value="true" ${currentConfig.footnote?.enabled ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.footnote?.enabled ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('chineseFontSize2')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.footnote?.font_size_cn || 10.5}"
                                           onchange="updateConfig('footnote.font_size_cn', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('englishFontSize2')}</label>
                                    <input type="number" step="0.5" value="${currentConfig.footnote?.font_size_en || 9}"
                                           onchange="updateConfig('footnote.font_size_en', parseFloat(this.value))">
                                </div>
                                <div class="form-group">
                                    <label>${t('numberingFormat')}</label>
                                    <select onchange="updateConfig('footnote.numbering', this.value)">
                                        <option value="circled" ${currentConfig.footnote?.numbering === 'circled' ? 'selected' : ''}>${t('circled')}</option>
                                        <option value="arabic" ${currentConfig.footnote?.numbering === 'arabic' ? 'selected' : ''}>${t('arabic')}</option>
                                        <option value="roman" ${currentConfig.footnote?.numbering === 'roman' ? 'selected' : ''}>${t('roman')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('restartPerPage')}</label>
                                    <select onchange="updateConfig('footnote.restart_per_page', this.value === 'true')">
                                        <option value="true" ${currentConfig.footnote?.restart_per_page ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.footnote?.restart_per_page ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    `;
                case 'other':
                    return `
                        <div class="section">
                            <div class="section-title">${t('protectionSettings')}</div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label>${t('protectFormulas')}</label>
                                    <select onchange="updateConfig('protection.preserve_formulas', this.value === 'true')">
                                        <option value="true" ${currentConfig.protection?.preserve_formulas ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.protection?.preserve_formulas ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('protectImages')}</label>
                                    <select onchange="updateConfig('protection.preserve_images', this.value === 'true')">
                                        <option value="true" ${currentConfig.protection?.preserve_images ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.protection?.preserve_images ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>${t('protectTables')}</label>
                                    <select onchange="updateConfig('protection.preserve_tables', this.value === 'true')">
                                        <option value="true" ${currentConfig.protection?.preserve_tables ? 'selected' : ''}>${t('yes')}</option>
                                        <option value="false" ${!currentConfig.protection?.preserve_tables ? 'selected' : ''}>${t('no')}</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    `;
                default:
                    return '';
            }
        }
        
        function updateConfig(path, value) {
            const keys = path.split('.');
            let obj = currentConfig;
            
            for (let i = 0; i < keys.length - 1; i++) {
                if (!obj[keys[i]]) obj[keys[i]] = {};
                obj = obj[keys[i]];
            }
            
            obj[keys[keys.length - 1]] = value;
        }
        
        async function saveConfig() {
            const response = await fetch(`/api/configs/${currentConfigName}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(currentConfig)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification(t('configSaved'), 'success');
                originalConfig = JSON.parse(JSON.stringify(currentConfig));
            } else {
                showNotification(result.error, 'error');
            }
        }
        
        function showSaveAsModal() {
            document.getElementById('saveAsName').value = currentConfigName + '_copy';
            document.getElementById('saveAsModal').classList.add('active');
        }
        
        async function saveAsConfig() {
            const name = document.getElementById('saveAsName').value;
            
            const response = await fetch(`/api/configs/${name}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(currentConfig)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification(`${t('configSavedAs')} "${name}"`, 'success');
                closeModal('saveAsModal');
                currentConfigName = name;
                loadConfigs();
            } else {
                showNotification(result.error, 'error');
            }
        }
        
        function showNewConfigModal() {
            document.getElementById('newConfigName').value = '';
            document.getElementById('newConfigModal').classList.add('active');
        }
        
        async function createNewConfig() {
            const name = document.getElementById('newConfigName').value;
            const base = document.getElementById('baseTemplate').value;
            
            let config = {};
            if (base !== 'empty') {
                const response = await fetch(`/api/configs/${base}`);
                config = await response.json();
            }
            
            const response = await fetch(`/api/configs/${name}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification(`${t('configCreated')} "${name}"`, 'success');
                closeModal('newConfigModal');
                loadConfig(name);
            } else {
                showNotification(result.error, 'error');
            }
        }
        
        function showImportModal() {
            document.getElementById('importName').value = '';
            document.getElementById('importContent').value = '';
            document.getElementById('importModal').classList.add('active');
        }
        
        async function importConfig() {
            const name = document.getElementById('importName').value;
            const content = document.getElementById('importContent').value;
            
            const response = await fetch('/api/configs/import', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, content})
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification(t('configImported'), 'success');
                closeModal('importModal');
                loadConfig(result.name);
            } else {
                showNotification(result.error, 'error');
            }
        }
        
        async function deleteConfig() {
            if (!confirm(`${t('confirmDelete')} "${currentConfigName}"?`)) return;
            
            const response = await fetch(`/api/configs/${currentConfigName}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification(t('configDeleted'), 'success');
                currentConfig = null;
                currentConfigName = null;
                document.getElementById('emptyState').style.display = 'block';
                document.getElementById('editorContent').style.display = 'none';
                loadConfigs();
            } else {
                showNotification(result.error, 'error');
            }
        }
        
        function resetConfig() {
            if (originalConfig) {
                currentConfig = JSON.parse(JSON.stringify(originalConfig));
                switchTab('basic');
                showNotification(t('configReset'), 'success');
            }
        }
        
        function showYamlPreview() {
            fetch(`/api/configs/${currentConfigName}/yaml`)
                .then(response => response.text())
                .then(yaml => {
                    document.getElementById('yamlPreviewContent').textContent = yaml;
                    document.getElementById('yamlPreviewModal').classList.add('active');
                });
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }
        
        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
        
        // Initialize
        applyTranslations();
        loadConfigs();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/configs')
def list_configs():
    return jsonify(manager.list_configs())


@app.route('/api/configs/<name>')
def get_config(name):
    config = manager.load_config(name)
    if config is None:
        return jsonify({'error': f'Config "{name}" not found'}), 404
    return jsonify(config)


@app.route('/api/configs/<name>/yaml')
def get_config_yaml(name):
    config = manager.load_config(name)
    if config is None:
        return 'Config not found', 404
    return yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False), 200, {'Content-Type': 'text/plain'}


@app.route('/api/configs/<name>', methods=['POST'])
def save_config(name):
    config = request.json
    result = manager.save_config(name, config, overwrite=True)
    return jsonify(result)


@app.route('/api/configs/<name>', methods=['PUT'])
def save_as_config(name):
    config = request.json
    result = manager.save_as_config(name, config)
    return jsonify(result)


@app.route('/api/configs/<name>', methods=['DELETE'])
def delete_config(name):
    result = manager.delete_config(name)
    return jsonify(result)


@app.route('/api/configs/import', methods=['POST'])
def import_config():
    data = request.json
    name = data.get('name')
    content = data.get('content')
    
    if not content:
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    try:
        config = yaml.safe_load(content)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Invalid YAML: {e}'}), 400
    
    if not name:
        name = 'imported_config'
    
    result = manager.save_as_config(name, config)
    if result['success']:
        result['name'] = name
    return jsonify(result)


@app.route('/api/schema')
def get_schema():
    return jsonify(manager.get_config_schema())


def run_server(host='127.0.0.1', port=5001, open_browser=True):
    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()
    
    print(f"[INFO] Format Manager Web UI starting at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    import sys
    
    host = '127.0.0.1'
    port = 5001
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    run_server(host, port)
