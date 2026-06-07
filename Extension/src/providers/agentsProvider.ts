import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

interface AgentInfo {
  name: string;
  description: string;
  path: string;
}

export class AgentsProvider implements vscode.TreeDataProvider<AgentItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<AgentItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private rootPath: string | undefined) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: AgentItem): vscode.TreeItem {
    return element;
  }

  getChildren(): Thenable<AgentItem[]> {
    if (!this.rootPath) {
      return Promise.resolve([]);
    }

    const agentsDir = path.join(this.rootPath, 'ComponentAgents');
    if (!fs.existsSync(agentsDir)) {
      return Promise.resolve([]);
    }

    const agents = this.scanAgents(agentsDir);
    return Promise.resolve(agents.map(a => new AgentItem(a)));
  }

  private scanAgents(dir: string): AgentInfo[] {
    const agents: AgentInfo[] = [];
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory()) {
          const agentMd = path.join(dir, entry.name, 'AGENT.md');
          if (fs.existsSync(agentMd)) {
            const content = fs.readFileSync(agentMd, 'utf-8');
            const descMatch = content.match(/description:\s*(.+)/);
            agents.push({
              name: entry.name,
              description: descMatch?.[1]?.trim() || 'No description',
              path: agentMd
            });
          }
        }
      }
    } catch (e) {
      // ignore
    }
    return agents;
  }
}

class AgentItem extends vscode.TreeItem {
  constructor(public readonly agent: AgentInfo) {
    super(agent.name, vscode.TreeItemCollapsibleState.None);
    this.tooltip = agent.description;
    this.description = agent.description;
    this.iconPath = new vscode.ThemeIcon('robot');
    this.command = {
      command: 'vscode.open',
      title: 'Open AGENT.md',
      arguments: [vscode.Uri.file(agent.path)]
    };
  }
}
