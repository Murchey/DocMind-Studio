import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import AdmZip = require('adm-zip');

export type ExportScope = 'full' | 'output-only' | 'custom';
export type ExportFormat = 'dms' | 'copy';

export interface ExportOptions {
  projectName: string;
  projectPath: string;
  scope: ExportScope;
  format: ExportFormat;
  targetPath?: string;
  includeAgents?: string[];
}

export interface ExportResult {
  success: boolean;
  outputPath: string;
  totalSize: number;
  fileCount: number;
  error?: string;
}

/**
 * .dms 项目元数据文件（DocMind Studio Project）
 * 本质是 ZIP，内含 project_manifest.json + 全部项目文件
 */
export const DMS_EXTENSION = '.dms';
export const DMS_MIMETYPE = 'application/x-docmind-project';

interface ProjectManifest {
  format_version: string;
  exported_at: string;
  source: string;
  project_name: string;
  scope: ExportScope;
  agents: AgentManifest[];
  knowledge_base?: KnowledgeBaseManifest;
  total_files: number;
  total_size_bytes: number;
  description?: string;
}

interface AgentManifest {
  name: string;
  folders: string[];
  artifact_count: number;
}

interface KnowledgeBaseManifest {
  doc_count: number;
  keyword_count: number;
}

const RESULT_FOLDERS = ['input', 'output', 'summary', 'parsed', 'validated', 'converted', 'projects', 'solution'];
const OUTPUT_ONLY_FOLDERS = ['output', 'summary', 'validated'];
const EXCLUDE_PATTERNS = ['.workflow_state.json', '.docmind-progress.json', '.tmp', '.kb_state.json'];

/**
 * 导出单个工作区项目
 */
export async function exportProject(options: ExportOptions): Promise<ExportResult> {
  if (!fs.existsSync(options.projectPath)) {
    return { success: false, outputPath: '', totalSize: 0, fileCount: 0, error: `Project path not found: ${options.projectPath}` };
  }

  const manifest = buildManifest(options);

  if (options.format === 'dms') {
    return exportAsDms(options, manifest);
  }
  return exportAsCopy(options, manifest);
}

/**
 * .dms 模式导出（DocMind Studio Project 文件）
 */
async function exportAsDms(options: ExportOptions, manifest: ProjectManifest): Promise<ExportResult> {
  const saveUri = await vscode.window.showSaveDialog({
    defaultUri: vscode.Uri.file(`${options.projectName}${DMS_EXTENSION}`),
    filters: { 'DocMind Project': ['dms'], 'All Files': ['*'] },
    title: `Export Project: ${options.projectName}`
  });

  if (!saveUri) {
    return { success: false, outputPath: '', totalSize: 0, fileCount: 0, error: 'Export cancelled by user' };
  }

  const zip = new AdmZip();
  let fileCount = 0;
  let totalSize = 0;

  const dirsToExport = getDirsToExport(options);

  for (const dirInfo of dirsToExport) {
    if (!fs.existsSync(dirInfo.fullPath)) {
      continue;
    }
    const entries = collectFiles(dirInfo.fullPath);
    for (const entry of entries) {
      const relativeInDir = path.relative(dirInfo.fullPath, entry);
      const archivePath = path.join(options.projectName, dirInfo.archivePrefix, relativeInDir).replace(/\\/g, '/');
      zip.addLocalFile(entry, path.dirname(archivePath === path.join(options.projectName, dirInfo.archivePrefix).replace(/\\/g, '/') ? '.' : path.dirname(archivePath)), path.basename(archivePath));
      const stat = fs.statSync(entry);
      totalSize += stat.size;
      fileCount++;
    }
  }

  // 添加 manifest
  const manifestJson = JSON.stringify(manifest, null, 2);
  zip.addFile(`${options.projectName}/project_manifest.json`, Buffer.from(manifestJson, 'utf-8'));

  // 写入临时文件再移动（原子写入）
  const tmpFile = path.join(os.tmpdir(), `docmind-export-${Date.now()}.zip`);
  try {
    zip.writeZip(tmpFile);
    // 确保目标目录存在
    const targetDir = path.dirname(saveUri.fsPath);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    fs.copyFileSync(tmpFile, saveUri.fsPath);
    fs.unlinkSync(tmpFile);
    return { success: true, outputPath: saveUri.fsPath, totalSize, fileCount: fileCount + 1 };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    try { fs.unlinkSync(tmpFile); } catch { /* ignore */ }
    return { success: false, outputPath: '', totalSize: 0, fileCount: 0, error: `ZIP write failed: ${msg}` };
  }
}

