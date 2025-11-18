/**
 * TypeScript type definitions for AI Agent Template
 * 基于 StreamingEngine 协议的完整类型定义
 */

// ==================== Event Metadata ====================

export interface EventMetadata {
  request_id: string;
  timestamp: number;
  sequence: number;
  duration_ms?: number;  // 工具调用结束事件包含此字段
}

// ==================== SSE Event Types (新协议) ====================

export interface SessionStartEvent {
  type: "session_start";
  data: {
    session_id: string;
    request_id: string;
  };
  metadata: EventMetadata;
}

export interface ThinkingEventNew {
  type: "thinking";
  data: {
    content: string;
    stage?: "reasoning" | "planning" | "analyzing";
  };
  metadata: EventMetadata;
}

export interface ToolCallStartEvent {
  type: "tool_call_start";
  data: {
    tool_id: string;
    tool_name: string;
    description: string;
    arguments?: Record<string, any>;
  };
  metadata: EventMetadata;
}

export interface ToolCallEndEvent {
  type: "tool_call_end";
  data: {
    tool_id: string;
    status: "success" | "failed";
    result?: any;
    error?: {
      message: string;
      code?: string;
    };
  };
  metadata: EventMetadata;
}

export interface ContentEvent {
  type: "content";
  data: {
    content: string;
    format: "markdown" | "text" | "html";
    is_complete: boolean;
  };
  metadata: EventMetadata;
}

export interface DataEvent {
  type: "data";
  data: {
    data_type: "dataframe" | "chart" | "image" | "custom";
    data: any;
    metadata?: Record<string, any>;
  };
  metadata: EventMetadata;
}

export interface ErrorEventNew {
  type: "error";
  data: {
    error_type: "validation" | "execution" | "timeout" | "system";
    message: string;
    details?: Record<string, any>;
    recoverable: boolean;
  };
  metadata: EventMetadata;
}

export interface SessionEndEvent {
  type: "session_end";
  data: {
    status: "completed" | "error" | "cancelled";
    summary?: {
      tool_calls?: number;
      data_blocks?: number;
      content_length?: number;
      duration_ms?: number;
      total_events?: number;
    };
  };
  metadata: EventMetadata;
}

// ==================== 向后兼容的旧事件类型 ====================

export interface ThinkingEvent {
  type: "thinking";
  content: string;
}

export interface ToolCallEvent {
  type: "tool_call";
  tool_id: string;
  tool_name: string;
  tool_args: string;
  status: "calling";
}

export interface ToolResultEvent {
  type: "tool_result";
  tool_id: string;
  status: "completed" | "failed";
}

export interface FinalAnswerEvent {
  type: "final_answer";
  content: string;
}

export interface DataFrameEvent {
  type: "dataframe_data";
  data: DataFrameData;
}

export interface DoneEvent {
  type: "done";
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

// 统一的 SSE 事件类型（支持新旧两种格式）
export type SSEEvent =
  | SessionStartEvent
  | ThinkingEventNew
  | ThinkingEvent  // 旧格式
  | ToolCallStartEvent
  | ToolCallEvent  // 旧格式
  | ToolCallEndEvent
  | ToolResultEvent  // 旧格式
  | ContentEvent
  | FinalAnswerEvent  // 旧格式
  | DataEvent
  | DataFrameEvent  // 旧格式
  | ErrorEventNew
  | ErrorEvent  // 旧格式
  | SessionEndEvent
  | DoneEvent;  // 旧格式

// ==================== Message Types ====================

export type MessageRole = "user" | "assistant";

export interface ToolCall {
  id: string;  // tool_id
  tool_name: string;
  description?: string;
  status: "calling" | "completed" | "failed";
  timestamp: number;
  duration_ms?: number;
  arguments?: Record<string, any>;
  tool_args?: string;  // 向后兼容
  result?: any;
  error?: {
    message: string;
    code?: string;
  };
}

export interface DataBlock {
  data_type: "dataframe" | "chart" | "image" | "custom";
  data: any;
  metadata?: Record<string, any>;
}

export interface Message {
  role: MessageRole;
  content: string;  // 主要内容（最终答案或用户输入）
  streaming: boolean;  // 是否正在流式输出
  messageId?: string;  // 消息ID（用于重发功能）

  // 分离的内容类型
  thinkingContent?: string;  // 思考过程（放在折叠框中）
  mainContent?: string;  // 最终答案内容（直接展示）
  answerContent?: string;  // 向后兼容旧字段名

  // 工具调用
  toolCalls?: ToolCall[];  // 数组形式（当前使用）
  toolCallsMap?: Record<string, ToolCall>;  // Map形式（新协议推荐）

  // 结构化数据
  dataBlocks?: DataBlock[];
  dataframeData?: DataFrameData;  // 向后兼容单个数据

  // 错误信息
  hasError?: boolean;
  errorMessage?: string;
  errorType?: "validation" | "execution" | "timeout" | "system";

  // 元数据
  metadata?: {
    requestId?: string;
    startTime?: number;
    endTime?: number;
    sessionStatus?: "completed" | "error" | "cancelled";
  };
}

// ==================== DataFrame Types ====================

export interface DataFrameData {
  type?: "dataframe_display";  // 向后兼容旧格式
  data_type?: "dataframe";  // 新格式
  name?: string;  // 新格式字段
  dataframe_name?: string;  // 旧格式字段
  columns: string[];
  rows?: any[][];  // 新格式
  data?: any[][];  // 旧格式
  metadata?: Record<string, any>;  // 新格式
}

// ==================== Session Types ====================

export interface Session {
  session_id: string;
  title: string;
  created_at: string;
  last_activity_at: string;
  message_count: number;
}

// ==================== File Types ====================

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
}

// ==================== Utility Types ====================

/**
 * 事件处理器类型
 */
export type EventHandler = (event: SSEEvent) => void;

/**
 * 消息更新函数类型
 */
export type MessageUpdater = (updater: (prev: Message) => Message) => void;

/**
 * 类型守卫：检查是否为新协议事件
 */
export function isNewProtocolEvent(event: SSEEvent): event is (
  SessionStartEvent | ThinkingEventNew | ToolCallStartEvent | ToolCallEndEvent |
  ContentEvent | DataEvent | ErrorEventNew | SessionEndEvent
) {
  return 'data' in event && 'metadata' in event;
}

/**
 * 类型守卫：检查是否为旧协议事件
 */
export function isOldProtocolEvent(event: SSEEvent): event is (
  ThinkingEvent | ToolCallEvent | ToolResultEvent | FinalAnswerEvent |
  DataFrameEvent | DoneEvent | ErrorEvent
) {
  return !('data' in event && 'metadata' in event);
}
