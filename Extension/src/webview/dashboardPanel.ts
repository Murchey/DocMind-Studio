import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

interface AgentSummary {
  name: string;
  description: string;
  path: string;
  skills: number;
}

interface WorkflowSummary {
  name: string;
  title: string;
  description: string;
  path: string;
  agents: string[];
}

interface ProjectSummary {
  name: string;
  path: string;
  agentCount: number;
  artifactCount: number;
  updatedAt: string;
  knowledgeBase?: KnowledgeBaseSummary;
  agents: AgentWorkspaceSummary[];
}

interface AgentWorkspaceSummary {
  name: string;
  path: string;
  folders: FolderSummary[];
}

interface FolderSummary {
  name: string;
  path: string;
  count: number;
}

interface KnowledgeBaseSummary {
  path: string;
  manifestPath?: string;
  docCount: number;
  keywordCount: number;
  conceptCount: number;
  documents: KnowledgeDocument[];
}

interface KnowledgeDocument {
  title: string;
  path?: string;
  sourceFile?: string;
}

interface ProgressStatus {
  exists: boolean;
  path?: string;
  project?: string;
  workflow?: string;
  agent?: string;
  status: string;
  phase?: string;
  message?: string;
  percent: number;
  updatedAt?: string;
  startedAt?: string;
  currentStep?: string;
  steps: ProgressStep[];
  outputs: ProgressOutput[];
  error?: string;
}

interface ProgressStep {
  id?: string;
  name: string;
  agent?: string;
  status: string;
  percent?: number;
  message?: string;
}

interface ProgressOutput {
  label: string;
  path: string;
  kind?: string;
}

const RESULT_FOLDERS = ['input', 'output', 'summary', 'parsed', 'validated'];

// 翻译字典
const translations = {
  en: {
    dashboard: 'Dashboard',
    progress: 'Progress',
    projects: 'Projects',
    agents: 'Agents',
    workflows: 'Workflows',
    knowledge: 'Knowledge Base',
    components: 'Components',
    resources: 'Resources',
    refresh: 'Refresh',
    workspace: 'Workspace',
    noActiveTask: 'No Active Task',
    waitingForProgress: 'Waiting for progress file. Default path: WORKSPACE/.docmind-progress.json',
    runWorkflowHint: 'Run a workflow from AGENTS.md to see live progress here.',
    noProjects: 'No Projects',
    runAgentsHint: 'Run AGENTS.md to create projects in the WORKSPACE directory.',
    noAgents: 'No Agents',
    noAgentsHint: 'No agents found in ComponentAgents directory.',
    noWorkflows: 'No Workflows',
    noWorkflowsHint: 'No workflow files found in Workflows directory.',
    noKnowledgeBase: 'No Knowledge Base',
    noKnowledgeBaseHint: 'No knowledge base found. Run a workflow to generate one.',
    project: 'Project',
    agent: 'Agent',
    updated: 'Updated',
    outputs: 'Outputs',
    open: 'Open',
    run: 'Run',
    openManifest: 'Open Manifest',
    agentsCount: 'agents',
    artifactsCount: 'artifacts',
    docsCount: 'docs',
    skillsCount: 'skills',
    documents: 'documents',
    keywords: 'keywords',
    concepts: 'concepts',
    justNow: 'just now',
    minutesAgo: 'm ago',
    hoursAgo: 'h ago',
    daysAgo: 'd ago',
  },
  zh: {
    dashboard: '仪表盘',
    progress: '进度',
    projects: '项目',
    agents: '智能体',
    workflows: '工作流',
    knowledge: '知识库',
    components: '组件',
    resources: '资源',
    refresh: '刷新',
    workspace: '工作区',
    noActiveTask: '暂无活动任务',
    waitingForProgress: '等待进度文件。默认路径：WORKSPACE/.docmind-progress.json',
    runWorkflowHint: '从 AGENTS.md 运行工作流以查看实时进度。',
    noProjects: '暂无项目',
    runAgentsHint: '运行 AGENTS.md 在 WORKSPACE 目录中创建项目。',
    noAgents: '暂无智能体',
    noAgentsHint: '在 ComponentAgents 目录中未找到智能体。',
    noWorkflows: '暂无工作流',
    noWorkflowsHint: '在 Workflows 目录中未找到工作流文件。',
    noKnowledgeBase: '暂无知识库',
    noKnowledgeBaseHint: '未找到知识库。运行工作流以生成知识库。',
    project: '项目',
    agent: '智能体',
    updated: '更新时间',
    outputs: '输出产物',
    open: '打开',
    run: '运行',
    openManifest: '打开清单',
    agentsCount: '个智能体',
    artifactsCount: '个产物',
    docsCount: '个文档',
    skillsCount: '个技能',
    documents: '个文档',
    keywords: '个关键词',
    concepts: '个概念',
    justNow: '刚刚',
    minutesAgo: '分钟前',
    hoursAgo: '小时前',
    daysAgo: '天前',
  }
};

type Language = 'en' | 'zh';

