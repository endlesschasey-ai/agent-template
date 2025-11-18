/**
 * MessageStreamHandler - 统一处理新旧两种 SSE 协议
 *
 * 功能：
 * - 自动检测事件协议版本（新协议带 data/metadata，旧协议直接字段）
 * - 将事件转换为 Message 状态更新
 * - 支持所有事件类型的处理
 */

import type {
  SSEEvent,
  Message,
  ToolCall,
  DataBlock,
  isNewProtocolEvent,
  isOldProtocolEvent
} from "@/types";

export type MessageUpdater = (updater: (prev: Message) => Message) => void;

export class MessageStreamHandler {
  private updateMessage: MessageUpdater;
  private onStreamingComplete?: () => void;

  constructor(
    updateMessage: MessageUpdater,
    onStreamingComplete?: () => void
  ) {
    this.updateMessage = updateMessage;
    this.onStreamingComplete = onStreamingComplete;
  }

  /**
   * 处理单个 SSE 事件
   */
  handleEvent(event: SSEEvent): void {
    // 检测协议版本
    if ('data' in event && 'metadata' in event) {
      this.handleNewProtocolEvent(event);
    } else {
      this.handleOldProtocolEvent(event);
    }
  }

  /**
   * 处理新协议事件
   */
  private handleNewProtocolEvent(event: SSEEvent): void {
    if (!('data' in event && 'metadata' in event)) return;

    switch (event.type) {
      case 'session_start':
        this.handleSessionStart(event);
        break;

      case 'thinking':
        this.handleThinkingNew(event);
        break;

      case 'tool_call_start':
        this.handleToolCallStart(event);
        break;

      case 'tool_call_end':
        this.handleToolCallEnd(event);
        break;

      case 'content':
        this.handleContent(event);
        break;

      case 'data':
        this.handleData(event);
        break;

      case 'error':
        this.handleErrorNew(event);
        break;

      case 'session_end':
        this.handleSessionEnd(event);
        break;
    }
  }

  /**
   * 处理旧协议事件（向后兼容）
   */
  private handleOldProtocolEvent(event: SSEEvent): void {
    switch (event.type) {
      case 'thinking':
        if ('content' in event && typeof event.content === 'string') {
          this.handleThinkingOld(event);
        }
        break;

      case 'tool_call':
        if ('tool_id' in event) {
          this.handleToolCallOld(event);
        }
        break;

      case 'tool_result':
        if ('tool_id' in event) {
          this.handleToolResultOld(event);
        }
        break;

      case 'final_answer':
        if ('content' in event && typeof event.content === 'string') {
          this.handleFinalAnswer(event);
        }
        break;

      case 'dataframe_data':
        if ('data' in event) {
          this.handleDataFrameOld(event);
        }
        break;

      case 'done':
        this.handleDone();
        break;

      case 'error':
        if ('message' in event) {
          this.handleErrorOld(event);
        }
        break;
    }
  }

  // ==================== 新协议事件处理 ====================

