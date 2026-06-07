import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

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

  private constructor(panel: vscode.WebviewPanel, rootPath: string | undefined) {
    this._panel = panel;
    this._update(rootPath);
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

  private _update(rootPath: string | undefined) {
    this._panel.webview.html = this._getHtml(rootPath);
  }

  private _getHtml(rootPath: string | undefined): string {
    const agents = this._scanAgents(rootPath);
    const workflows = this._scanWorkflows(rootPath);
    const kbStatus = this._scanKnowledgeBase(rootPath);

    return `<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DocMind Studio</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      padding: 24px;
    }
    h1 { font-size: 24px; margin-bottom: 8px; }
    h2 { font-size: 16px; margin: 24px 0 12px; color: var(--vscode-descriptionForeground); }
    .subtitle { color: var(--vscode-descriptionForeground); margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
    .card {
      background: var(--vscode-sideBar-background);
      border: 1px solid var(--vscode-widget-border);
      border-radius: 8px;
      padding: 16px;
    }
    .card-title { font-weight: 600; margin-bottom: 4px; }
    .card-desc { font-size: 12px; color: var(--vscode-descriptionForeground); }
    .status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .status-ready { background: #2ea04333; color: #3fb950; }
    .status-empty { background: #6e768133; color: #8b949e; }
    .status-running { background: #d2992233; color: #d29922; }
    .kb-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--vscode-widget-border); }
    .kb-item:last-child { border-bottom: none; }
    .kb-icon { font-size: 18px; }
    .kb-name { font-size: 13px; }
    .stat { font-size: 28px; font-weight: 700; }
    .stat-label { font-size: 12px; color: var(--vscode-descriptionForeground); }
    .stats { display: flex; gap: 32px; margin-bottom: 24px; }
    .btn {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 6px 14px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      margin-top: 8px;
    }
    .btn:hover { background: var(--vscode-button-hoverBackground); }
  </style>
</head>
<body>
  <h1>DocMind Studio</h1>
  <p class="subtitle">多 Agent 文档智能处理与知识库管理</p>

  <div class="stats">
    <div>
      <div class="stat">${agents.length}</div>
      <div class="stat-label">Agents</div>
    </div>
    <div>
      <div class="stat">${workflows.length}</div>
      <div class="stat-label">Workflows</div>
    </div>
    <div>
      <div class="stat">${kbStatus.exists ? kbStatus.docCount : '-'}</div>
      <div class="stat-label">Documents</div>
    </div>
  </div>

  <h2>Agents</h2>
  <div class="grid">
    ${agents.map(a => `
    <div class="card">
      <div class="card-title">${a.name}</div>
      <div class="card-desc">${a.description}</div>
    </div>`).join('')}
  </div>

  <h2>Workflows</h2>
  <div class="grid">
    ${workflows.map(w => `
    <div class="card">
      <div class="card-title">${w.name}</div>
      <div class="card-desc">${w.description}</div>
      <button class="btn" onclick="runWorkflow('${w.name}')">Run</button>
    </div>`).join('')}
  </div>

  <h2>Knowledge Base</h2>
  <div class="card">
    ${kbStatus.exists ? `
    <div class="card-title">
      Knowledge Base
      <span class="status status-ready">Ready</span>
    </div>
    <div class="card-desc">${kbStatus.docCount} documents, ${kbStatus.keywordCount} keywords, ${kbStatus.conceptCount} concepts</div>
    ${kbStatus.documents.map(d => `
    <div class="kb-item">
      <span class="kb-icon">${d.icon}</span>
      <span class="kb-name">${d.title}</span>
    </div>`).join('')}
    ` : `
    <div class="card-title">
      Knowledge Base
      <span class="status status-empty">Not Built</span>
    </div>
    <div class="card-desc">Run KnowledgeBuilder workflow to generate</div>
    `}
  </div>

  <script>
    function runWorkflow(name) {
      const vscode = acquireVsCodeApi();
      vscode.postMessage({ type: 'runWorkflow', name });
    }
  </script>
</body>
</html>`;
  }

  private _scanAgents(rootPath: string | undefined): { name: string; description: string }[] {
    if (!rootPath) return [];
    const agentsDir = path.join(rootPath, 'ComponentAgents');
    if (!fs.existsSync(agentsDir)) return [];

    const agents: { name: string; description: string }[] = [];
    try {
      for (const entry of fs.readdirSync(agentsDir, { withFileTypes: true })) {
        if (entry.isDirectory()) {
          const agentMd = path.join(agentsDir, entry.name, 'AGENT.md');
          if (fs.existsSync(agentMd)) {
            const content = fs.readFileSync(agentMd, 'utf-8');
            const match = content.match(/description:\s*(.+)/);
            agents.push({
              name: entry.name,
              description: match?.[1]?.trim() || 'No description'
            });
          }
        }
      }
    } catch (e) { /* ignore */ }
    return agents;
  }

  private _scanWorkflows(rootPath: string | undefined): { name: string; description: string }[] {
    if (!rootPath) return [];
    const dir = path.join(rootPath, 'Workflows');
    if (!fs.existsSync(dir)) return [];

    const workflows: { name: string; description: string }[] = [];
    try {
      for (const file of fs.readdirSync(dir)) {
        if (file.endsWith('Workflow.md')) {
          const content = fs.readFileSync(path.join(dir, file), 'utf-8');
          const firstLine = content.split('\n').find(l => l.startsWith('# '));
          workflows.push({
            name: file.replace('.md', ''),
            description: firstLine?.replace('# ', '') || ''
          });
        }
      }
    } catch (e) { /* ignore */ }
    return workflows;
  }

  private _scanKnowledgeBase(rootPath: string | undefined): {
    exists: boolean;
    docCount: number;
    keywordCount: number;
    conceptCount: number;
    documents: { title: string; icon: string }[];
  } {
    if (!rootPath) return { exists: false, docCount: 0, keywordCount: 0, conceptCount: 0, documents: [] };

    const kbPath = path.join(rootPath, 'knowledge-base');
    const manifestPath = path.join(kbPath, 'kb-manifest.json');

    if (!fs.existsSync(manifestPath)) {
      return { exists: false, docCount: 0, keywordCount: 0, conceptCount: 0, documents: [] };
    }

    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
      return {
        exists: true,
        docCount: manifest.document_count || 0,
        keywordCount: manifest.keyword_count || 0,
        conceptCount: manifest.concept_count || 0,
        documents: (manifest.documents || []).map((d: any) => ({
          title: d.title || d.source_file,
          icon: this._getDocIcon(d.source_file)
        }))
      };
    } catch (e) {
      return { exists: false, docCount: 0, keywordCount: 0, conceptCount: 0, documents: [] };
    }
  }

  private _getDocIcon(filename: string): string {
    if (filename.endsWith('.doc') || filename.endsWith('.docx')) return ' ';
    if (filename.endsWith('.pdf')) return ' ';
    if (filename.endsWith('.txt')) return ' ';
    if (filename.endsWith('.ppt') || filename.endsWith('.pptx')) return ' ';
    if (filename.endsWith('.xls') || filename.endsWith('.xlsx')) return ' ';
    return ' ';
  }
}
