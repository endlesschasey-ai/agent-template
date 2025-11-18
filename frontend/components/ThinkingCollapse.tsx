"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Brain } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ToolCallDisplay, { ToolCall } from "./ToolCallDisplay";

interface ThinkingCollapseProps {
  thinkingContent?: string;
  toolCalls?: ToolCall[];
  isStreaming?: boolean;
}

/**
 * 思考过程折叠组件
 * 展示 Agent 的思考过程和工具调用
 */
export default function ThinkingCollapse({
  thinkingContent,
  toolCalls,
  isStreaming = false,
}: ThinkingCollapseProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // 如果没有内容也没有工具调用，不渲染组件
  if (!thinkingContent && (!toolCalls || toolCalls.length === 0)) {
    return null;
  }

  const toolCallCount = toolCalls?.length || 0;
  const hasThinkingContent = thinkingContent && thinkingContent.trim().length > 0;

  return (
    <div className="mb-3 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800/50">
      {/* 折叠框头部 */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors"
      >
        {/* 展开/收起图标 */}
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" />
        )}

        {/* 思考图标 */}
        <Brain className="w-4 h-4 text-blue-500 dark:text-blue-400 flex-shrink-0" />

        {/* 标题 */}
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex-1 text-left">
          思考过程
          {isStreaming && (
            <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">(进行中...)</span>
          )}
        </span>

        {/* 统计信息 */}
        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          {toolCallCount > 0 && <span>{toolCallCount} 个工具调用</span>}
        </div>
      </button>

      {/* 折叠内容 */}
      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          {/* 工具调用展示 */}
          {toolCalls && toolCalls.length > 0 && (
            <div className="mb-3 space-y-2">
              <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                工具调用
              </h4>
              {toolCalls.map((toolCall) => (
                <ToolCallDisplay key={toolCall.id} toolCall={toolCall} />
              ))}
            </div>
          )}

          {/* 思考内容展示 */}
          {hasThinkingContent && (
            <div>
              {toolCallCount > 0 && (
                <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                  思考内容
                </h4>
              )}
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-2 prose-p:leading-7 text-gray-600 dark:text-gray-400">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {thinkingContent}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
