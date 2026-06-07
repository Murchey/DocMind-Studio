import * as vscode from 'vscode';
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
      if (item) {
        vscode.window.showInformationMessage(`Running workflow: ${item.label}`);
        // TODO: trigger workflow execution
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('docmind.openKnowledgeBase', () => {
      DashboardPanel.createOrShow(context.extensionUri, rootPath);
    })
  );

  vscode.window.showInformationMessage('DocMind Studio activated');
}

export function deactivate() {}