/**
 * 复制模式导出
 */
async function exportAsCopy(options: ExportOptions, manifest: ProjectManifest): Promise<ExportResult> {
  const targetUri = await vscode.window.showOpenDialog({
    canSelectFiles: false,
    canSelectFolders: true,
    canSelectMany: false,
    title: `Select export destination for: ${options.projectName}`
  });

  if (!targetUri || !targetUri[0]) {
    return { success: false, outputPath: '', totalSize: 0, fileCount: 0, error: 'Export cancelled by user' };
  }

  const destBase = path.join(targetUri[0].fsPath, options.projectName);

  // 清理目标目录（如果存在）
  if (fs.existsSync(destBase)) {
    const answer = await vscode.window.showWarningMessage(
      `Directory "${options.projectName}" already exists at target. Overwrite?`,
      'Overwrite', 'Cancel'
    );
    if (answer !== 'Overwrite') {
      return { success: false, outputPath: '', totalSize: 0, fileCount: 0, error: 'Export cancelled: directory exists' };
    }
    fs.rmSync(destBase, { recursive: true, force: true });
  }

  let fileCount = 0;
  let totalSize = 0;

  const dirsToExport = getDirsToExport(options);

  for (const dirInfo of dirsToExport) {
    if (!fs.existsSync(dirInfo.fullPath)) {
      continue;
    }
    const destDir = path.join(destBase, dirInfo.archivePrefix);
    fs.mkdirSync(destDir, { recursive: true });

    const entries = collectFiles(dirInfo.fullPath);
    for (const entry of entries) {
      const relativePath = path.relative(dirInfo.fullPath, entry);
      const destFile = path.join(destDir, relativePath);
      const destFileDir = path.dirname(destFile);
      if (!fs.existsSync(destFileDir)) {
        fs.mkdirSync(destFileDir, { recursive: true });
      }
      fs.copyFileSync(entry, destFile);
      const stat = fs.statSync(entry);
      totalSize += stat.size;
      fileCount++;
    }
  }

  // 写入 manifest
  const manifestDir = path.join(destBase);
  fs.mkdirSync(manifestDir, { recursive: true });
  fs.writeFileSync(path.join(manifestDir, 'project_manifest.json'), JSON.stringify(manifest, null, 2), 'utf-8');

  return { success: true, outputPath: destBase, totalSize, fileCount: fileCount + 1 };
}

/**
 * 构建项目元数据 manifest
 */
function buildManifest(options: ExportOptions): ProjectManifest {
  const agents: AgentManifest[] = [];
  let knowledgeBase: KnowledgeBaseManifest | undefined;

  if (fs.existsSync(options.projectPath)) {
    const entries = fs.readdirSync(options.projectPath, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) { continue; }
      if (entry.name === 'knowledge-base') {
        knowledgeBase = readKnowledgeBaseManifest(path.join(options.projectPath, entry.name));
        continue;
      }
      if (options.scope === 'custom' && options.includeAgents && !options.includeAgents.includes(entry.name)) {
        continue;
      }
      const agentPath = path.join(options.projectPath, entry.name);
      const folders = RESULT_FOLDERS.filter(f => fs.existsSync(path.join(agentPath, f)));
      const artifactCount = folders.reduce((sum, f) => sum + countFiles(path.join(agentPath, f)), 0);
      agents.push({ name: entry.name, folders, artifact_count: artifactCount });
    }
  }

  return {
    format_version: '1.0',
    exported_at: new Date().toISOString(),
    source: 'DocMind-Studio',
    project_name: options.projectName,
    scope: options.scope,
    agents,
    knowledge_base: knowledgeBase,
    total_files: 0,
    total_size_bytes: 0
  };
}

function readKnowledgeBaseManifest(kbPath: string): KnowledgeBaseManifest | undefined {
  const manifestPath = path.join(kbPath, 'kb-manifest.json');
  if (!fs.existsSync(manifestPath)) {
    return undefined;
  }
  try {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
    return {
      doc_count: Array.isArray(manifest.documents) ? manifest.documents.length : 0,
      keyword_count: Array.isArray(manifest.keywords) ? manifest.keywords.length : 0
    };
  } catch {
    return undefined;
  }
}

/**
 * 根据 scope 决定要导出的目录列表
 */
