import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { AgentsProvider } from './providers/agentsProvider';
import { WorkflowsProvider } from './providers/workflowsProvider';
import { KnowledgeBaseProvider } from './providers/knowledgeBaseProvider';
import { DashboardPanel } from './webview/dashboardPanel';

export function activate(context: vscode.ExtensionContext) {
  const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

  // Tree View Providers
  const agentsProvider = new AgentsProvider(rootPath);
  const workflowsProvider = new WorkflowsProvider(rootPath);
  const knowledgeBaseProvider = new KnowledgeBaseProvider(rootPath);

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

  if (rootPath) {
    const progressFile = vscode.workspace.getConfiguration('docmind').get<string>('progressFile') || 'WORKSPACE/.docmind-progress.json';
    const configuredWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(rootPath, progressFile));
    const watcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(rootPath, '**/*progress*.json'));
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
    context.subscriptions.push(configuredWatcher);
    context.subscriptions.push(watcher);
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
