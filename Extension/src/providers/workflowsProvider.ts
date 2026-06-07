import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

interface WorkflowInfo {
  name: string;
  description: string;
  path: string;
}

export class WorkflowsProvider implements vscode.TreeDataProvider<WorkflowItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<WorkflowItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private rootPath: string | undefined) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: WorkflowItem): vscode.TreeItem {
    return element;
  }

  getChildren(): Thenable<WorkflowItem[]> {
    if (!this.rootPath) {
      return Promise.resolve([]);
    }

    const workflowsDir = path.join(this.rootPath, 'Workflows');
    if (!fs.existsSync(workflowsDir)) {
      return Promise.resolve([]);
    }

    const workflows = this.scanWorkflows(workflowsDir);
    return Promise.resolve(workflows.map(w => new WorkflowItem(w)));
  }

  private scanWorkflows(dir: string): WorkflowInfo[] {
    const workflows: WorkflowInfo[] = [];
    try {
      const files = fs.readdirSync(dir);
      for (const file of files) {
        if (file.endsWith('Workflow.md')) {
          const fullPath = path.join(dir, file);
          const content = fs.readFileSync(fullPath, 'utf-8');
          const heading = content.split(/\r?\n/).find(line => line.startsWith('# '));
          workflows.push({
            name: file.replace('.md', ''),
            description: heading?.replace(/^#\s*/, '').trim() || 'Workflow',
            path: fullPath
          });
        }
      }
    } catch (e) {
      // ignore
    }
    return workflows;
  }
}

class WorkflowItem extends vscode.TreeItem {
  constructor(public readonly workflow: WorkflowInfo) {
    super(workflow.name, vscode.TreeItemCollapsibleState.None);
    this.tooltip = workflow.description;
    this.description = workflow.description;
    this.iconPath = new vscode.ThemeIcon('play');
    this.command = {
      command: 'vscode.open',
      title: 'Open Workflow',
      arguments: [vscode.Uri.file(workflow.path)]
    };
    this.contextValue = 'workflow docmindOpenable docmindRevealable';
  }
}