  private handleSessionStart(event: Extract<SSEEvent, { type: 'session_start' }>): void {
    this.updateMessage(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        requestId: event.data.request_id,
        startTime: event.metadata.timestamp,
      }
    }));
  }

  private handleThinkingNew(event: Extract<SSEEvent, { type: 'thinking' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => ({
      ...prev,
      thinkingContent: (prev.thinkingContent || '') + event.data.content
    }));
  }

  private handleToolCallStart(event: Extract<SSEEvent, { type: 'tool_call_start' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => {
      const newToolCall: ToolCall = {
        id: event.data.tool_id,
        tool_name: event.data.tool_name,
        description: event.data.description,
        status: 'calling',
        timestamp: event.metadata.timestamp,
        arguments: event.data.arguments,
      };

      // 使用 toolCallsMap（推荐）
      const toolCallsMap = { ...(prev.toolCallsMap || {}) };
      toolCallsMap[event.data.tool_id] = newToolCall;

      // 同时更新 toolCalls 数组（向后兼容）
      const toolCalls = [...(prev.toolCalls || []), newToolCall];

      return {
        ...prev,
        toolCallsMap,
        toolCalls
      };
    });
  }

  private handleToolCallEnd(event: Extract<SSEEvent, { type: 'tool_call_end' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => {
      // 更新 toolCallsMap
      const toolCallsMap = { ...(prev.toolCallsMap || {}) };
      if (toolCallsMap[event.data.tool_id]) {
        toolCallsMap[event.data.tool_id] = {
          ...toolCallsMap[event.data.tool_id],
          status: event.data.status === 'success' ? 'completed' : 'failed',
          duration_ms: event.metadata.duration_ms,
          result: event.data.result,
          error: event.data.error,
        };
      }

      // 同步更新 toolCalls 数组
      const toolCalls = (prev.toolCalls || []).map(tc => {
        if (tc.id === event.data.tool_id) {
          return {
            ...tc,
            status: event.data.status === 'success' ? 'completed' : 'failed',
            duration_ms: event.metadata.duration_ms,
            result: event.data.result,
            error: event.data.error,
          };
        }
        return tc;
      });

      return {
        ...prev,
        toolCallsMap,
        toolCalls
      };
    });
  }

  private handleContent(event: Extract<SSEEvent, { type: 'content' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => ({
      ...prev,
      mainContent: (prev.mainContent || '') + event.data.content
    }));
  }

  private handleData(event: Extract<SSEEvent, { type: 'data' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => {
      const newDataBlock: DataBlock = {
        data_type: event.data.data_type,
        data: event.data.data,
        metadata: event.data.metadata,
      };

      return {
        ...prev,
        dataBlocks: [...(prev.dataBlocks || []), newDataBlock]
      };
    });
  }

  private handleErrorNew(event: Extract<SSEEvent, { type: 'error' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => ({
      ...prev,
      hasError: true,
      errorMessage: event.data.message,
      errorType: event.data.error_type,
      streaming: false,
    }));

    this.onStreamingComplete?.();
  }

  private handleSessionEnd(event: Extract<SSEEvent, { type: 'session_end' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => ({
      ...prev,
      streaming: false,
      metadata: {
        ...prev.metadata,
        endTime: event.metadata.timestamp,
        sessionStatus: event.data.status,
      }
    }));

    this.onStreamingComplete?.();
  }

  // ==================== 旧协议事件处理（向后兼容）====================

  private handleThinkingOld(event: Extract<SSEEvent, { type: 'thinking', content: string }>): void {
    this.updateMessage(prev => ({
      ...prev,
      thinkingContent: (prev.thinkingContent || '') + event.content
    }));
  }

  private handleToolCallOld(event: any): void {
    this.updateMessage(prev => {
      const newToolCall: ToolCall = {
        id: event.tool_id || `${event.tool_name}-${Date.now()}`,
        tool_name: event.tool_name,
        tool_args: event.tool_args,
        status: 'calling',
        timestamp: Date.now()
      };

      return {
        ...prev,
        toolCalls: [...(prev.toolCalls || []), newToolCall]
      };
    });
  }

  private handleToolResultOld(event: any): void {
    this.updateMessage(prev => {
      const toolCalls = (prev.toolCalls || []).map(tc => {
        if (tc.id === event.tool_id && tc.status === 'calling') {
          return {
            ...tc,
            status: event.status === 'completed' ? 'completed' as const : 'failed' as const
          };
        }
        return tc;
      });

      return {
        ...prev,
        toolCalls
      };
    });
  }

  private handleFinalAnswer(event: Extract<SSEEvent, { type: 'final_answer', content: string }>): void {
    this.updateMessage(prev => ({
      ...prev,
      answerContent: (prev.answerContent || '') + event.content
    }));
  }

  private handleDataFrameOld(event: Extract<SSEEvent, { type: 'dataframe_data' }>): void {
    if (!('data' in event)) return;

    this.updateMessage(prev => ({
      ...prev,
      dataframeData: event.data
    }));
  }

  private handleDone(): void {
    this.updateMessage(prev => ({
      ...prev,
      streaming: false
    }));

    this.onStreamingComplete?.();
  }

  private handleErrorOld(event: Extract<SSEEvent, { type: 'error', message: string }>): void {
    this.updateMessage(prev => ({
      ...prev,
      hasError: true,
      errorMessage: event.message,
      streaming: false,
    }));

    this.onStreamingComplete?.();
  }
}

/**
 * 解析 SSE 数据行
 * @param line SSE 数据行（格式：data: {...}）
 * @returns 解析后的事件对象，解析失败返回 null
 */
export function parseSSELine(line: string): SSEEvent | null {
  if (!line.startsWith('data: ')) {
    return null;
  }

  const jsonStr = line.slice(6); // 移除 "data: " 前缀

  try {
    const event = JSON.parse(jsonStr) as SSEEvent;
    return event;
  } catch (e) {
    // 忽略不完整的 JSON 片段
    return null;
  }
}