function getDirsToExport(options: ExportOptions): Array<{ fullPath: string; archivePrefix: string }> {
  const result: Array<{ fullPath: string; archivePrefix: string }> = [];

  if (!fs.existsSync(options.projectPath)) {
    return result;
  }

  const entries = fs.readdirSync(options.projectPath, { withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isDirectory()) { continue; }

    // 始终跳过 knowledge-base（单独处理）
    if (entry.name === 'knowledge-base') { continue; }

    const agentDir = path.join(options.projectPath, entry.name);

    if (options.scope === 'full') {
      result.push({ fullPath: agentDir, archivePrefix: entry.name });
    } else if (options.scope === 'output-only') {
      // 只收集 output 类目录
      for (const folder of OUTPUT_ONLY_FOLDERS) {
        const folderPath = path.join(agentDir, folder);
        if (fs.existsSync(folderPath)) {
          result.push({ fullPath: folderPath, archivePrefix: path.join(entry.name, folder) });
        }
      }
    } else if (options.scope === 'custom') {
      if (options.includeAgents && options.includeAgents.includes(entry.name)) {
        result.push({ fullPath: agentDir, archivePrefix: entry.name });
      }
    }
  }

  // knowledge-base 单独包含
  if (options.scope !== 'output-only') {
    const kbPath = path.join(options.projectPath, 'knowledge-base');
    if (fs.existsSync(kbPath)) {
      result.push({ fullPath: kbPath, archivePrefix: 'knowledge-base' });
    }
  }

  return result;
}

/**
 * 递归收集目录下所有文件（排除隐藏文件和临时文件）
 */
function collectFiles(dirPath: string): string[] {
  const results: string[] = [];
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectFiles(fullPath));
    } else if (entry.isFile() && !isExcluded(entry.name)) {
      results.push(fullPath);
    }
  }

  return results;
}

function isExcluded(filename: string): boolean {
  if (filename.startsWith('.')) { return true; }
  return EXCLUDE_PATTERNS.some(pattern => filename === pattern || filename.endsWith(pattern));
}

function countFiles(dirPath: string): number {
  if (!fs.existsSync(dirPath)) { return 0; }
  let count = 0;
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory()) {
      count += countFiles(path.join(dirPath, entry.name));
    } else if (entry.isFile()) {
      count++;
    }
  }
  return count;
}

// ============================================================
// Import
// ============================================================

export interface ImportResult {
  success: boolean;
  projectPath: string;
  projectName: string;
  fileCount: number;
  error?: string;
}

/**
 * 从 .dms / ZIP 文件导入项目到 WORKSPACE
 */
export async function importFromZip(workspaceRoot: string): Promise<ImportResult> {
  const uris = await vscode.window.showOpenDialog({
    canSelectFiles: true,
    canSelectFolders: false,
    canSelectMany: false,
    filters: { 'DocMind Project': ['dms'], 'ZIP Archive': ['zip'] },
    title: 'Import Project'
  });

  if (!uris || !uris[0]) {
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: 'Import cancelled' };
  }

  const filePath = uris[0].fsPath;
  return importFromDmsPath(workspaceRoot, filePath);
}

/**
 * 直接导入 .dms 文件（双击 / 命令调用）
 */
export async function importFromDms(workspaceRoot: string, dmsFilePath: string): Promise<ImportResult> {
  if (!fs.existsSync(dmsFilePath)) {
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: `File not found: ${dmsFilePath}` };
  }
  return importFromDmsPath(workspaceRoot, dmsFilePath);
}

/**
 * 从已解压的目录导入项目到 WORKSPACE
 */
export async function importFromFolder(workspaceRoot: string): Promise<ImportResult> {
  const uris = await vscode.window.showOpenDialog({
    canSelectFiles: false,
    canSelectFolders: true,
    canSelectMany: false,
    title: 'Import Project from Folder'
  });

  if (!uris || !uris[0]) {
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: 'Import cancelled' };
  }

  const srcDir = uris[0].fsPath;
  return importFromFolderPath(workspaceRoot, srcDir);
}

/**
 * 从 .dms / ZIP 路径导入
 */
