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

export class DashboardPanel {
  public static currentPanel: DashboardPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];

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
        localResourceRoots: [extensionUri]
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

  private handleMessage(message: { type: string; path?: string; name?: string }) {
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

    if (message.type === 'refresh') {
      this._update(this.rootPath);
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
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
    }
    button { font: inherit; }
    .shell {
      min-height: 100vh;
      padding: 26px;
      background:
        linear-gradient(180deg, color-mix(in srgb, var(--vscode-sideBar-background) 42%, transparent), transparent 260px),
        var(--vscode-editor-background);
    }
    .topbar {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 22px;
    }
    .eyebrow {
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
      margin-bottom: 7px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      line-height: 1.16;
      font-weight: 680;
      letter-spacing: 0;
    }
    .subtitle {
      max-width: 780px;
      margin: 9px 0 0;
      color: var(--vscode-descriptionForeground);
      line-height: 1.6;
    }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .button {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 30px;
      border: 1px solid var(--vscode-button-border, transparent);
      border-radius: 6px;
      padding: 5px 11px;
      color: var(--vscode-button-foreground);
      background: var(--vscode-button-background);
      cursor: pointer;
    }
    .button.secondary {
      color: var(--vscode-foreground);
      background: var(--vscode-button-secondaryBackground);
      border-color: var(--vscode-widget-border);
    }
    .button:hover { background: var(--vscode-button-hoverBackground); }
    .button.secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }
    .metric {
      min-height: 88px;
      border: 1px solid var(--vscode-widget-border);
      border-radius: 8px;
      padding: 14px;
      background: color-mix(in srgb, var(--vscode-sideBar-background) 78%, transparent);
    }
    .metric-value {
      font-size: 25px;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 8px;
    }
    .metric-label {
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(320px, .75fr);
      gap: 16px;
    }
    .section {
      margin-top: 16px;
    }
    .section:first-child { margin-top: 0; }
    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 9px;
    }
    h2 {
      margin: 0;
      font-size: 13px;
      font-weight: 650;
      letter-spacing: 0;
      text-transform: uppercase;
      color: var(--vscode-descriptionForeground);
    }
    .count {
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(245px, 1fr));
      gap: 10px;
    }
    .card {
      border: 1px solid var(--vscode-widget-border);
      border-radius: 8px;
      background: var(--vscode-sideBar-background);
      padding: 13px;
      overflow: hidden;
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
    }
    .title {
      min-width: 0;
      font-weight: 650;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .desc {
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
      line-height: 1.5;
    }
    .tag-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .tag {
      border: 1px solid var(--vscode-widget-border);
      border-radius: 999px;
      padding: 2px 8px;
      color: var(--vscode-descriptionForeground);
      background: color-mix(in srgb, var(--vscode-editor-background) 80%, transparent);
      font-size: 11px;
    }
    .status {
      flex: 0 0 auto;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 11px;
      color: var(--vscode-testing-iconPassed);
      background: color-mix(in srgb, var(--vscode-testing-iconPassed) 14%, transparent);
    }
    .status.running {
      color: var(--vscode-charts-blue);
      background: color-mix(in srgb, var(--vscode-charts-blue) 14%, transparent);
    }
    .status.failed {
      color: var(--vscode-testing-iconFailed);
      background: color-mix(in srgb, var(--vscode-testing-iconFailed) 14%, transparent);
    }
    .progress-card { padding: 0; }
    .progress-head {
      padding: 15px;
      border-bottom: 1px solid var(--vscode-widget-border);
    }
    .progress-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }
    .progress-bar {
      height: 8px;
      overflow: hidden;
      border-radius: 999px;
      background: var(--vscode-editorWidget-background);
      border: 1px solid var(--vscode-widget-border);
    }
    .progress-fill {
      width: var(--progress);
      height: 100%;
      background: var(--vscode-progressBar-background);
    }
    .progress-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .progress-kv {
      border: 1px solid var(--vscode-widget-border);
      border-radius: 6px;
      padding: 8px;
      min-width: 0;
      background: color-mix(in srgb, var(--vscode-editor-background) 70%, transparent);
    }
    .progress-kv-label {
      color: var(--vscode-descriptionForeground);
      font-size: 11px;
      margin-bottom: 4px;
    }
    .progress-kv-value {
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .steps { padding: 7px 0; }
    .step {
      display: grid;
      grid-template-columns: 18px minmax(0, 1fr) auto;
      gap: 9px;
      align-items: start;
      padding: 8px 15px;
      border-top: 1px solid color-mix(in srgb, var(--vscode-widget-border) 62%, transparent);
    }
    .step:first-child { border-top: 0; }
    .dot {
      width: 9px;
      height: 9px;
      margin-top: 5px;
      border-radius: 999px;
      background: var(--vscode-descriptionForeground);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--vscode-descriptionForeground) 14%, transparent);
    }
    .dot.running {
      background: var(--vscode-charts-blue);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--vscode-charts-blue) 16%, transparent);
    }
    .dot.completed {
      background: var(--vscode-testing-iconPassed);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--vscode-testing-iconPassed) 16%, transparent);
    }
    .dot.failed {
      background: var(--vscode-testing-iconFailed);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--vscode-testing-iconFailed) 16%, transparent);
    }
    .list {
      border: 1px solid var(--vscode-widget-border);
      border-radius: 8px;
      overflow: hidden;
      background: var(--vscode-sideBar-background);
    }
    .row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 12px 13px;
      border-top: 1px solid var(--vscode-widget-border);
    }
    .row:first-child { border-top: 0; }
    .row-main { min-width: 0; }
    .row-title {
      font-weight: 620;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 3px;
    }
    .row-sub {
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .icon-button {
      width: 28px;
      height: 28px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--vscode-widget-border);
      border-radius: 6px;
      color: var(--vscode-foreground);
      background: transparent;
      cursor: pointer;
    }
    .icon-button:hover { background: var(--vscode-toolbar-hoverBackground); }
    .empty {
      border: 1px dashed var(--vscode-widget-border);
      border-radius: 8px;
      padding: 18px;
      color: var(--vscode-descriptionForeground);
      background: color-mix(in srgb, var(--vscode-sideBar-background) 52%, transparent);
    }
    .project-card { padding: 0; }
    .project-head {
      padding: 14px;
      border-bottom: 1px solid var(--vscode-widget-border);
    }
    .project-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 10px;
    }
    .agent-lines { padding: 5px 0; }
    .agent-line {
      display: grid;
      grid-template-columns: minmax(0, 120px) minmax(0, 1fr);
      gap: 10px;
      padding: 8px 14px;
      border-top: 1px solid color-mix(in srgb, var(--vscode-widget-border) 62%, transparent);
    }
    .agent-line:first-child { border-top: 0; }
    .folder-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-width: 0;
    }
    .folder-pill {
      border-radius: 5px;
      padding: 2px 7px;
      background: var(--vscode-editorWidget-background);
      color: var(--vscode-descriptionForeground);
      font-size: 11px;
      cursor: pointer;
    }
    .folder-pill:hover { color: var(--vscode-foreground); }
    @media (max-width: 900px) {
      .shell { padding: 18px; }
      .topbar { flex-direction: column; }
      .actions { justify-content: flex-start; }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .layout { grid-template-columns: 1fr; }
      .agent-line { grid-template-columns: 1fr; }
      .progress-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div>
        <div class="eyebrow">DocMind Studio</div>
        <h1>成果与智能体工作流管理台</h1>
        <p class="subtitle">${rootPath ? `当前工作区：${this.escapeHtml(rootPath)}` : '请先打开 DocMind-Studio 项目根目录。'}</p>
      </div>
      <div class="actions">
        <button class="button secondary" data-action="refresh" title="Refresh">↻ 刷新</button>
        ${rootPath ? `<button class="button" data-action="reveal" data-path="${this.escapeAttr(path.join(rootPath, 'WORKSPACE'))}" title="Reveal Workspace">□ WORKSPACE</button>` : ''}
      </div>
    </header>

    <section class="metrics">
      ${this.metric('Agents', agents.length)}
      ${this.metric('Workflows', workflows.length)}
      ${this.metric('Projects', projects.length)}
      ${this.metric('Progress', progress.exists ? progress.percent : 0, '%')}
    </section>

    <div class="layout">
      <div>
        <section class="section">
          <div class="section-title">
            <h2>Live Progress</h2>
            <span class="count">${progress.exists ? this.escapeHtml(progress.status) : 'waiting'}</span>
          </div>
          ${this.progressPanel(progress)}
        </section>

        <section class="section">
          <div class="section-title">
            <h2>Workspace Projects</h2>
            <span class="count">${projects.length} projects · ${artifactCount || kbCount} artifacts</span>
          </div>
          ${projects.length ? `<div class="grid">${projects.map(project => this.projectCard(project)).join('')}</div>` : this.empty('还没有生成成果。运行 AGENTS.md 调度后，项目会出现在 WORKSPACE 下。')}
        </section>

        <section class="section">
          <div class="section-title">
            <h2>Workflows</h2>
            <span class="count">${workflows.length} workflows</span>
          </div>
          ${workflows.length ? `<div class="grid">${workflows.map(workflow => this.workflowCard(workflow)).join('')}</div>` : this.empty('没有发现 Workflows/*.md。')}
        </section>
      </div>

      <aside>
        <section class="section">
          <div class="section-title">
            <h2>Agents</h2>
            <span class="count">${agents.length} agents</span>
          </div>
          ${agents.length ? `<div class="list">${agents.map(agent => this.agentRow(agent)).join('')}</div>` : this.empty('没有发现 ComponentAgents/*/AGENT.md。')}
        </section>

        <section class="section">
          <div class="section-title">
            <h2>Latest Knowledge Base</h2>
          </div>
          ${latestProject?.knowledgeBase ? this.knowledgeBaseCard(latestProject.name, latestProject.knowledgeBase) : this.empty('尚未发现 knowledge-base/kb-manifest.json。')}
        </section>
      </aside>
    </div>
  </main>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    document.addEventListener('click', (event) => {
      const target = event.target.closest('[data-action]');
      if (!target) return;
      const action = target.dataset.action;
      if (action === 'open') {
        vscode.postMessage({ type: 'openPath', path: target.dataset.path });
      }
      if (action === 'reveal') {
        vscode.postMessage({ type: 'revealPath', path: target.dataset.path });
      }
      if (action === 'workflow') {
        vscode.postMessage({ type: 'runWorkflow', name: target.dataset.name });
      }
      if (action === 'refresh') {
        vscode.postMessage({ type: 'refresh' });
      }
    });
  </script>
</body>
</html>`;
  }

  private metric(label: string, value: number, suffix = ''): string {
    return `<div class="metric"><div class="metric-value">${value}${this.escapeHtml(suffix)}</div><div class="metric-label">${this.escapeHtml(label)}</div></div>`;
  }

  private progressPanel(progress: ProgressStatus): string {
    if (!progress.exists) {
      return this.empty('等待进度文件。默认路径：WORKSPACE/.docmind-progress.json，可通过 docmind.progressFile 配置。');
    }

    const statusClass = this.statusClass(progress.status);
    return `<article class="card progress-card">
      <div class="progress-head">
        <div class="progress-title">
          <div class="title">${this.escapeHtml(progress.workflow || progress.project || 'DocMind Task')}</div>
          <span class="status ${statusClass}">${this.escapeHtml(progress.status)}</span>
        </div>
        <div class="desc">${this.escapeHtml(progress.message || progress.phase || progress.currentStep || '任务状态已同步')}</div>
        <div class="progress-bar" title="${progress.percent}%">
          <div class="progress-fill" style="--progress: ${progress.percent}%"></div>
        </div>
        <div class="progress-grid">
          ${this.progressKeyValue('Project', progress.project || '-')}
          ${this.progressKeyValue('Agent', progress.agent || '-')}
          ${this.progressKeyValue('Updated', progress.updatedAt || '-')}
        </div>
      </div>
      ${progress.steps.length ? `<div class="steps">${progress.steps.map(step => this.progressStep(step)).join('')}</div>` : ''}
      ${progress.outputs.length ? `<div class="tag-row" style="padding: 0 15px 15px; margin-top: 0;">${progress.outputs.map(output => `
        <span class="folder-pill" data-action="open" data-path="${this.escapeAttr(output.path)}">${this.escapeHtml(output.label)}</span>
      `).join('')}</div>` : ''}
      ${progress.error ? `<div class="empty" style="margin: 0 15px 15px;">${this.escapeHtml(progress.error)}</div>` : ''}
    </article>`;
  }

  private progressKeyValue(label: string, value: string): string {
    return `<div class="progress-kv"><div class="progress-kv-label">${this.escapeHtml(label)}</div><div class="progress-kv-value" title="${this.escapeAttr(value)}">${this.escapeHtml(value)}</div></div>`;
  }

  private progressStep(step: ProgressStep): string {
    const statusClass = this.statusClass(step.status);
    return `<div class="step">
      <span class="dot ${statusClass}"></span>
      <div class="row-main">
        <div class="row-title">${this.escapeHtml(step.name)}</div>
        <div class="row-sub">${this.escapeHtml([step.agent, step.message].filter(Boolean).join(' · ') || step.status)}</div>
      </div>
      <span class="tag">${typeof step.percent === 'number' ? `${this.clampPercent(step.percent)}%` : this.escapeHtml(step.status)}</span>
    </div>`;
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
    return '';
  }

  private projectCard(project: ProjectSummary): string {
    return `<article class="card project-card">
      <div class="project-head">
        <div class="card-header">
          <div class="title">${this.escapeHtml(project.name)}</div>
          ${project.knowledgeBase?.manifestPath ? '<span class="status">KB Ready</span>' : ''}
        </div>
        <div class="desc">${project.updatedAt}</div>
        <div class="project-meta">
          <span class="tag">${project.agentCount} agents</span>
          <span class="tag">${project.artifactCount} artifacts</span>
          ${project.knowledgeBase ? `<span class="tag">${project.knowledgeBase.docCount} docs</span>` : ''}
        </div>
      </div>
      <div class="agent-lines">
        ${project.agents.length ? project.agents.map(agent => `
          <div class="agent-line">
            <div class="row-title" title="${this.escapeAttr(agent.name)}">${this.escapeHtml(agent.name)}</div>
            <div class="folder-pills">
              ${agent.folders.map(folder => `<span class="folder-pill" data-action="reveal" data-path="${this.escapeAttr(folder.path)}">${this.escapeHtml(folder.name)} · ${folder.count}</span>`).join('')}
            </div>
          </div>
        `).join('') : '<div class="row"><div class="row-sub">Empty project workspace</div></div>'}
      </div>
    </article>`;
  }

  private workflowCard(workflow: WorkflowSummary): string {
    return `<article class="card">
      <div class="card-header">
        <div class="title" title="${this.escapeAttr(workflow.title)}">${this.escapeHtml(workflow.title)}</div>
        <button class="icon-button" data-action="workflow" data-name="${this.escapeAttr(workflow.name)}" title="Run Workflow">▶</button>
      </div>
      <div class="desc">${this.escapeHtml(workflow.description)}</div>
      <div class="tag-row">
        ${workflow.agents.map(agent => `<span class="tag">${this.escapeHtml(agent)}</span>`).join('')}
      </div>
    </article>`;
  }

  private agentRow(agent: AgentSummary): string {
    return `<div class="row">
      <div class="row-main">
        <div class="row-title" title="${this.escapeAttr(agent.name)}">${this.escapeHtml(agent.name)}</div>
        <div class="row-sub">${this.escapeHtml(agent.description)} · ${agent.skills} skills</div>
      </div>
      <button class="icon-button" data-action="open" data-path="${this.escapeAttr(agent.path)}" title="Open AGENT.md">↗</button>
    </div>`;
  }

  private knowledgeBaseCard(projectName: string, kb: KnowledgeBaseSummary): string {
    return `<div class="card">
      <div class="card-header">
        <div class="title">${this.escapeHtml(projectName)}</div>
        <button class="icon-button" data-action="open" data-path="${this.escapeAttr(kb.manifestPath || kb.path)}" title="Open Manifest">↗</button>
      </div>
      <div class="desc">${kb.docCount} documents, ${kb.keywordCount} keywords, ${kb.conceptCount} concepts</div>
      <div class="tag-row">
        ${kb.documents.slice(0, 8).map(doc => doc.path
          ? `<span class="folder-pill" data-action="open" data-path="${this.escapeAttr(doc.path)}">${this.escapeHtml(doc.title)}</span>`
          : `<span class="tag">${this.escapeHtml(doc.title)}</span>`).join('')}
      </div>
    </div>`;
  }

  private empty(text: string): string {
    return `<div class="empty">${this.escapeHtml(text)}</div>`;
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
        return {
          name,
          path: agentPath,
          folders: RESULT_FOLDERS
            .map(folder => {
              const folderPath = path.join(agentPath, folder);
              return {
                name: folder,
                path: folderPath,
                count: fs.existsSync(folderPath) ? this.countChildren(folderPath) : 0
              };
            })
            .filter(folder => folder.count > 0 || fs.existsSync(folder.path))
        };
      });
  }

  private scanKnowledgeBase(projectPath: string): KnowledgeBaseSummary | undefined {
    const kbPath = path.join(projectPath, 'knowledge-base');
    if (!fs.existsSync(kbPath)) {
      return undefined;
    }

    const manifestPath = path.join(kbPath, 'kb-manifest.json');
    if (!fs.existsSync(manifestPath)) {
      const documents = this.scanKnowledgeDocuments(kbPath);
      return { path: kbPath, docCount: documents.length, keywordCount: 0, conceptCount: 0, documents };
    }

    try {
      const manifest = JSON.parse(this.readText(manifestPath));
      const documents = Array.isArray(manifest.documents)
        ? manifest.documents.map((doc: { title?: string; source_file?: string; path?: string; file?: string; source_path?: string }) => {
          const sourcePath = doc.path || doc.file || doc.source_path || doc.source_file;
          return {
            title: doc.title || doc.source_file || doc.file || 'Untitled',
            sourceFile: doc.source_file,
            path: sourcePath ? this.resolveKnowledgeDocumentPath(sourcePath, projectPath, kbPath) : undefined
          };
        })
        : this.scanKnowledgeDocuments(kbPath);

      return {
        path: kbPath,
        manifestPath,
        docCount: manifest.document_count || 0,
        keywordCount: manifest.keyword_count || 0,
        conceptCount: manifest.concept_count || 0,
        documents
      };
    } catch {
      const documents = this.scanKnowledgeDocuments(kbPath);
      return { path: kbPath, manifestPath, docCount: documents.length, keywordCount: 0, conceptCount: 0, documents };
    }
  }

  private scanKnowledgeDocuments(kbPath: string): KnowledgeDocument[] {
    const documentExtensions = new Set(['.doc', '.docx', '.pdf', '.ppt', '.pptx', '.xls', '.xlsx', '.csv']);
    const documents: KnowledgeDocument[] = [];
    const visit = (dirPath: string, depth: number) => {
      if (depth < 0) {
        return;
      }
      for (const entry of this.readDirEntries(dirPath)) {
        const fullPath = path.join(dirPath, entry.name);
        if (entry.isDirectory()) {
          visit(fullPath, depth - 1);
          continue;
        }
        if (documentExtensions.has(path.extname(entry.name).toLowerCase())) {
          documents.push({ title: entry.name, path: fullPath, sourceFile: entry.name });
        }
      }
    };

    visit(kbPath, 3);
    return documents;
  }

  private extractAgents(content: string): string[] {
    const knownAgents = ['doc-content-analysis', 'doc-form-master', 'excel-master', 'ppt-deep-summary', 'knowledge-builder'];
    return knownAgents.filter(agent => content.includes(agent));
  }

  private countSkills(agentDir: string): number {
    const skillDirs = ['SKILLS', 'skills'].map(folder => path.join(agentDir, folder));
    return skillDirs.reduce((count, dir) => count + this.countChildren(dir), 0);
  }

  private countChildren(dirPath: string): number {
    return this.readDirEntries(dirPath).length;
  }

  private readDirs(dirPath: string): string[] {
    return this.readDirEntries(dirPath).filter(entry => entry.isDirectory()).map(entry => entry.name);
  }

  private readFiles(dirPath: string): string[] {
    return this.readDirEntries(dirPath).filter(entry => entry.isFile()).map(entry => entry.name);
  }

  private readDirEntries(dirPath: string): fs.Dirent[] {
    try {
      return fs.readdirSync(dirPath, { withFileTypes: true });
    } catch {
      return [];
    }
  }

  private readText(filePath: string): string {
    try {
      return fs.readFileSync(filePath, 'utf-8');
    } catch {
      return '';
    }
  }

  private getMtimeMs(filePath: string): number {
    try {
      return fs.statSync(filePath).mtimeMs;
    } catch {
      return 0;
    }
  }

  private formatUpdated(filePath: string): string {
    try {
      const updated = fs.statSync(filePath).mtime;
      return `Updated ${updated.toLocaleString('zh-CN', { hour12: false })}`;
    } catch {
      return 'Updated unknown';
    }
  }

  private getNonce(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let text = '';
    for (let i = 0; i < 32; i++) {
      text += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return text;
  }

  private escapeHtml(value: string): string {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  private escapeAttr(value: string): string {
    return this.escapeHtml(value);
  }

  private resolveWorkspacePath(filePath: string, basePath: string): string {
    if (!filePath) {
      return '';
    }
    return path.isAbsolute(filePath) ? filePath : path.resolve(basePath, filePath);
  }

  private resolveKnowledgeDocumentPath(filePath: string, projectPath: string, kbPath: string): string {
    if (!filePath) {
      return '';
    }
    if (path.isAbsolute(filePath)) {
      return filePath;
    }

    const candidates = [
      path.resolve(projectPath, filePath),
      path.resolve(kbPath, filePath),
      path.resolve(kbPath, 'documents', filePath)
    ];

    return candidates.find(candidate => fs.existsSync(candidate)) || candidates[0];
  }

  private clampPercent(value: number): number {
    if (!Number.isFinite(value)) {
      return 0;
    }
    return Math.max(0, Math.min(100, Math.round(value)));
  }

  private asRecord(value: unknown): Record<string, unknown> | undefined {
    return value && typeof value === 'object' && !Array.isArray(value)
      ? value as Record<string, unknown>
      : undefined;
  }

  private asString(value: unknown): string | undefined {
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    return undefined;
  }

  private asNumber(value: unknown): number | undefined {
    if (typeof value === 'number') {
      return value;
    }
    if (typeof value === 'string' && value.trim()) {
      const parsed = Number(value.replace('%', ''));
      return Number.isFinite(parsed) ? parsed : undefined;
    }
    return undefined;
  }
}
