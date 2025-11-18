"use client";

import { useState, useEffect } from "react";
import {
  Wrench,
  CheckCircle2,
  Loader2,
  Table,
  MessageSquare,
} from "lucide-react";

export interface ToolCall {
  id: string;
  tool_name: string;
  tool_args?: string;
  status: "calling" | "completed" | "failed";
  timestamp: number;
}

interface ToolCallDisplayProps {
  toolCall: ToolCall;
}

/** 工具图标和中文名称映射 */
const TOOL_INFO: Record<string, { icon: any; label: string; color: string }> = {
  finalize_answer: {
    icon: MessageSquare,
    label: "输出最终答案",
    color: "text-green-500"
  },
  display_table: {
    icon: Table,
    label: "展示表格",
    color: "text-blue-500"
  },
};

/**
 * 工具调用展示组件
 * 优雅展示 Agent 的工具调用过程
 */
export default function ToolCallDisplay({ toolCall }: ToolCallDisplayProps) {
  const [isAnimating, setIsAnimating] = useState(true);

  // 获取工具信息
  const toolInfo = TOOL_INFO[toolCall.tool_name] || {
    icon: Wrench,
    label: toolCall.tool_name,
    color: "text-gray-500"
  };

  const Icon = toolInfo.icon;

  // 动画效果
  useEffect(() => {
    if (toolCall.status === "completed" || toolCall.status === "failed") {
      setTimeout(() => setIsAnimating(false), 300);
    }
  }, [toolCall.status]);

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-lg mb-2
        transition-all duration-300 ease-in-out
        ${toolCall.status === "calling"
          ? "bg-blue-50 border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800 animate-pulse"
          : toolCall.status === "completed"
          ? "bg-green-50 border border-green-200 dark:bg-green-900/20 dark:border-green-800"
          : "bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800"
        }
      `}
    >
      {/* 工具图标 */}
      <div className={`flex-shrink-0 ${toolInfo.color}`}>
        {toolCall.status === "calling" ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : toolCall.status === "completed" ? (
          <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
        ) : (
          <Icon className="w-5 h-5" />
        )}
      </div>

      {/* 工具信息 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
            {toolInfo.label}
          </span>
          {toolCall.status === "calling" && (
            <span className="text-xs text-blue-600 dark:text-blue-400 animate-pulse">
              执行中...
            </span>
          )}
          {toolCall.status === "completed" && (
            <span className="text-xs text-green-600 dark:text-green-400">
              ✓ 完成
            </span>
          )}
        </div>
      </div>

      {/* 时间戳 */}
      <div className="flex-shrink-0 text-xs text-gray-400 dark:text-gray-500">
        {new Date(toolCall.timestamp).toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })}
      </div>
    </div>
  );
}
