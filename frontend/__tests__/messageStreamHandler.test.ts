/**
 * MessageStreamHandler 单元测试
 *
 * 测试事件处理器的核心功能
 */

import { MessageStreamHandler, parseSSELine } from '@/utils/messageStreamHandler';
import type { Message, SSEEvent } from '@/types';

describe('MessageStreamHandler', () => {
  let updatedMessage: Message | null = null;
  let streamingComplete = false;

  const mockUpdateMessage = jest.fn((updater) => {
    // 模拟初始消息
    const initialMessage: Message = {
      role: 'assistant',
      content: '',
      streaming: true,
    };
    updatedMessage = updater(initialMessage);
  });

  const mockOnComplete = jest.fn(() => {
    streamingComplete = true;
  });

  beforeEach(() => {
    updatedMessage = null;
    streamingComplete = false;
    mockUpdateMessage.mockClear();
    mockOnComplete.mockClear();
  });

  describe('新协议事件处理', () => {
    test('处理 session_start 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'session_start',
        data: {
          session_id: 'session_123',
          request_id: 'req_123',
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(mockUpdateMessage).toHaveBeenCalled();
      expect(updatedMessage?.metadata?.requestId).toBe('req_123');
    });

    test('处理 thinking 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'thinking',
        data: {
          content: '我正在思考...',
          stage: 'reasoning',
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(updatedMessage?.thinkingContent).toBe('我正在思考...');
    });

    test('处理 tool_call_start 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'tool_call_start',
        data: {
          tool_id: 'tool_001',
          tool_name: 'search_database',
          description: '搜索数据库',
          arguments: { query: 'test' },
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(updatedMessage?.toolCallsMap).toBeDefined();
      expect(updatedMessage?.toolCallsMap?.['tool_001']).toBeDefined();
      expect(updatedMessage?.toolCallsMap?.['tool_001'].tool_name).toBe('search_database');
      expect(updatedMessage?.toolCallsMap?.['tool_001'].status).toBe('calling');
    });

    test('处理 tool_call_end 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      // 先添加 tool_call_start
      const startEvent: SSEEvent = {
        type: 'tool_call_start',
        data: {
          tool_id: 'tool_001',
          tool_name: 'test',
          description: 'test',
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };
      handler.handleEvent(startEvent);

      // 再添加 tool_call_end
      const endEvent: SSEEvent = {
        type: 'tool_call_end',
        data: {
          tool_id: 'tool_001',
          status: 'success',
          result: { count: 5 },
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 2,
          duration_ms: 123,
        },
      };
      handler.handleEvent(endEvent);

      expect(updatedMessage?.toolCallsMap?.['tool_001'].status).toBe('completed');
      expect(updatedMessage?.toolCallsMap?.['tool_001'].result).toEqual({ count: 5 });
    });

    test('处理 content 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'content',
        data: {
          content: '这是答案',
          format: 'markdown',
          is_complete: true,
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(updatedMessage?.mainContent).toBe('这是答案');
    });

    test('处理 data 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'data',
        data: {
          data_type: 'dataframe',
          data: {
            columns: ['A', 'B'],
            data: [[1, 2], [3, 4]],
          },
          metadata: { name: '结果表' },
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(updatedMessage?.dataBlocks).toBeDefined();
      expect(updatedMessage?.dataBlocks?.length).toBe(1);
      expect(updatedMessage?.dataBlocks?.[0].data_type).toBe('dataframe');
    });

    test('处理 error 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'error',
        data: {
          message: '发生错误',
          error_type: 'execution',
          details: {},
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(updatedMessage?.hasError).toBe(true);
      expect(updatedMessage?.errorMessage).toBe('发生错误');
      expect(updatedMessage?.streaming).toBe(false);
      expect(mockOnComplete).toHaveBeenCalled();
    });

    test('处理 session_end 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'session_end',
        data: {
          status: 'completed',
          summary: '成功完成',
          total_duration_ms: 1234,
        },
        metadata: {
          request_id: 'req_123',
          timestamp: Date.now(),
          sequence: 1,
        },
      };

      handler.handleEvent(event);

      expect(updatedMessage?.streaming).toBe(false);
      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  describe('旧协议事件处理（向后兼容）', () => {
    test('处理旧协议 thinking 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'thinking',
        content: '正在思考...',
      };

      handler.handleEvent(event);

      expect(updatedMessage?.thinkingContent).toBe('正在思考...');
    });

    test('处理旧协议 tool_call 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: any = {
        type: 'tool_call',
        tool_id: 'tool_001',
        tool_name: 'test_tool',
        tool_args: '{"key": "value"}',
      };

      handler.handleEvent(event);

      expect(updatedMessage?.toolCalls).toBeDefined();
      expect(updatedMessage?.toolCalls?.length).toBe(1);
      expect(updatedMessage?.toolCalls?.[0].tool_name).toBe('test_tool');
    });

    test('处理旧协议 final_answer 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'final_answer',
        content: '最终答案',
      };

      handler.handleEvent(event);

      expect(updatedMessage?.answerContent).toBe('最终答案');
    });

    test('处理旧协议 done 事件', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      const event: SSEEvent = {
        type: 'done',
      };

      handler.handleEvent(event);

      expect(updatedMessage?.streaming).toBe(false);
      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  describe('累积更新测试', () => {
    test('thinking 内容应该累积', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      handler.handleEvent({
        type: 'thinking',
        data: { content: '第一段' },
        metadata: { request_id: 'req_123', timestamp: Date.now(), sequence: 1 },
      });

      const firstContent = updatedMessage?.thinkingContent;

      handler.handleEvent({
        type: 'thinking',
        data: { content: '第二段' },
        metadata: { request_id: 'req_123', timestamp: Date.now(), sequence: 2 },
      });

      expect(updatedMessage?.thinkingContent).toBe(firstContent + '第二段');
    });

    test('content 内容应该累积', () => {
      const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);

      handler.handleEvent({
        type: 'content',
        data: { content: 'Hello ' },
        metadata: { request_id: 'req_123', timestamp: Date.now(), sequence: 1 },
      });

      handler.handleEvent({
        type: 'content',
        data: { content: 'World' },
        metadata: { request_id: 'req_123', timestamp: Date.now(), sequence: 2 },
      });

      expect(updatedMessage?.mainContent).toBe('Hello World');
    });
  });
});

describe('parseSSELine', () => {
  test('解析有效的 SSE 行', () => {
    const line = 'data: {"type":"thinking","data":{"content":"测试"},"metadata":{"request_id":"req_123","timestamp":1234567890,"sequence":1}}';
    const event = parseSSELine(line);

    expect(event).not.toBeNull();
    expect(event?.type).toBe('thinking');
    expect((event as any).data?.content).toBe('测试');
  });

  test('解析非 SSE 行返回 null', () => {
    const line = 'some random text';
    const event = parseSSELine(line);

    expect(event).toBeNull();
  });

  test('解析无效 JSON 返回 null', () => {
    const line = 'data: {invalid json}';
    const event = parseSSELine(line);

    expect(event).toBeNull();
  });

  test('解析空数据行', () => {
    const line = 'data: ';
    const event = parseSSELine(line);

    expect(event).toBeNull();
  });
});