async function importFromDmsPath(workspaceRoot: string, filePath: string): Promise<ImportResult> {
  let zip: AdmZip;
  try {
    zip = new AdmZip(filePath);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: `Failed to read file: ${msg}` };
  }

  // 读取文件内的 manifest
  const manifestEntry = zip.getEntry('project_manifest.json');
  let manifest: ProjectManifest | null = null;
  if (manifestEntry) {
    try {
      manifest = JSON.parse(manifestEntry.getData().toString('utf-8'));
    } catch { /* ignore */ }
  }

  // 确定项目名：优先 manifest，其次文件名（去掉 .dms 或 .zip 后缀）
  const ext = path.extname(filePath);
  const baseName = path.basename(filePath, ext);
  let projectName = manifest?.project_name || baseName;

  // 检查 WORKSPACE 下同名目录，处理冲突
  const workspaceDir = path.join(workspaceRoot, 'WORKSPACE');
  if (!fs.existsSync(workspaceDir)) {
    fs.mkdirSync(workspaceDir, { recursive: true });
  }

  const resolvedName = await resolveProjectName(workspaceDir, projectName);
  if (!resolvedName) {
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: 'Import cancelled' };
  }
  projectName = resolvedName;

  const targetDir = path.join(workspaceDir, projectName);

  // 解压到临时目录再移动
  const tmpDir = path.join(os.tmpdir(), `docmind-import-${Date.now()}`);
  try {
    zip.extractAllTo(tmpDir, true);

    // ZIP 内可能有一层项目名子目录（导出时的结构）
    // 检查是否只有一层子目录且包含 manifest
    const tmpEntries = fs.readdirSync(tmpDir, { withFileTypes: true });
    let sourceDir = tmpDir;
    if (tmpEntries.length === 1 && tmpEntries[0].isDirectory()) {
      const innerDir = path.join(tmpDir, tmpEntries[0].name);
      const innerManifest = path.join(innerDir, 'project_manifest.json');
      if (fs.existsSync(innerManifest)) {
        sourceDir = innerDir;
      }
    }

    // 复制到目标
    fs.mkdirSync(targetDir, { recursive: true });
    const fileCount = copyRecursive(sourceDir, targetDir);

    return { success: true, projectPath: targetDir, projectName, fileCount };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: `Extract failed: ${msg}` };
  } finally {
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch { /* ignore */ }
  }
}

/**
 * 从文件夹路径导入
 */
async function importFromFolderPath(workspaceRoot: string, srcDir: string): Promise<ImportResult> {
  if (!fs.existsSync(srcDir)) {
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: `Source directory not found: ${srcDir}` };
  }

  // 读取 manifest
  const manifestPath = path.join(srcDir, 'project_manifest.json');
  let manifest: ProjectManifest | null = null;
  if (fs.existsSync(manifestPath)) {
    try {
      manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
    } catch { /* ignore */ }
  }

  let projectName = manifest?.project_name || path.basename(srcDir);

  const workspaceDir = path.join(workspaceRoot, 'WORKSPACE');
  if (!fs.existsSync(workspaceDir)) {
    fs.mkdirSync(workspaceDir, { recursive: true });
  }

  const resolvedName = await resolveProjectName(workspaceDir, projectName);
  if (!resolvedName) {
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: 'Import cancelled' };
  }
  projectName = resolvedName;

  const targetDir = path.join(workspaceDir, projectName);

  try {
    fs.mkdirSync(targetDir, { recursive: true });
    const fileCount = copyRecursive(srcDir, targetDir);
    return { success: true, projectPath: targetDir, projectName, fileCount };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, projectPath: '', projectName: '', fileCount: 0, error: `Copy failed: ${msg}` };
  }
}

/**
 * 解决项目名冲突：同名时询问用户是覆盖、重命名还是取消
 */
async function resolveProjectName(workspaceDir: string, desiredName: string): Promise<string | null> {
  const targetPath = path.join(workspaceDir, desiredName);
  if (!fs.existsSync(targetPath)) {
    return desiredName;
  }

  const choice = await vscode.window.showWarningMessage(
    `Project "${desiredName}" already exists in WORKSPACE.`,
    'Overwrite', 'Rename', 'Cancel'
  );

  if (choice === 'Cancel' || !choice) {
    return null;
  }

  if (choice === 'Overwrite') {
    fs.rmSync(targetPath, { recursive: true, force: true });
    return desiredName;
  }

  // Rename：让用户输入新名称
  const newName = await vscode.window.showInputBox({
    prompt: 'Enter a new project name',
    value: `${desiredName}_imported`,
    validateInput: (value) => {
      if (!value || !value.trim()) { return 'Name cannot be empty'; }
      if (fs.existsSync(path.join(workspaceDir, value.trim()))) {
        return `Project "${value.trim()}" already exists`;
      }
      return null;
    }
  });

  return newName ? newName.trim() : null;
}

/**
 * 递归复制目录，返回复制的文件数
 */
function copyRecursive(src: string, dest: string): number {
  let count = 0;
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      fs.mkdirSync(destPath, { recursive: true });
      count += copyRecursive(srcPath, destPath);
    } else if (entry.isFile() && !entry.name.startsWith('.')) {
      const destDir = path.dirname(destPath);
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }
      fs.copyFileSync(srcPath, destPath);
      count++;
    }
  }

  return count;
}
