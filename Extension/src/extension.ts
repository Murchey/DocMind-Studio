import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as crypto from 'crypto';
import { ProgressService } from './services/progressService';
import { AgentsProvider } from './providers/agentsProvider';
import { WorkflowsProvider } from './providers/workflowsProvider';
import { KnowledgeBaseProvider } from './providers/knowledgeBaseProvider';
import { DashboardPanel } from './webview/dashboardPanel';
import { exportProject, ExportScope, ExportFormat, importFromZip, importFromFolder, importFromDms } from './utils/projectExporter';
import AdmZip = require('adm-zip');

export function activate(context: vscode.ExtensionContext) {
  const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

  // Tree View Providers
  const agentsProvider = new AgentsProvider(rootPath);
  const workflowsProvider = new WorkflowsProvider(rootPath);
  const knowledgeBaseProvider = new KnowledgeBaseProvider(rootPath);

  // ── ProgressService：通过 stdout 实时监听 Python 进度 ──
  const progressService = new ProgressService();
  context.subscriptions.push(progressService);

  // 将 ProgressService 事件转发到 Dashboard postMessage（增量更新，不重绘 HTML）
  context.subscriptions.push(
    progressService.onProgress((_event, task) => {
      if (task && DashboardPanel.currentPanel) {
        DashboardPanel.currentPanel.sendProgressUpdate({
          exists: true,
          status: task.status,
          percent: task.percent,
          project: task.project,
          workflow: task.workflow,
          agent: task.agent,
          currentStep: task.currentStep,
          message: task.message,
          steps: Array.from(task.steps.values()).map(s => ({
            id: s.step_id,
            name: s.step_id,
            status: s.status,
            percent: s.percent,
            message: s.message,
          })),
          outputs: [],
        });
      }
    })
  );

  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('docmind.agents', agentsProvider),
    vscode.window.registerTreeDataProvider('docmind.workflows', workflowsProvider),
    vscode.window.createTreeView('docmind.knowledgeBase', {
      treeDataProvider: knowledgeBaseProvider,
      showCollapseAll: true
    })
  );

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.openDashboard', () => {
      DashboardPanel.createOrShow(context.extensionUri, rootPath);
    })
  );

  // 启动 Python 任务并实时监听进度（替代旧的文件监听方案）
  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.startTask', (args: { taskId: string; script: string; args?: string[]; cwd?: string }) => {
      const workingDir = args.cwd || rootPath || process.cwd();
      progressService.startProcess(args.taskId, args.script, args.args || [], workingDir);
      DashboardPanel.createOrShow(context.extensionUri, rootPath);
      vscode.window.showInformationMessage(`DocMind task started: ${args.taskId}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.refreshAgents', () => {
      agentsProvider.refresh();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.refreshWorkflows', () => {
      workflowsProvider.refresh();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.refreshKnowledgeBase', () => {
      knowledgeBaseProvider.refresh();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.runWorkflow', (item) => {
      const label = item?.workflow?.name || item?.label || 'Workflow';
      if (item?.workflow?.path) {
        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(item.workflow.path));
      }
      vscode.window.showInformationMessage(`DocMind workflow ready: ${label}. Follow AGENTS.md to dispatch it from the workspace.`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.openKnowledgeBase', () => {
      DashboardPanel.createOrShow(context.extensionUri, rootPath);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.openPath', (target) => {
      const filePath = typeof target === 'string' ? target : target?.filePath;
      if (!filePath) {
        return;
      }
      if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
        vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(filePath));
        return;
      }
      if (shouldOpenExternally(filePath)) {
        vscode.env.openExternal(vscode.Uri.file(filePath));
        return;
      }
      vscode.commands.executeCommand('vscode.open', vscode.Uri.file(filePath));
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.revealPath', (target) => {
      const filePath = typeof target === 'string' ? target : target?.filePath;
      if (!filePath) {
        return;
      }
      vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(filePath));
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.exportProject', async (target) => {
      const projectPath = typeof target === 'string' ? target : target?.filePath || target?.node?.filePath;
      const projectName = typeof target === 'object' && target?.node?.label ? target.node.label : (typeof target === 'object' && target?.label ? target.label : undefined);

      if (!projectPath || !fs.existsSync(projectPath)) {
        vscode.window.showErrorMessage('DocMind: No project selected for export.');
        return;
      }

      // 如果没有从 TreeView 拿到名称，从路径推断
      const resolvedName = projectName || path.basename(projectPath);

      // 询问导出范围
      const scopePick = await vscode.window.showQuickPick([
        { label: 'Full Package', description: 'All Agent data, inputs, and outputs', scope: 'full' as ExportScope },
        { label: 'Output Only', description: 'Only output/summary/validated folders', scope: 'output-only' as ExportScope },
        { label: 'Custom Selection', description: 'Choose specific Agents to include', scope: 'custom' as ExportScope }
      ], {
        title: `Export Project: ${resolvedName}`,
        placeHolder: 'Select export scope'
      });

      if (!scopePick) { return; }

      // 如果选了 custom，弹出 Agent 选择
      let includeAgents: string[] | undefined;
      if (scopePick.scope === 'custom') {
        const agentDirs = fs.readdirSync(projectPath, { withFileTypes: true })
          .filter(e => e.isDirectory() && e.name !== 'knowledge-base')
          .map(e => e.name);
        const picks = await vscode.window.showQuickPick(
          agentDirs.map(name => ({ label: name, picked: true })),
          { canPickMany: true, title: 'Select Agents to Export' }
        );
        if (!picks || picks.length === 0) { return; }
        includeAgents = picks.map(p => p.label);
      }

      // 询问导出格式
      const formatPick = await vscode.window.showQuickPick([
        { label: 'DocMind Project (.dms)', description: 'Project file with metadata, directly restorable', format: 'dms' as ExportFormat },
        { label: 'Copy to Directory', description: 'Copy files to a target folder', format: 'copy' as ExportFormat }
      ], {
        title: `Export Project: ${resolvedName}`,
        placeHolder: 'Select export format'
      });

      if (!formatPick) { return; }

      // 执行导出
      const result = await exportProject({
        projectName: resolvedName,
        projectPath,
        scope: scopePick.scope,
        format: formatPick.format,
        includeAgents
      });

      if (result.success) {
        DashboardPanel.refresh(rootPath);
        knowledgeBaseProvider.refresh();
        vscode.window.showInformationMessage(
          `DocMind: Exported "${resolvedName}" → ${result.fileCount} files, ${formatSize(result.totalSize)}`,
          'Open Location'
        ).then(action => {
          if (action === 'Open Location') {
            vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(result.outputPath));
          }
        });
      } else if (result.error && result.error !== 'Export cancelled by user') {
        vscode.window.showErrorMessage(`DocMind Export failed: ${result.error}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.importProject', async () => {
      if (!rootPath) {
        vscode.window.showErrorMessage('DocMind: No workspace open.');
        return;
      }

      // 选择导入来源
      const sourcePick = await vscode.window.showQuickPick([
        { label: 'DocMind Project (.dms)', description: 'Import from a .dms project file', source: 'dms' },
        { label: 'ZIP Archive', description: 'Import from a .zip file', source: 'zip' },
        { label: 'Folder', description: 'Import from an existing directory', source: 'folder' }
      ], {
        title: 'Import Project',
        placeHolder: 'Select import source'
      });

      if (!sourcePick) { return; }

      let result;
      if (sourcePick.source === 'dms') {
        result = await importFromZip(rootPath);
      } else if (sourcePick.source === 'zip') {
        result = await importFromZip(rootPath);
      } else {
        result = await importFromFolder(rootPath);
      }

      if (result.success) {
        DashboardPanel.refresh(rootPath);
        knowledgeBaseProvider.refresh();
        vscode.window.showInformationMessage(
          `DocMind: Imported "${result.projectName}" → ${result.fileCount} files`,
          'Open Project'
        ).then(action => {
          if (action === 'Open Project') {
            vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(result.projectPath));
          }
        });
      } else if (result.error && result.error !== 'Import cancelled') {
        vscode.window.showErrorMessage(`DocMind Import failed: ${result.error}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.deleteProject', async (target) => {
      const projectPath = typeof target === 'string' ? target : target?.filePath || target?.node?.filePath;
      const projectName = typeof target === 'object' && target?.node?.label ? target.node.label : (typeof target === 'object' && target?.label ? target.label : undefined);

      if (!projectPath || !fs.existsSync(projectPath)) {
        vscode.window.showErrorMessage('DocMind: No project selected for deletion.');
        return;
      }

      const resolvedName = projectName || path.basename(projectPath);

      const confirm = await vscode.window.showWarningMessage(
        `Delete project "${resolvedName}" and all its data?`,
        { modal: true },
        'Delete'
      );

      if (confirm !== 'Delete') { return; }

      try {
        fs.rmSync(projectPath, { recursive: true, force: true });
        DashboardPanel.refresh(rootPath);
        knowledgeBaseProvider.refresh();
        vscode.window.showInformationMessage(`DocMind: Project "${resolvedName}" deleted.`);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`DocMind: Delete failed — ${msg}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.openDmsFile', async (uri?: vscode.Uri) => {
      if (!rootPath) {
        vscode.window.showErrorMessage('DocMind: No workspace open.');
        return;
      }

      // 如果没有传入 URI，弹出文件选择器
      let dmsPath: string | undefined;
      if (uri) {
        dmsPath = uri.fsPath;
      } else {
        const uris = await vscode.window.showOpenDialog({
          canSelectFiles: true,
          canSelectFolders: false,
          canSelectMany: false,
          filters: { 'DocMind Project': ['dms'] },
          title: 'Open DocMind Project File'
        });
        if (uris && uris[0]) {
          dmsPath = uris[0].fsPath;
        }
      }

      if (!dmsPath) { return; }

      const result = await importFromDms(rootPath, dmsPath);
      if (result.success) {
        DashboardPanel.refresh(rootPath);
        knowledgeBaseProvider.refresh();
        vscode.window.showInformationMessage(
          `DocMind: Restored "${result.projectName}" → ${result.fileCount} files`,
          'Open Project'
        ).then(action => {
          if (action === 'Open Project') {
            vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(result.projectPath));
          }
        });
      } else if (result.error && result.error !== 'Import cancelled') {
        vscode.window.showErrorMessage(`DocMind: Failed to open project — ${result.error}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.importAgent', async () => {
      if (!rootPath) {
        vscode.window.showErrorMessage('DocMind: No workspace open.');
        return;
      }

      const uris = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: { 'ZIP Archive': ['zip'] },
        title: '导入智能体 (ZIP)'
      });

      if (!uris || !uris[0]) { return; }

      const zipPath = uris[0].fsPath;
      const targetDir = path.join(rootPath, 'ComponentAgents');

      try {
        if (!fs.existsSync(targetDir)) {
          fs.mkdirSync(targetDir, { recursive: true });
        }
        const zip = new AdmZip(zipPath);
        zip.extractAllTo(targetDir, true);
        DashboardPanel.refresh(rootPath);
        vscode.window.showInformationMessage(`DocMind: 智能体已导入 → ${targetDir}`);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`DocMind: 智能体导入失败 — ${msg}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.importWorkflow', async () => {
      if (!rootPath) {
        vscode.window.showErrorMessage('DocMind: No workspace open.');
        return;
      }

      const uris = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: { 'ZIP Archive': ['zip'] },
        title: '导入工作流 (ZIP)'
      });

      if (!uris || !uris[0]) { return; }

      const zipPath = uris[0].fsPath;
      const targetDir = path.join(rootPath, 'Workflows');

      try {
        if (!fs.existsSync(targetDir)) {
          fs.mkdirSync(targetDir, { recursive: true });
        }
        const zip = new AdmZip(zipPath);
        zip.extractAllTo(targetDir, true);
        DashboardPanel.refresh(rootPath);
        vscode.window.showInformationMessage(`DocMind: 工作流已导入 → ${targetDir}`);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`DocMind: 工作流导入失败 — ${msg}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.buildKnowledgeBase', async (target) => {
      if (!rootPath) {
        vscode.window.showErrorMessage('DocMind: No workspace open.');
        return;
      }

      const projectPath = typeof target === 'string' ? target : target?.filePath || target?.node?.filePath;
      const projectName = typeof target === 'object' && target?.label ? target.label : (projectPath ? path.basename(projectPath) : undefined);

      if (!projectPath || !fs.existsSync(projectPath)) {
        vscode.window.showErrorMessage('DocMind: No project selected for KB build.');
        return;
      }

      // 查找 doc-content-analysis 的 summary 目录和 manifest
      const dcaDir = path.join(projectPath, 'doc-content-analysis');
      const summaryDir = path.join(dcaDir, 'summary');
      const manifestPath = path.join(summaryDir, 'manifest.json');
      const kbDir = path.join(projectPath, 'knowledge-base');
      const kbManagerScript = path.join(rootPath, 'ComponentAgents', 'doc-content-analysis', 'SKILLS', 'knowledge-builder', 'scripts', 'kb_manager.py');

      if (!fs.existsSync(kbManagerScript)) {
        vscode.window.showErrorMessage('DocMind: kb_manager.py not found.');
        return;
      }

      if (!fs.existsSync(manifestPath)) {
        vscode.window.showWarningMessage(`DocMind: No manifest.json found in ${summaryDir}. Run doc-content-analysis first.`);
        return;
      }

      const terminal = vscode.window.createTerminal({ name: 'DocMind KB Builder' });
      terminal.show();
      terminal.sendText(`python "${kbManagerScript}" init "${kbDir}" "${summaryDir}" "${manifestPath}" --agent doc-content-analysis`);

      vscode.window.showInformationMessage(`DocMind: Building knowledge base for "${projectName || path.basename(projectPath)}"...`);

      // 延迟刷新面板
      setTimeout(() => {
        DashboardPanel.refresh(rootPath);
        knowledgeBaseProvider.refresh();
      }, 5000);
    })
  );

  // [LEGACY] 基于文件监听的进度同步 — 保留作为 fallback（兼容非 Extension 启动的任务）。
  // 主路径已切换到 ProgressService（stdout 实时推送，见上方 docmind.startTask 命令）。
  if (rootPath) {
    const progressFile = vscode.workspace.getConfiguration('docmind').get<string>('progressFile') || 'WORKSPACE/.docmind-progress.json';
    const configuredWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(rootPath, progressFile));
    const watcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(rootPath, '**/*progress*.json'));
    
    // 新增：监听工作流执行器状态文件（.workflow_state.json）
    const workflowStateWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(rootPath, '**/WORKSPACE/*/.workflow_state.json'));
    
    const refreshProgress = () => {
      DashboardPanel.refresh(rootPath);
      knowledgeBaseProvider.refresh();
    };
    configuredWatcher.onDidCreate(refreshProgress, null, context.subscriptions);
    configuredWatcher.onDidChange(refreshProgress, null, context.subscriptions);
    configuredWatcher.onDidDelete(refreshProgress, null, context.subscriptions);
    watcher.onDidCreate(refreshProgress, null, context.subscriptions);
    watcher.onDidChange(refreshProgress, null, context.subscriptions);
    watcher.onDidDelete(refreshProgress, null, context.subscriptions);
    
    // 新增：工作流状态变更时刷新 Dashboard
    workflowStateWatcher.onDidCreate(refreshProgress, null, context.subscriptions);
    workflowStateWatcher.onDidChange(refreshProgress, null, context.subscriptions);
    workflowStateWatcher.onDidDelete(refreshProgress, null, context.subscriptions);
    
    context.subscriptions.push(configuredWatcher);
    context.subscriptions.push(watcher);
    context.subscriptions.push(workflowStateWatcher);

    // 启动进度轮询（每 3 秒扫描所有项目，作为文件监听的兜底）
    startProgressPolling(context, rootPath);
  }
}

export function deactivate() {}

function shouldOpenExternally(filePath: string): boolean {
  const officeLikeExtensions = new Set([
    '.doc',
    '.docx',
    '.pdf',
    '.ppt',
    '.pptx',
    '.xls',
    '.xlsx',
    '.csv'
  ]);

  return officeLikeExtensions.has(path.extname(filePath).toLowerCase());
}

function formatSize(bytes: number): string {
  if (bytes < 1024) { return `${bytes} B`; }
  if (bytes < 1024 * 1024) { return `${Math.round(bytes / 1024)} KB`; }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/**
 * 扫描所有项目的 .workflow_state.json，返回状态 map
 */
function scanAllWorkflowStates(rootPath: string): Map<string, object> {
  const states = new Map<string, object>();
  const workspacePath = path.join(rootPath, 'WORKSPACE');
  if (!fs.existsSync(workspacePath)) { return states; }

  try {
    const projects = fs.readdirSync(workspacePath, { withFileTypes: true });
    for (const project of projects) {
      if (!project.isDirectory()) { continue; }
      const stateFile = path.join(workspacePath, project.name, '.workflow_state.json');
      if (fs.existsSync(stateFile)) {
        try {
          const content = fs.readFileSync(stateFile, 'utf-8');
          const state = JSON.parse(content);
          states.set(project.name, state);
        } catch { /* skip invalid JSON */ }
      }
    }
  } catch { /* skip */ }

  return states;
}

/**
 * 启动进度轮询定时器
 */
/**
 * [LEGACY] 基于文件轮询的进度监听 — 保留作为 fallback。
 * 主路径已切换到 ProgressService（stdout 实时推送）。
 * 新任务请使用 docmind.startTask 命令。
 */
function startProgressPolling(context: vscode.ExtensionContext, workspaceRoot: string) {
  const lastHashes = new Map<string, string>();
  let lastProjectCount = 0;

  const poll = () => {
    const states = scanAllWorkflowStates(workspaceRoot);
    let progressChanged = false;
    let structureChanged = false;

    states.forEach((state, projectName) => {
      const content = JSON.stringify(state);
      const hash = crypto.createHash('md5').update(content).digest('hex');
      if (lastHashes.get(projectName) !== hash) {
        lastHashes.set(projectName, hash);
        progressChanged = true;
      }
    });

    // 检查已消失的项目
    lastHashes.forEach((_, projectName) => {
      if (!states.has(projectName)) {
        lastHashes.delete(projectName);
        structureChanged = true;
      }
    });

    // 项目数量变化 → 结构化变更，需要全量刷新
    if (states.size !== lastProjectCount) {
      lastProjectCount = states.size;
      structureChanged = true;
    }

    // 进度数据变更 → 增量更新（postMessage，不刷新整个 HTML）
    if (progressChanged && !structureChanged) {
      DashboardPanel.syncProgressFromFile(workspaceRoot);
    }

    // 结构化变更 → 全量刷新
    if (structureChanged) {
      DashboardPanel.refresh(workspaceRoot);
    }
  };

  // 每 3 秒轮询一次
  const timer = setInterval(poll, 3000);
  context.subscriptions.push({ dispose: () => clearInterval(timer) });
}
