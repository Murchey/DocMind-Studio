import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

type ResultKind = 'project' | 'agent' | 'folder' | 'file' | 'empty';

interface ResultNode {
  label: string;
  filePath: string;
  kind: ResultKind;
  description?: string;
  collapsible: vscode.TreeItemCollapsibleState;
}

const RESULT_FOLDERS = ['knowledge-base', 'output', 'summary', 'parsed', 'validated', 'input'];

export class KnowledgeBaseProvider implements vscode.TreeDataProvider<ResultItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<ResultItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private rootPath: string | undefined) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ResultItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: ResultItem): Thenable<ResultItem[]> {
    if (!this.rootPath) {
      return Promise.resolve([this.emptyItem('Open DocMind-Studio as a workspace')]);
    }

    if (element) {
      return Promise.resolve(this.getChildItems(element.node));
    }

    return Promise.resolve(this.getProjectItems());
  }

  private getProjectItems(): ResultItem[] {
    const workspaceDir = path.join(this.rootPath!, 'WORKSPACE');
    if (!fs.existsSync(workspaceDir)) {
      return [this.emptyItem('No WORKSPACE directory found')];
    }

    const projects = this.readDirs(workspaceDir).map(project => {
      const projectPath = path.join(workspaceDir, project);
      return new ResultItem({
        label: project,
        filePath: projectPath,
        kind: 'project',
        description: this.describeProject(projectPath),
        collapsible: vscode.TreeItemCollapsibleState.Collapsed
      }, undefined, true);
    });

    return projects.length ? projects : [this.emptyItem('No generated projects yet')];
  }

  private getChildItems(node: ResultNode): ResultItem[] {
    if (!node.filePath || !fs.existsSync(node.filePath)) {
      return [];
    }

    if (node.kind === 'project') {
      return this.getProjectChildren(node.filePath);
    }

    if (node.kind === 'agent') {
      return this.getAgentChildren(node.filePath);
    }

    if (node.kind === 'folder') {
      return this.getDirectoryChildren(node.filePath);
    }

    return [];
  }

  private getProjectChildren(projectPath: string): ResultItem[] {
    const items: ResultItem[] = [];
    const knowledgeBasePath = path.join(projectPath, 'knowledge-base');

    if (fs.existsSync(knowledgeBasePath)) {
      items.push(this.folderItem('knowledge-base', knowledgeBasePath, 'database'));
    }

    for (const agentName of this.readDirs(projectPath)) {
      const agentPath = path.join(projectPath, agentName);
      if (agentName === 'knowledge-base') {
        continue;
      }

      items.push(new ResultItem({
        label: agentName,
        filePath: agentPath,
        kind: 'agent',
        description: this.describeAgentWorkspace(agentPath),
        collapsible: vscode.TreeItemCollapsibleState.Collapsed
      }));
    }

    return items.length ? items : [this.emptyItem('Project workspace is empty')];
  }

  private getAgentChildren(agentPath: string): ResultItem[] {
    const items = RESULT_FOLDERS
      .map(folder => path.join(agentPath, folder))
      .filter(folderPath => fs.existsSync(folderPath))
      .map(folderPath => this.folderItem(path.basename(folderPath), folderPath, this.iconForFolder(path.basename(folderPath))));

    return items.length ? items : [this.emptyItem('No agent artifacts yet')];
  }

  private getDirectoryChildren(dirPath: string): ResultItem[] {
    const entries = this.readDirEntries(dirPath)
      .filter(entry => !entry.name.startsWith('.'))
      .sort((a, b) => Number(b.isDirectory()) - Number(a.isDirectory()) || a.name.localeCompare(b.name));

    const items = entries.map(entry => {
      const fullPath = path.join(dirPath, entry.name);
      return entry.isDirectory()
        ? this.folderItem(entry.name, fullPath, this.iconForFolder(entry.name))
        : this.fileItem(entry.name, fullPath);
    });

    return items.length ? items : [this.emptyItem('Empty folder')];
  }

  private folderItem(label: string, filePath: string, iconName: string): ResultItem {
    return new ResultItem({
      label,
      filePath,
      kind: 'folder',
      description: this.describeFolder(filePath),
      collapsible: vscode.TreeItemCollapsibleState.Collapsed
    }, iconName);
  }

  private fileItem(label: string, filePath: string): ResultItem {
    return new ResultItem({
      label,
      filePath,
      kind: 'file',
      description: this.describeFile(filePath),
      collapsible: vscode.TreeItemCollapsibleState.None
    }, this.iconForFile(label));
  }

  private emptyItem(label: string): ResultItem {
    return new ResultItem({
      label,
      filePath: '',
      kind: 'empty',
      collapsible: vscode.TreeItemCollapsibleState.None
    }, 'info');
  }

  private describeProject(projectPath: string): string {
    const kbManifest = path.join(projectPath, 'knowledge-base', 'kb-manifest.json');
    const agentCount = this.readDirs(projectPath).filter(name => name !== 'knowledge-base').length;
    if (fs.existsSync(kbManifest)) {
      try {
        const manifest = JSON.parse(fs.readFileSync(kbManifest, 'utf-8'));
        return `${agentCount} agents, ${manifest.document_count || 0} docs`;
      } catch {
        return `${agentCount} agents, knowledge base`;
      }
    }
    return `${agentCount} agents`;
  }

  private describeAgentWorkspace(agentPath: string): string {
    const folders = RESULT_FOLDERS.filter(folder => fs.existsSync(path.join(agentPath, folder)));
    return folders.length ? folders.join(', ') : 'empty';
  }

  private describeFolder(folderPath: string): string {
    const count = this.readDirEntries(folderPath).length;
    return `${count} item${count === 1 ? '' : 's'}`;
  }

  private describeFile(filePath: string): string {
    try {
      const stat = fs.statSync(filePath);
      if (stat.size < 1024) {
        return `${stat.size} B`;
      }
      if (stat.size < 1024 * 1024) {
        return `${Math.round(stat.size / 1024)} KB`;
      }
      return `${(stat.size / 1024 / 1024).toFixed(1)} MB`;
    } catch {
      return '';
    }
  }

  private readDirs(dirPath: string): string[] {
    return this.readDirEntries(dirPath).filter(entry => entry.isDirectory()).map(entry => entry.name);
  }

  private readDirEntries(dirPath: string): fs.Dirent[] {
    try {
      return fs.readdirSync(dirPath, { withFileTypes: true });
    } catch {
      return [];
    }
  }

  private iconForFolder(folderName: string): string {
    if (folderName === 'knowledge-base') {
      return 'database';
    }
    if (folderName === 'output') {
      return 'output';
    }
    if (folderName === 'summary') {
      return 'book';
    }
    if (folderName === 'input') {
      return 'inbox';
    }
    if (folderName === 'parsed' || folderName === 'validated') {
      return 'checklist';
    }
    return 'folder';
  }

  private iconForFile(filename: string): string {
    const ext = path.extname(filename).toLowerCase();
    if (ext === '.json') {
      return 'json';
    }
    if (ext === '.md') {
      return 'markdown';
    }
    if (['.doc', '.docx', '.pdf', '.txt'].includes(ext)) {
      return 'file-text';
    }
    if (['.ppt', '.pptx'].includes(ext)) {
      return 'file-media';
    }
    if (['.xls', '.xlsx', '.csv'].includes(ext)) {
      return 'table';
    }
    return 'file';
  }
}

class ResultItem extends vscode.TreeItem {
  constructor(public readonly node: ResultNode, iconName?: string, exportable?: boolean) {
    super(node.label, node.collapsible);
    this.filePath = node.filePath;
    this.description = node.description;
    this.tooltip = node.filePath || node.label;
    this.iconPath = new vscode.ThemeIcon(iconName || this.iconNameForKind(node.kind));

    if (node.kind === 'file' && node.filePath) {
      this.command = {
        command: 'docmind.openPath',
        title: 'Open File',
        arguments: [node.filePath]
      };
    }

    const exportFlag = exportable ? ' docmindExportable' : '';
    this.contextValue = node.filePath
      ? `${node.kind} docmindOpenable docmindRevealable${exportFlag}`
      : node.kind;
  }

  public readonly filePath: string;

  private iconNameForKind(kind: ResultKind): string {
    if (kind === 'project') {
      return 'repo';
    }
    if (kind === 'agent') {
      return 'robot';
    }
    if (kind === 'folder') {
      return 'folder';
    }
    if (kind === 'file') {
      return 'file';
    }
    return 'info';
  }
}
