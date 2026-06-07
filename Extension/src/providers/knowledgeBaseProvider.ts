import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

export class KnowledgeBaseProvider implements vscode.TreeDataProvider<KBItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<KBItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private rootPath: string | undefined) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: KBItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: KBItem): Thenable<KBItem[]> {
    if (!this.rootPath) {
      return Promise.resolve([]);
    }

    if (element) {
      return Promise.resolve(this.getChildItems(element));
    }

    // Root level: scan for knowledge-base and agent workspaces
    return Promise.resolve(this.getRootItems());
  }

  private getRootItems(): KBItem[] {
    const items: KBItem[] = [];

    // Knowledge Base
    const kbPath = path.join(this.rootPath!, 'knowledge-base');
    if (fs.existsSync(kbPath)) {
      items.push(new KBItem('Knowledge Base', kbPath, 'database', true));
    }

    // Agent workspaces with summary
    const agentsDir = path.join(this.rootPath!, 'ComponentAgents');
    if (fs.existsSync(agentsDir)) {
      try {
        for (const entry of fs.readdirSync(agentsDir, { withFileTypes: true })) {
          if (entry.isDirectory()) {
            const summaryDir = path.join(agentsDir, entry.name, 'workspace', 'summary');
            if (fs.existsSync(summaryDir)) {
              items.push(new KBItem(entry.name, summaryDir, 'folder-library', true));
            }
          }
        }
      } catch (e) {
        // ignore
      }
    }

    if (items.length === 0) {
      items.push(new KBItem('No knowledge base found', '', 'info', false));
    }

    return items;
  }

  private getChildItems(element: KBItem): KBItem[] {
    if (!fs.existsSync(element.filePath)) {
      return [];
    }

    const items: KBItem[] = [];
    try {
      const entries = fs.readdirSync(element.filePath, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(element.filePath, entry.name);
        if (entry.name === 'manifest.json' || entry.name === 'kb-manifest.json') {
          items.push(new KBItem(entry.name, fullPath, 'file-code', false));
        } else if (entry.name.endsWith('.json')) {
          items.push(new KBItem(entry.name, fullPath, 'file-code', false));
        } else if (entry.isDirectory()) {
          items.push(new KBItem(entry.name, fullPath, 'folder', true));
        }
      }
    } catch (e) {
      // ignore
    }
    return items;
  }
}

class KBItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly filePath: string,
    iconName: string,
    public readonly isDir: boolean
  ) {
    super(label, isDir ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None);
    this.iconPath = new vscode.ThemeIcon(iconName);
    if (!isDir && filePath) {
      this.command = {
        command: 'vscode.open',
        title: 'Open File',
        arguments: [vscode.Uri.file(filePath)]
      };
    }
  }
}
