import * as vscode from 'vscode';
import { ChildProcess, spawn } from 'child_process';

export interface ProgressEvent {
	type: string;
	task_id: string;
	step_id?: string;
	percent?: number;
	message?: string;
	error?: string;
	project?: string;
	workflow?: string;
	agent?: string;
}

export interface TaskState {
	task_id: string;
	project: string;
	workflow: string;
	agent: string;
	status: string;
	percent: number;
	currentStep: string;
	message: string;
	steps: Map<string, StepState>;
}

export interface StepState {
	step_id: string;
	status: string;
	percent: number;
	message: string;
}

type ProgressListener = (event: ProgressEvent, task: TaskState | undefined) => void;

/**
 * 进度服务 — 通过监听 Python 子进程 stdout 获取实时进度。
 *
 * 替代旧的文件监听 + 轮询方案：
 * - Python ProgressTracker 在每次状态变更时输出 `DOCMIND:{json}` 到 stdout
 * - 本服务 spawn Python 进程并逐行解析 stdout
 * - 进度数据存储在内存中，通过回调通知 Dashboard
 */
export class ProgressService implements vscode.Disposable {
	private _processes: Map<string, ChildProcess> = new Map();
	private _tasks: Map<string, TaskState> = new Map();
	private _listeners: ProgressListener[] = [];
	private _outputChannel: vscode.OutputChannel;

	constructor() {
		this._outputChannel = vscode.window.createOutputChannel('DocMind Progress');
	}

	// ── 公共 API ──────────────────────────────────────────────

	/**
	 * 启动一个 Python 进程并监听其 stdout 进度输出。
	 * @param taskId  唯一标识（用于管理多个并发进程）
	 * @param script  Python 脚本路径
	 * @param args    命令行参数
	 * @param cwd     工作目录
	 */
	startProcess(taskId: string, script: string, args: string[], cwd: string): void {
		// 如果已有同名进程，先关闭
		this.stopProcess(taskId);

		const pythonPath = this._findPython();
		const proc = spawn(pythonPath, ['-u', script, ...args], {
			cwd,
			env: { ...process.env, DOCMIND_STDOUT: '1', PYTHONUNBUFFERED: '1' },
			stdio: ['ignore', 'pipe', 'pipe'],
		});

		this._processes.set(taskId, proc);

		// 逐行读取 stdout
		let buffer = '';
		proc.stdout?.on('data', (chunk: Buffer) => {
			buffer += chunk.toString();
			const lines = buffer.split('\n');
			buffer = lines.pop() || '';
			for (const line of lines) {
				this._handleLine(line.trim());
			}
		});

		// stderr → OutputChannel
		proc.stderr?.on('data', (chunk: Buffer) => {
			this._outputChannel.appendLine(chunk.toString());
		});

		proc.on('close', (code) => {
			this._processes.delete(taskId);
			if (code !== 0) {
				this._emit({ type: 'task_fail', task_id: taskId, error: `Process exited with code ${code}` });
			}
		});

		proc.on('error', (err) => {
			this._processes.delete(taskId);
			this._emit({ type: 'task_fail', task_id: taskId, error: err.message });
		});
	}

	/**
	 * 停止指定进程。
	 */
	stopProcess(taskId: string): void {
		const proc = this._processes.get(taskId);
		if (proc && !proc.killed) {
			proc.kill();
		}
		this._processes.delete(taskId);
	}

	/**
	 * 停止所有进程。
	 */
	stopAll(): void {
		for (const [id, proc] of this._processes) {
			if (!proc.killed) {
				proc.kill();
			}
		}
		this._processes.clear();
	}

	/**
	 * 获取指定任务的当前状态。
	 */
	getTask(taskId: string): TaskState | undefined {
		return this._tasks.get(taskId);
	}

	/**
	 * 获取所有活跃任务。
	 */
	getAllTasks(): TaskState[] {
		return Array.from(this._tasks.values());
	}

	/**
	 * 注册进度事件监听器。
	 */
	onProgress(listener: ProgressListener): vscode.Disposable {
		this._listeners.push(listener);
		return {
			dispose: () => {
				const idx = this._listeners.indexOf(listener);
				if (idx >= 0) {
					this._listeners.splice(idx, 1);
				}
			},
		};
	}

	// ── 内部方法 ──────────────────────────────────────────────

	private _handleLine(line: string): void {
		if (!line.startsWith('DOCMIND:')) {
			return;
		}

		try {
			const json = JSON.parse(line.substring(8));
			this._processEvent(json as ProgressEvent);
		} catch {
			// 忽略非 JSON 行
		}
	}

	private _processEvent(event: ProgressEvent): void {
		let task = this._tasks.get(event.task_id);

		switch (event.type) {
			case 'task_create':
				task = {
					task_id: event.task_id,
					project: event.project || '',
					workflow: event.workflow || '',
					agent: event.agent || '',
					status: 'running',
					percent: 0,
					currentStep: '',
					message: '',
					steps: new Map(),
				};
				this._tasks.set(event.task_id, task);
				break;

			case 'step_start':
				if (task && event.step_id) {
					task.steps.set(event.step_id, {
						step_id: event.step_id,
						status: 'running',
						percent: 0,
						message: event.message || '',
					});
					task.currentStep = event.step_id;
					task.status = 'running';
				}
				break;

			case 'step_progress':
				if (task && event.step_id) {
					const step = task.steps.get(event.step_id);
					if (step) {
						step.percent = event.percent || 0;
						step.message = event.message || '';
					}
					task.percent = this._calcTotalPercent(task);
				}
				break;

			case 'step_complete':
				if (task && event.step_id) {
					const step = task.steps.get(event.step_id);
					if (step) {
						step.status = 'completed';
						step.percent = 100;
						step.message = event.message || '';
					}
					task.percent = this._calcTotalPercent(task);
				}
				break;

			case 'step_fail':
				if (task && event.step_id) {
					const step = task.steps.get(event.step_id);
					if (step) {
						step.status = 'failed';
						step.percent = 100;
						step.message = event.error || '';
					}
					task.status = 'failed';
				}
				break;

			case 'task_complete':
				if (task) {
					task.status = 'completed';
					task.percent = 100;
					task.message = event.message || '';
				}
				break;

			case 'task_fail':
				if (task) {
					task.status = 'failed';
					task.message = event.error || '';
				}
				break;
		}

		this._emit(event);
	}

	private _calcTotalPercent(task: TaskState): number {
		if (task.steps.size === 0) {
			return 0;
		}
		let total = 0;
		for (const step of task.steps.values()) {
			total += step.percent;
		}
		return Math.floor(total / task.steps.size);
	}

	private _emit(event: ProgressEvent): void {
		const task = this._tasks.get(event.task_id);
		for (const listener of this._listeners) {
			try {
				listener(event, task);
			} catch {
				// listener 异常不影响其他 listener
			}
		}
	}

	private _findPython(): string {
		// 优先使用 VS Code 配置的 Python 路径
		const config = vscode.workspace.getConfiguration('docmind');
		const configured = config.get<string>('pythonPath');
		if (configured) {
			return configured;
		}
		// 回退到系统 python
		return process.platform === 'win32' ? 'python' : 'python3';
	}

	dispose(): void {
		this.stopAll();
		this._outputChannel.dispose();
	}
}