export class DashboardPanel {
  public static currentPanel: DashboardPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];
  private _currentView: string = 'progress';
  private _language: Language = 'zh';

  public static createOrShow(extensionUri: vscode.Uri, rootPath: string | undefined) {
    const column = vscode.ViewColumn.One;

    if (DashboardPanel.currentPanel) {
      DashboardPanel.currentPanel._panel.reveal(column);
      DashboardPanel.currentPanel._update(rootPath);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      'docmindDashboard',
      'DocMind Studio',
      column,
      {
        enableScripts: true,
        localResourceRoots: [extensionUri],
        retainContextWhenHidden: true
      }
    );

    DashboardPanel.currentPanel = new DashboardPanel(panel, rootPath);
  }

  public static refresh(rootPath: string | undefined) {
    DashboardPanel.currentPanel?._update(rootPath);
  }

  private constructor(panel: vscode.WebviewPanel, private rootPath: string | undefined) {
    this._panel = panel;
    this._update(rootPath);
    this._panel.webview.onDidReceiveMessage(message => this.handleMessage(message), null, this._disposables);
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }

  public dispose() {
    DashboardPanel.currentPanel = undefined;
    this._panel.dispose();
    while (this._disposables.length) {
      const d = this._disposables.pop();
      d?.dispose();
    }
  }

  private t(key: keyof typeof translations.en): string {
    return translations[this._language][key] || translations.en[key] || key;
  }

  private handleMessage(message: { type: string; path?: string; name?: string; view?: string; lang?: string }) {
    if (message.type === 'openPath' && message.path) {
      vscode.commands.executeCommand('docmind.openPath', message.path);
      return;
    }

    if (message.type === 'revealPath' && message.path) {
      vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(message.path));
      return;
    }

    if (message.type === 'runWorkflow' && message.name) {
      const workflow = this.scanWorkflows(this.rootPath).find(item => item.name === message.name);
      if (workflow) {
        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(workflow.path));
      }
      vscode.window.showInformationMessage(`DocMind workflow ready: ${message.name}. Follow AGENTS.md to dispatch it from the workspace.`);
      return;
    }

    if (message.type === 'editWorkflow' && message.name) {
      const workflow = this.scanWorkflows(this.rootPath).find(item => item.name === message.name);
      if (workflow) {
        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(workflow.path));
      }
      return;
    }

    if (message.type === 'newWorkflow') {
      if (this.rootPath) {
        const workflowsDir = path.join(this.rootPath, 'Workflows');
        if (!fs.existsSync(workflowsDir)) {
          fs.mkdirSync(workflowsDir, { recursive: true });
        }
        const templatePath = path.join(workflowsDir, 'NewWorkflow.md');
        const template = `# New Workflow\n\n## Description\n\nDescribe your workflow here.\n\n## Steps\n\n1. Step 1\n2. Step 2\n3. Step 3\n\n## Agents\n\nagents: []\n`;
        fs.writeFileSync(templatePath, template, 'utf-8');
        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(templatePath));
        this._update(this.rootPath);
      }
      return;
    }

    if (message.type === 'refresh') {
      this._update(this.rootPath);
      return;
    }

    if (message.type === 'navigate' && message.view) {
      this._currentView = message.view;
      this._update(this.rootPath);
      return;
    }

    if (message.type === 'switchLang' && message.lang) {
      this._language = message.lang as Language;
      this._update(this.rootPath);
      return;
    }
  }

  private _update(rootPath: string | undefined) {
    this.rootPath = rootPath;
    this._panel.webview.html = this._getHtml(rootPath);
  }

  private _getHtml(rootPath: string | undefined): string {
    const nonce = this.getNonce();
    const agents = this.scanAgents(rootPath);
    const workflows = this.scanWorkflows(rootPath);
    const projects = this.scanProjects(rootPath);
    const progress = this.scanProgress(rootPath);
    const artifactCount = projects.reduce((sum, project) => sum + project.artifactCount, 0);
    const latestProject = projects[0];
    const kbCount = projects.filter(project => project.knowledgeBase?.manifestPath).length;

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <title>DocMind Studio</title>
  <style>
    :root {
      --sidebar-width: 240px;
      --header-height: 48px;
      --transition-fast: 150ms ease;
      --transition-normal: 250ms ease;
      --radius-sm: 4px;
      --radius-md: 6px;
      --radius-lg: 8px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      line-height: 1.5;
      overflow: hidden;
    }

    .app {
      display: flex;
      height: 100vh;
      width: 100vw;
    }

    /* Sidebar */
    .sidebar {
      width: var(--sidebar-width);
      background: var(--vscode-sideBar-background);
      border-right: 1px solid var(--vscode-widget-border);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }

    .sidebar-header {
      height: var(--header-height);
      padding: 0 16px;
      display: flex;
      align-items: center;
      border-bottom: 1px solid var(--vscode-widget-border);
    }

    .logo {
      font-size: 14px;
      font-weight: 600;
      color: var(--vscode-foreground);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .logo-icon {
      width: 20px;
      height: 20px;
      background: var(--vscode-progressBar-background);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      color: white;
      font-weight: bold;
    }

    .nav {
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;
    }

    .nav-section {
      padding: 0 8px;
      margin-bottom: 16px;
    }

    .nav-section-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--vscode-descriptionForeground);
      padding: 8px 8px 4px;
      letter-spacing: 0.5px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: background var(--transition-fast);
      color: var(--vscode-foreground);
      text-decoration: none;
    }

    .nav-item:hover {
      background: var(--vscode-list-hoverBackground);
    }

    .nav-item.active {
      background: var(--vscode-list-activeSelectionBackground);
      color: var(--vscode-list-activeSelectionForeground);
    }

    .nav-item-icon {
      width: 16px;
      height: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      opacity: 0.8;
    }

    .nav-item-text {
      flex: 1;
      font-size: 13px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .nav-item-badge {
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 10px;
      background: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
    }

    /* Main Content */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .header {
      height: var(--header-height);
      padding: 0 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--vscode-widget-border);
      background: var(--vscode-editor-background);
    }

    .header-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--vscode-foreground);
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border: 1px solid var(--vscode-widget-border);
      border-radius: var(--radius-sm);
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      font-size: 12px;
      cursor: pointer;
      transition: all var(--transition-fast);
    }

    .btn:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }

    .btn-primary {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border-color: var(--vscode-button-background);
    }

    .btn-primary:hover {
      background: var(--vscode-button-hoverBackground);
    }

    .content {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
    }

    /* Cards */
    .card {
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-widget-border);
      border-radius: var(--radius-lg);
      overflow: hidden;
      margin-bottom: 16px;
    }

    .card-header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--vscode-widget-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .card-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--vscode-foreground);
    }

    .card-body {
      padding: 16px;
    }

    /* Progress Section */
    .progress-container {
      margin-bottom: 24px;
    }

    .progress-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }

    .progress-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--vscode-foreground);
    }

    .progress-status {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 500;
    }

    .status-idle { background: var(--vscode-descriptionForeground); color: var(--vscode-editor-background); }
    .status-running { background: var(--vscode-progressBar-background); color: white; }
    .status-completed { background: var(--vscode-testing-iconPassed); color: white; }
    .status-failed { background: var(--vscode-testing-iconFailed); color: white; }

    .progress-bar {
      height: 4px;
      background: var(--vscode-editorWidget-background);
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 16px;
    }

    .progress-fill {
      height: 100%;
      background: var(--vscode-progressBar-background);
      transition: width var(--transition-normal);
      border-radius: 2px;
    }

    .progress-info {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 16px;
    }

    .progress-info-item {
      text-align: center;
    }

    .progress-info-label {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      margin-bottom: 4px;
    }

    .progress-info-value {
      font-size: 13px;
      font-weight: 500;
      color: var(--vscode-foreground);
    }

    /* Steps */
    .steps-list {
      margin-top: 16px;
    }

    .step-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid var(--vscode-widget-border);
    }

    .step-item:last-child {
      border-bottom: none;
    }

    .step-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-top: 6px;
      flex-shrink: 0;
    }

    .step-pending { background: var(--vscode-descriptionForeground); }
    .step-running { background: var(--vscode-progressBar-background); }
    .step-completed { background: var(--vscode-testing-iconPassed); }
    .step-failed { background: var(--vscode-testing-iconFailed); }

    .step-content {
      flex: 1;
      min-width: 0;
    }

    .step-name {
      font-size: 13px;
      font-weight: 500;
      color: var(--vscode-foreground);
      margin-bottom: 4px;
    }

    .step-message {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .step-progress {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      margin-left: auto;
      flex-shrink: 0;
    }

    /* Outputs */
    .outputs-section {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--vscode-widget-border);
    }

    .outputs-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--vscode-descriptionForeground);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .output-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: var(--vscode-editorWidget-background);
      border-radius: var(--radius-sm);
      margin-bottom: 8px;
      cursor: pointer;
      transition: background var(--transition-fast);
    }

    .output-item:hover {
      background: var(--vscode-list-hoverBackground);
    }

    .output-icon {
      font-size: 14px;
      opacity: 0.7;
    }

    .output-label {
      flex: 1;
      font-size: 12px;
      color: var(--vscode-foreground);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Empty State */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
      text-align: center;
    }

    .empty-icon {
      font-size: 48px;
      margin-bottom: 16px;
      opacity: 0.3;
    }

    .empty-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--vscode-foreground);
      margin-bottom: 8px;
    }

    .empty-description {
      font-size: 13px;
      color: var(--vscode-descriptionForeground);
      max-width: 300px;
      line-height: 1.6;
    }

    /* List */
    .list {
      border: 1px solid var(--vscode-widget-border);
      border-radius: var(--radius-lg);
      overflow: hidden;
    }

    .list-item {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      border-bottom: 1px solid var(--vscode-widget-border);
      transition: background var(--transition-fast);
    }

    .list-item:last-child {
      border-bottom: none;
    }

    .list-item:hover {
      background: var(--vscode-list-hoverBackground);
    }

    .list-item-content {
      flex: 1;
      min-width: 0;
    }

    .list-item-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--vscode-foreground);
      margin-bottom: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .list-item-description {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .list-item-action {
      margin-left: 12px;
      flex-shrink: 0;
    }

    /* Tags */
    .tag {
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      background: var(--vscode-editorWidget-background);
      color: var(--vscode-descriptionForeground);
      margin-right: 6px;
      margin-bottom: 4px;
    }

    .tag-primary {
      background: var(--vscode-progressBar-background);
      color: white;
    }

    /* Grid */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }

    .grid-item {
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-widget-border);
      border-radius: var(--radius-lg);
      padding: 16px;
      transition: all var(--transition-fast);
    }

    .grid-item:hover {
      border-color: var(--vscode-focusBorder);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .grid-item-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }

    .grid-item-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--vscode-foreground);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .grid-item-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      background: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
    }

    .grid-item-content {
      margin-bottom: 12px;
    }

    .grid-item-description {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      line-height: 1.6;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .grid-item-footer {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .app {
        flex-direction: column;
      }

      .sidebar {
        width: 100%;
        height: auto;
        border-right: none;
        border-bottom: 1px solid var(--vscode-widget-border);
      }

      .nav {
        display: flex;
        overflow-x: auto;
        padding: 8px;
      }

      .nav-section {
        display: flex;
        gap: 4px;
        margin-bottom: 0;
      }

      .nav-section-title {
        display: none;
      }

      .nav-item {
        white-space: nowrap;
      }

      .progress-info {
        grid-template-columns: 1fr;
      }

      .grid {
        grid-template-columns: 1fr;
      }
    }

    /* Animations */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
      animation: fadeIn var(--transition-normal);
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    ::-webkit-scrollbar-track {
      background: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background: var(--vscode-scrollbarSlider-background);
      border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: var(--vscode-scrollbarSlider-hoverBackground);
    }
    .lang-switch {
      display: flex;
      gap: 4px;
      margin-left: auto;
    }

    .lang-btn {
      padding: 2px 8px;
      border: 1px solid var(--vscode-widget-border);
      border-radius: var(--radius-sm);
      background: transparent;
      color: var(--vscode-descriptionForeground);
      font-size: 11px;
      cursor: pointer;
      transition: all var(--transition-fast);
    }

    .lang-btn:hover {
      background: var(--vscode-list-hoverBackground);
    }

    .lang-btn.active {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border-color: var(--vscode-button-background);
    }
  </style>
</head>
<body>
  <div class="app">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">D</div>
          <span>DocMind</span>
        </div>
        <div class="lang-switch">
          <button class="lang-btn ${this._language === 'en' ? 'active' : ''}" data-action="switchLang" data-lang="en">EN</button>
          <button class="lang-btn ${this._language === 'zh' ? 'active' : ''}" data-action="switchLang" data-lang="zh">中</button>
        </div>
      </div>
      <nav class="nav">
        <div class="nav-section">
          <div class="nav-section-title">${this.t('dashboard')}</div>
          <div class="nav-item ${this._currentView === 'progress' ? 'active' : ''}" data-action="navigate" data-view="progress">
            <span class="nav-item-icon">⚡</span>
            <span class="nav-item-text">${this.t('progress')}</span>
            ${progress.exists ? `<span class="nav-item-badge">${progress.percent}%</span>` : ''}
          </div>
          <div class="nav-item ${this._currentView === 'projects' ? 'active' : ''}" data-action="navigate" data-view="projects">
            <span class="nav-item-icon">📁</span>
            <span class="nav-item-text">${this.t('projects')}</span>
            <span class="nav-item-badge">${projects.length}</span>
          </div>
        </div>
        <div class="nav-section">
          <div class="nav-section-title">${this.t('components')}</div>
          <div class="nav-item ${this._currentView === 'agents' ? 'active' : ''}" data-action="navigate" data-view="agents">
            <span class="nav-item-icon">🤖</span>
            <span class="nav-item-text">${this.t('agents')}</span>
            <span class="nav-item-badge">${agents.length}</span>
          </div>
          <div class="nav-item ${this._currentView === 'workflows' ? 'active' : ''}" data-action="navigate" data-view="workflows">
            <span class="nav-item-icon">🔄</span>
            <span class="nav-item-text">${this.t('workflows')}</span>
            <span class="nav-item-badge">${workflows.length}</span>
          </div>
        </div>
        <div class="nav-section">
          <div class="nav-section-title">${this.t('resources')}</div>
          <div class="nav-item ${this._currentView === 'knowledge' ? 'active' : ''}" data-action="navigate" data-view="knowledge">
            <span class="nav-item-icon">📚</span>
            <span class="nav-item-text">${this.t('knowledge')}</span>
            <span class="nav-item-badge">${kbCount}</span>
          </div>
        </div>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="main">
      <header class="header">
        <h1 class="header-title">${this.getHeaderTitle()}</h1>
        <div class="header-actions">
          <button class="btn" data-action="refresh">
            <span>↻</span> ${this.t('refresh')}
          </button>
          ${rootPath ? `<button class="btn btn-primary" data-action="reveal" data-path="${this.escapeAttr(path.join(rootPath, 'WORKSPACE'))}">
            <span>📂</span> ${this.t('workspace')}
          </button>` : ''}
        </div>
      </header>

      <div class="content">
        ${this.renderCurrentView(rootPath, progress, projects, agents, workflows, latestProject)}
      </div>
    </main>
  </div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();

    document.addEventListener('click', (event) => {
      const target = event.target.closest('[data-action]');
      if (!target) return;

      const action = target.dataset.action;

      if (action === 'navigate') {
        vscode.postMessage({ type: 'navigate', view: target.dataset.view });
        return;
      }

      if (action === 'open') {
        vscode.postMessage({ type: 'openPath', path: target.dataset.path });
        return;
      }

      if (action === 'reveal') {
        vscode.postMessage({ type: 'revealPath', path: target.dataset.path });
        return;
      }

      if (action === 'workflow') {
        vscode.postMessage({ type: 'runWorkflow', name: target.dataset.name });
        return;
      }

      if (action === 'editWorkflow') {
        vscode.postMessage({ type: 'editWorkflow', name: target.dataset.name });
        return;
      }

      if (action === 'newWorkflow') {
        vscode.postMessage({ type: 'newWorkflow' });
        return;
      }

      if (action === 'refresh') {
        vscode.postMessage({ type: 'refresh' });
        return;
      }

      if (action === 'switchLang') {
        vscode.postMessage({ type: 'switchLang', lang: target.dataset.lang });
        return;
      }
    });
  </script>
</body>
</html>`;
  }

  private getHeaderTitle(): string {
    const titles: Record<string, keyof typeof translations.en> = {
      progress: 'progress',
      projects: 'projects',
      agents: 'agents',
      workflows: 'workflows',
      knowledge: 'knowledge'
    };
    const key = titles[this._currentView] || 'dashboard';
    return this.t(key);
  }

  private renderCurrentView(
    rootPath: string | undefined,
    progress: ProgressStatus,
    projects: ProjectSummary[],
    agents: AgentSummary[],
    workflows: WorkflowSummary[],
    latestProject: ProjectSummary | undefined
  ): string {
    switch (this._currentView) {
      case 'progress':
        return this.renderProgressView(progress, projects);
      case 'projects':
        return this.renderProjectsView(projects);
      case 'agents':
        return this.renderAgentsView(agents);
      case 'workflows':
        return this.renderWorkflowsView(workflows);
      case 'knowledge':
        return this.renderKnowledgeView(latestProject);
      default:
        return this.renderProgressView(progress, projects);
    }
  }

  private renderProgressView(progress: ProgressStatus, projects: ProjectSummary[]): string {
    if (!progress.exists) {
      return `
        <div class="empty-state fade-in">
          <div class="empty-icon">⏳</div>
          <div class="empty-title">${this.t('noActiveTask')}</div>
          <div class="empty-description">
            ${this.t('waitingForProgress')}
            <br><br>
            ${this.t('runWorkflowHint')}
          </div>
        </div>
      `;
    }

    const statusClass = this.statusClass(progress.status);
    return `
      <div class="progress-container fade-in">
        <div class="progress-header">
          <div class="progress-title">${this.escapeHtml(progress.workflow || progress.project || 'DocMind Task')}</div>
          <span class="progress-status status-${statusClass}">${this.escapeHtml(progress.status)}</span>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" style="width: ${progress.percent}%"></div>
        </div>

        <div class="progress-info">
          <div class="progress-info-item">
            <div class="progress-info-label">${this.t('project')}</div>
            <div class="progress-info-value">${this.escapeHtml(progress.project || '-')}</div>
          </div>
          <div class="progress-info-item">
            <div class="progress-info-label">${this.t('agent')}</div>
            <div class="progress-info-value">${this.escapeHtml(progress.agent || '-')}</div>
          </div>
          <div class="progress-info-item">
            <div class="progress-info-label">${this.t('updated')}</div>
            <div class="progress-info-value">${this.escapeHtml(progress.updatedAt || '-')}</div>
          </div>
        </div>

        ${progress.message ? `<div style="margin-bottom: 16px; font-size: 13px; color: var(--vscode-descriptionForeground);">${this.escapeHtml(progress.message)}</div>` : ''}

        ${progress.steps.length ? `
          <div class="steps-list">
            ${progress.steps.map(step => this.renderStepItem(step)).join('')}
          </div>
        ` : ''}

        ${progress.outputs.length ? `
          <div class="outputs-section">
            <div class="outputs-title">${this.t('outputs')}</div>
            ${progress.outputs.map(output => `
              <div class="output-item" data-action="open" data-path="${this.escapeAttr(output.path)}">
                <span class="output-icon">📄</span>
                <span class="output-label">${this.escapeHtml(output.label)}</span>
              </div>
            `).join('')}
          </div>
        ` : ''}

        ${progress.error ? `
          <div style="margin-top: 16px; padding: 12px; background: var(--vscode-inputValidation-errorBackground); border: 1px solid var(--vscode-inputValidation-errorBorder); border-radius: var(--radius-sm); font-size: 12px; color: var(--vscode-errorForeground);">
            ${this.escapeHtml(progress.error)}
          </div>
        ` : ''}
      </div>
    `;
  }

  private renderStepItem(step: ProgressStep): string {
    const statusClass = this.stepStatusClass(step.status);
    return `
      <div class="step-item">
        <div class="step-indicator step-${statusClass}"></div>
        <div class="step-content">
          <div class="step-name">${this.escapeHtml(step.name)}</div>
          <div class="step-message">${this.escapeHtml(step.message || step.agent || step.status)}</div>
        </div>
        <div class="step-progress">${typeof step.percent === 'number' ? `${step.percent}%` : step.status}</div>
      </div>
    `;
  }

  private renderProjectsView(projects: ProjectSummary[]): string {
    if (!projects.length) {
      return `
        <div class="empty-state fade-in">
          <div class="empty-icon">📁</div>
          <div class="empty-title">${this.t('noProjects')}</div>
          <div class="empty-description">${this.t('runAgentsHint')}</div>
        </div>
      `;
    }

    return `
      <div class="grid fade-in">
        ${projects.map(project => `
          <div class="grid-item" data-action="reveal" data-path="${this.escapeAttr(project.path)}">
            <div class="grid-item-header">
              <div class="grid-item-title">${this.escapeHtml(project.name)}</div>
              ${project.knowledgeBase?.manifestPath ? '<span class="grid-item-badge">KB</span>' : ''}
            </div>
            <div class="grid-item-content">
              <div class="grid-item-description">
                ${project.agentCount} ${this.t('agentsCount')} · ${project.artifactCount} ${this.t('artifactsCount')}
                ${project.knowledgeBase ? ` · ${project.knowledgeBase.docCount} ${this.t('docsCount')}` : ''}
              </div>
            </div>
            <div class="grid-item-footer">
              <span class="tag">${project.updatedAt}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  private renderAgentsView(agents: AgentSummary[]): string {
    if (!agents.length) {
      return `
        <div class="empty-state fade-in">
          <div class="empty-icon">🤖</div>
          <div class="empty-title">${this.t('noAgents')}</div>
          <div class="empty-description">${this.t('noAgentsHint')}</div>
        </div>
      `;
    }

    return `
      <div class="list fade-in">
        ${agents.map(agent => `
          <div class="list-item" data-action="open" data-path="${this.escapeAttr(agent.path)}">
            <div class="list-item-content">
              <div class="list-item-title">${this.escapeHtml(agent.name)}</div>
              <div class="list-item-description">${this.escapeHtml(agent.description)} · ${agent.skills} ${this.t('skillsCount')}</div>
            </div>
            <div class="list-item-action">
              <button class="btn" data-action="open" data-path="${this.escapeAttr(agent.path)}">${this.t('open')}</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  private renderWorkflowsView(workflows: WorkflowSummary[]): string {
    const t = this.t.bind(this);

    return `
      <div class="fade-in">
        <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
          <button class="btn btn-primary" data-action="newWorkflow">+ New</button>
        </div>
        ${!workflows.length ? `
          <div class="empty-state">
            <div class="empty-icon">🔄</div>
            <div class="empty-title">${t('noWorkflows')}</div>
            <div class="empty-description">${t('noWorkflowsHint')}</div>
          </div>
        ` : `
          <div class="grid">
            ${workflows.map(workflow => `
              <div class="grid-item">
                <div class="grid-item-header">
                  <div class="grid-item-title">${this.escapeHtml(workflow.title)}</div>
                  <button class="btn" data-action="editWorkflow" data-name="${this.escapeAttr(workflow.name)}">${t('open')}</button>
                </div>
                <div class="grid-item-content">
                  <div class="grid-item-description">${this.escapeHtml(workflow.description)}</div>
                </div>
                <div class="grid-item-footer">
                  ${workflow.agents.map(agent => `<span class="tag">${this.escapeHtml(agent)}</span>`).join('')}
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </div>
    `;
  }

  private renderKnowledgeView(latestProject: ProjectSummary | undefined): string {
    if (!latestProject?.knowledgeBase) {
      return `
        <div class="empty-state fade-in">
          <div class="empty-icon">📚</div>
          <div class="empty-title">${this.t('noKnowledgeBase')}</div>
          <div class="empty-description">${this.t('noKnowledgeBaseHint')}</div>
        </div>
      `;
    }

    const kb = latestProject.knowledgeBase;
    return `
      <div class="card fade-in">
        <div class="card-header">
          <div class="card-title">${this.escapeHtml(latestProject.name)}</div>
          <button class="btn" data-action="open" data-path="${this.escapeAttr(kb.manifestPath || kb.path)}">${this.t('openManifest')}</button>
        </div>
        <div class="card-body">
          <div style="margin-bottom: 16px; font-size: 13px; color: var(--vscode-descriptionForeground);">
            ${kb.docCount} ${this.t('documents')} · ${kb.keywordCount} ${this.t('keywords')} · ${kb.conceptCount} ${this.t('concepts')}
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${kb.documents.slice(0, 12).map(doc => doc.path
              ? `<span class="tag" data-action="open" data-path="${this.escapeAttr(doc.path)}" style="cursor: pointer;">${this.escapeHtml(doc.title)}</span>`
              : `<span class="tag">${this.escapeHtml(doc.title)}</span>`
            ).join('')}
          </div>
        </div>
      </div>
    `;
  }

  private statusClass(status: string): string {
    const normalized = status.toLowerCase();
    if (['running', 'processing', 'in_progress', 'active'].includes(normalized)) {
      return 'running';
    }
    if (['completed', 'success', 'done', 'ready'].includes(normalized)) {
      return 'completed';
    }
    if (['failed', 'error', 'cancelled'].includes(normalized)) {
      return 'failed';
    }
    return 'idle';
  }

  private stepStatusClass(status: string): string {
    const normalized = status.toLowerCase();
    if (['running', 'processing', 'in_progress', 'active'].includes(normalized)) {
      return 'running';
    }
    if (['completed', 'success', 'done', 'ready'].includes(normalized)) {
      return 'completed';
    }
    if (['failed', 'error', 'cancelled'].includes(normalized)) {
      return 'failed';
    }
    return 'pending';
  }

  private scanProgress(rootPath: string | undefined): ProgressStatus {
    const emptyStatus: ProgressStatus = {
      exists: false,
      status: 'idle',
      percent: 0,
      steps: [],
      outputs: []
    };

    if (!rootPath) {
      return emptyStatus;
    }

    const progressPath = this.findProgressFile(rootPath);
    if (!progressPath) {
      return emptyStatus;
    }

    try {
      const raw = JSON.parse(this.readText(progressPath)) as Record<string, unknown>;
      const current = this.asRecord(raw.current_task) || this.asRecord(raw.currentTask) || raw;
      const status = this.asString(current.status) || this.asString(raw.status) || 'running';
      const steps = this.normalizeSteps(raw.steps || raw.stages || raw.tasks);
      const outputs = this.normalizeOutputs(raw.outputs || raw.artifacts || raw.files, rootPath);

      return {
        exists: true,
        path: progressPath,
        project: this.asString(current.project) || this.asString(raw.project) || this.asString(raw.project_name),
        workflow: this.asString(current.workflow) || this.asString(raw.workflow),
        agent: this.asString(current.agent) || this.asString(raw.agent),
        status,
        phase: this.asString(current.phase) || this.asString(raw.phase),
        message: this.asString(current.message) || this.asString(raw.message),
        percent: this.clampPercent(this.asNumber(current.percent) ?? this.asNumber(current.progress) ?? this.asNumber(raw.percent) ?? this.asNumber(raw.progress) ?? this.estimatePercent(status, steps)),
        updatedAt: this.asString(raw.updated_at) || this.asString(raw.updatedAt),
        startedAt: this.asString(raw.started_at) || this.asString(raw.startedAt),
        currentStep: this.asString(current.step) || this.asString(raw.current_step) || this.asString(raw.currentStep),
        steps,
        outputs,
        error: this.asString(raw.error) || this.asString(current.error)
      };
    } catch (error) {
      return {
        exists: true,
        path: progressPath,
        status: 'invalid',
        percent: 0,
        steps: [],
        outputs: [],
        error: error instanceof Error ? error.message : 'Progress JSON parse failed'
      };
    }
  }

  private findProgressFile(rootPath: string): string | undefined {
    const configured = vscode.workspace.getConfiguration('docmind').get<string>('progressFile') || 'WORKSPACE/.docmind-progress.json';
    const candidates = [
      configured,
      'WORKSPACE/.docmind-progress.json',
      'WORKSPACE/progress.json',
      '.docmind/progress.json',
      'docmind-progress.json'
    ];

    for (const candidate of candidates) {
      const fullPath = path.isAbsolute(candidate) ? candidate : path.join(rootPath, candidate);
      if (fs.existsSync(fullPath)) {
        return fullPath;
      }
    }

    const workspacePath = path.join(rootPath, 'WORKSPACE');
    return this.findFirstProgressFile(workspacePath, 3);
  }

  private findFirstProgressFile(dirPath: string, depth: number): string | undefined {
    if (depth < 0 || !fs.existsSync(dirPath)) {
      return undefined;
    }

    for (const entry of this.readDirEntries(dirPath)) {
      const fullPath = path.join(dirPath, entry.name);
      if (entry.isFile() && /progress|status|task/i.test(entry.name) && entry.name.endsWith('.json')) {
        return fullPath;
      }
    }

    for (const entry of this.readDirEntries(dirPath)) {
      if (entry.isDirectory()) {
        const match = this.findFirstProgressFile(path.join(dirPath, entry.name), depth - 1);
        if (match) {
          return match;
        }
      }
    }

    return undefined;
  }

  private normalizeSteps(value: unknown): ProgressStep[] {
    if (!Array.isArray(value)) {
      return [];
    }

    return value.map((item, index) => {
      const record = this.asRecord(item) || {};
      return {
        id: this.asString(record.id),
        name: this.asString(record.name) || this.asString(record.title) || this.asString(record.step) || `Step ${index + 1}`,
        agent: this.asString(record.agent),
        status: this.asString(record.status) || 'pending',
        percent: this.asNumber(record.percent) ?? this.asNumber(record.progress),
        message: this.asString(record.message) || this.asString(record.detail)
      };
    });
  }

  private normalizeOutputs(value: unknown, rootPath: string): ProgressOutput[] {
    if (!Array.isArray(value)) {
      return [];
    }

    return value.map(item => {
      if (typeof item === 'string') {
        return {
          label: path.basename(item),
          path: this.resolveWorkspacePath(item, rootPath)
        };
      }

      const record = this.asRecord(item) || {};
      const filePath = this.asString(record.path) || this.asString(record.file) || this.asString(record.href) || '';
      return {
        label: this.asString(record.label) || this.asString(record.name) || path.basename(filePath) || 'Output',
        path: this.resolveWorkspacePath(filePath, rootPath),
        kind: this.asString(record.kind) || this.asString(record.type)
      };
    }).filter(output => output.path);
  }

  private estimatePercent(status: string, steps: ProgressStep[]): number {
    const normalized = status.toLowerCase();
    if (['completed', 'success', 'done', 'ready'].includes(normalized)) {
      return 100;
    }
    if (!steps.length) {
      return ['running', 'processing', 'in_progress', 'active'].includes(normalized) ? 1 : 0;
    }

    const completed = steps.filter(step => ['completed', 'success', 'done'].includes(step.status.toLowerCase())).length;
    return Math.round((completed / steps.length) * 100);
  }

  private scanAgents(rootPath: string | undefined): AgentSummary[] {
    if (!rootPath) {
      return [];
    }

    const agentsDir = path.join(rootPath, 'ComponentAgents');
    if (!fs.existsSync(agentsDir)) {
      return [];
    }

    return this.readDirs(agentsDir).map(name => {
      const agentPath = path.join(agentsDir, name, 'AGENT.md');
      if (!fs.existsSync(agentPath)) {
        return undefined;
      }

      const content = this.readText(agentPath);
      const descMatch = content.match(/description:\s*(.+)/);
      const heading = content.split(/\r?\n/).find(line => line.startsWith('# '));
      return {
        name,
        description: descMatch?.[1]?.trim() || heading?.replace(/^#\s*/, '').trim() || 'Agent',
        path: agentPath,
        skills: this.countSkills(path.dirname(agentPath))
      };
    }).filter((agent): agent is AgentSummary => Boolean(agent));
  }

  private scanWorkflows(rootPath: string | undefined): WorkflowSummary[] {
    if (!rootPath) {
      return [];
    }

    const workflowsDir = path.join(rootPath, 'Workflows');
    if (!fs.existsSync(workflowsDir)) {
      return [];
    }

    return this.readFiles(workflowsDir)
      .filter(file => file.endsWith('Workflow.md'))
      .map(file => {
        const fullPath = path.join(workflowsDir, file);
        const content = this.readText(fullPath);
        const lines = content.split(/\r?\n/);
        const title = lines.find(line => line.startsWith('# '))?.replace(/^#\s*/, '').trim() || file.replace('.md', '');
        const description = lines.find(line => line.trim() && !line.startsWith('#') && !line.startsWith('-'))?.trim() || 'Workflow';
        return {
          name: file.replace('.md', ''),
          title,
          description,
          path: fullPath,
          agents: this.extractAgents(content)
        };
      });
  }

  private scanProjects(rootPath: string | undefined): ProjectSummary[] {
    if (!rootPath) {
      return [];
    }

    const workspacePath = path.join(rootPath, 'WORKSPACE');
    if (!fs.existsSync(workspacePath)) {
      return [];
    }

    return this.readDirs(workspacePath)
      .map(projectName => {
        const projectPath = path.join(workspacePath, projectName);
        const agents = this.scanAgentWorkspaces(projectPath);
        return {
          name: projectName,
          path: projectPath,
          agentCount: agents.length,
          artifactCount: agents.reduce((sum, agent) => sum + agent.folders.reduce((folderSum, folder) => folderSum + folder.count, 0), 0),
          updatedAt: this.formatUpdated(projectPath),
          knowledgeBase: this.scanKnowledgeBase(projectPath),
          agents
        };
      })
      .sort((a, b) => this.getMtimeMs(b.path) - this.getMtimeMs(a.path));
  }

  private scanAgentWorkspaces(projectPath: string): AgentWorkspaceSummary[] {
    return this.readDirs(projectPath)
      .filter(name => name !== 'knowledge-base')
      .map(name => {
        const agentPath = path.join(projectPath, name);
        const folders = RESULT_FOLDERS
          .map(folder => {
            const folderPath = path.join(agentPath, folder);
            if (!fs.existsSync(folderPath)) {
              return undefined;
            }
            return {
              name: folder,
              path: folderPath,
              count: this.countFiles(folderPath)
            };
          })
          .filter((folder): folder is FolderSummary => Boolean(folder));

        return {
          name,
          path: agentPath,
          folders
        };
      });
  }

  private scanKnowledgeBase(projectPath: string): KnowledgeBaseSummary | undefined {
    const kbPath = path.join(projectPath, 'knowledge-base');
    if (!fs.existsSync(kbPath)) {
      return undefined;
    }

    const manifestPath = path.join(kbPath, 'kb-manifest.json');
    let documents: KnowledgeDocument[] = [];
    let keywordCount = 0;
    let conceptCount = 0;

    if (fs.existsSync(manifestPath)) {
      try {
        const manifest = JSON.parse(this.readText(manifestPath));
        documents = (manifest.documents || []).map((doc: Record<string, unknown>) => ({
          title: this.asString(doc.title) || 'Document',
          path: this.asString(doc.path),
          sourceFile: this.asString(doc.source_file)
        }));
        keywordCount = Array.isArray(manifest.keywords) ? manifest.keywords.length : 0;
        conceptCount = Array.isArray(manifest.concepts) ? manifest.concepts.length : 0;
      } catch {
        // Ignore parse errors
      }
    }

    return {
      path: kbPath,
      manifestPath: fs.existsSync(manifestPath) ? manifestPath : undefined,
      docCount: documents.length,
      keywordCount,
      conceptCount,
      documents
    };
  }

  private countSkills(agentPath: string): number {
    const skillsDir = path.join(agentPath, 'SKILLS');
    if (!fs.existsSync(skillsDir)) {
      return 0;
    }
    return this.readDirs(skillsDir).length;
  }

  private countFiles(dirPath: string): number {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }
    let count = 0;
    for (const entry of this.readDirEntries(dirPath)) {
      if (entry.isFile()) {
        count++;
      } else if (entry.isDirectory()) {
        count += this.countFiles(path.join(dirPath, entry.name));
      }
    }
    return count;
  }

  private extractAgents(content: string): string[] {
    const agents: string[] = [];
    const lines = content.split(/\r?\n/);
    for (const line of lines) {
      const match = line.match(/agent[s]?:\s*\[([^\]]+)\]/i);
      if (match) {
        const agentList = match[1].split(',').map(a => a.trim().replace(/['"]/g, ''));
        agents.push(...agentList);
      }
    }
    return [...new Set(agents)];
  }

  private formatUpdated(filePath: string): string {
    try {
      const stats = fs.statSync(filePath);
      const now = new Date();
      const diff = now.getTime() - stats.mtime.getTime();
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);

      if (minutes < 1) return 'just now';
      if (minutes < 60) return `${minutes}m ago`;
      if (hours < 24) return `${hours}h ago`;
      if (days < 7) return `${days}d ago`;
      return stats.mtime.toLocaleDateString();
    } catch {
      return 'unknown';
    }
  }

  private getMtimeMs(filePath: string): number {
    try {
      return fs.statSync(filePath).mtime.getTime();
    } catch {
      return 0;
    }
  }

  private readText(filePath: string): string {
    try {
      return fs.readFileSync(filePath, 'utf-8');
    } catch {
      return '';
    }
  }

  private readDirs(dirPath: string): string[] {
    try {
      return fs.readdirSync(dirPath, { withFileTypes: true })
        .filter(entry => entry.isDirectory())
        .map(entry => entry.name)
        .sort();
    } catch {
      return [];
    }
  }

  private readFiles(dirPath: string): string[] {
    try {
      return fs.readdirSync(dirPath, { withFileTypes: true })
        .filter(entry => entry.isFile())
        .map(entry => entry.name)
        .sort();
    } catch {
      return [];
    }
  }

  private readDirEntries(dirPath: string): fs.Dirent[] {
    try {
      return fs.readdirSync(dirPath, { withFileTypes: true });
    } catch {
      return [];
    }
  }

  private resolveWorkspacePath(filePath: string, rootPath: string): string {
    if (path.isAbsolute(filePath)) {
      return filePath;
    }
    return path.join(rootPath, filePath);
  }

  private clampPercent(value: number): number {
    return Math.max(0, Math.min(100, Math.round(value)));
  }

  private asString(value: unknown): string | undefined {
    return typeof value === 'string' ? value : undefined;
  }

  private asNumber(value: unknown): number | undefined {
    return typeof value === 'number' ? value : undefined;
  }

  private asRecord(value: unknown): Record<string, unknown> | undefined {
    return typeof value === 'object' && value !== null ? value as Record<string, unknown> : undefined;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  private escapeAttr(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  private getNonce(): string {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
      text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
  }
}
