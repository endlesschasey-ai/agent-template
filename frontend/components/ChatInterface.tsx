"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, Loader2, Paperclip, X, Image as ImageIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ThinkingCollapse from "./ThinkingCollapse";
import ToolCallDisplay, { ToolCall } from "./ToolCallDisplay";
import DataFrameViewer from "./DataFrameViewer";
import { MessageStreamHandler, parseSSELine } from "@/utils/messageStreamHandler";
import type { Message, MessageRole, DataFrameData } from "@/types";

interface ChatInterfaceProps {
  sessionId: string | null;
  onCreateSession: () => Promise<string>;
}

interface PendingFile {
  file: File;
  preview: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * 聊天界面组件
 * 核心功能：
 * - 流式对话
 * - 思考过程展示
 * - 工具调用可视化
 * - 图片上传
 * - DataFrame 表格展示
 */
export default function ChatInterface({
  sessionId,
  onCreateSession,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() && pendingFiles.length === 0) return;
    if (isStreaming) return;

    // 如果没有会话 ID，先创建会话
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      try {
        currentSessionId = await onCreateSession();
      } catch (error) {
        console.error("创建会话失败:", error);
        return;
      }
    }

    // 上传文件（如果有）
    let fileIds: string[] = [];
    if (pendingFiles.length > 0) {
      setIsUploading(true);
      try {
        fileIds = await uploadPendingFiles(currentSessionId);
      } catch (error) {
        console.error("文件上传失败:", error);
        setIsUploading(false);
        return;
      } finally {
        setIsUploading(false);
      }
    }

    // 添加用户消息
    const userMessage: Message = {
      role: "user" as MessageRole,
      content: input.trim() || "（附件文件）",
      streaming: false,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    // 创建空的 Assistant 消息用于流式输出
    const assistantMessage: Message = {
      role: "assistant" as MessageRole,
      content: "",
      streaming: true,
    };
    setMessages((prev) => [...prev, assistantMessage]);

    // 发送消息
    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          content: userMessage.content,
          file_ids: fileIds.length > 0 ? fileIds : null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // 读取 SSE 流式响应
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("无响应体");
      }

      // 创建消息流处理器
      const handler = new MessageStreamHandler(
        (updater) => {
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg && lastMsg.role === "assistant") {
              newMessages[newMessages.length - 1] = updater(lastMsg);
            }
            return newMessages;
          });
        },
        () => {
          // 流式输出完成回调
          setIsStreaming(false);
        }
      );

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // 解析 SSE 数据
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            const event = parseSSELine(line);
            if (event) {
              handler.handleEvent(event);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error("查询失败:", error);
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg && lastMsg.role === "assistant") {
          lastMsg.content = `❌ 查询失败: ${error instanceof Error ? error.message : "未知错误"}`;
          lastMsg.streaming = false;
        }
        return newMessages;
      });
      setIsStreaming(false);
    }
  };

  // 键盘事件：Enter 发送，Shift+Enter 换行
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const allowedTypes = ["image/jpeg", "image/png", "image/jpg"];
    const filesArray = Array.from(files);

    for (const file of filesArray) {
      if (!allowedTypes.includes(file.type)) {
        alert(`文件 "${file.name}" 格式不支持。仅支持图片（JPG/PNG）`);
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert(`文件 "${file.name}" 超过 10MB 限制`);
        return;
      }
    }

    const newPendingFiles: PendingFile[] = filesArray.map((file) => ({
      file,
      preview: URL.createObjectURL(file)
    }));

    setPendingFiles((prev) => [...prev, ...newPendingFiles]);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // 移除待上传文件
  const handleRemovePendingFile = (index: number) => {
    setPendingFiles((prev) => {
      const newFiles = [...prev];
      const removed = newFiles.splice(index, 1)[0];
      URL.revokeObjectURL(removed.preview);
      return newFiles;
    });
  };

  // 上传待上传的文件
  const uploadPendingFiles = async (currentSessionId: string): Promise<string[]> => {
    const fileIds: string[] = [];

    for (const pendingFile of pendingFiles) {
      const formData = new FormData();
      formData.append("file", pendingFile.file);
      formData.append("session_id", currentSessionId);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`上传 "${pendingFile.file.name}" 失败`);
      }

      const data = await response.json();
      fileIds.push(data.file_id);
    }

    // 清空待上传列表并释放预览URL
    pendingFiles.forEach((pf) => {
      URL.revokeObjectURL(pf.preview);
    });
    setPendingFiles([]);

    return fileIds;
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* 消息列表区域 */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <h3 className="text-3xl font-normal text-gray-800 dark:text-gray-200 mb-3">
              有什么可以帮忙的？
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
              你可以直接开始对话，或者点击下方 📎 按钮上传图片
            </p>
          </div>
        ) : (
          <div className="px-4 py-8">
            <div className="space-y-6 max-w-4xl mx-auto">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`flex ${msg.role === "user" ? "flex-row-reverse" : "flex-row"} items-start gap-3 ${msg.role === "user" ? "max-w-[80%]" : "w-full"}`}>
                    {/* AI 头像 */}
                    {msg.role === "assistant" && (
                      <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0 mt-1">
                        <Bot className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      </div>
                    )}

                    {/* 消息内容 */}
                    <div className="flex-1">
                      <div
                        className={`${
                          msg.role === "user"
                            ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-3xl px-4 py-3"
                            : "text-gray-900 dark:text-gray-100"
                        }`}
                      >
                        {msg.role === "user" ? (
                          <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{msg.content}</p>
                        ) : (
                          <div>
                            {/* 思考过程折叠框 */}
                            <ThinkingCollapse
                              thinkingContent={msg.thinkingContent}
                              toolCalls={msg.toolCalls}
                              isStreaming={msg.streaming}
                            />

                            {/* 最终答案内容（支持新旧协议）*/}
                            {(msg.mainContent || msg.answerContent) && (
                              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-2 prose-p:leading-7">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {msg.mainContent || msg.answerContent || ""}
                                </ReactMarkdown>
                              </div>
                            )}

                            {/* DataFrame 展示（旧协议）*/}
                            {msg.dataframeData && (
                              <DataFrameViewer data={msg.dataframeData} />
                            )}

                            {/* 数据块展示（新协议）*/}
                            {msg.dataBlocks && msg.dataBlocks.length > 0 && (
                              <div className="space-y-4 mt-4">
                                {msg.dataBlocks.map((block, idx) => {
                                  if (block.data_type === 'dataframe') {
                                    return <DataFrameViewer key={idx} data={block.data} />;
                                  }
                                  // 其他数据类型可以在此扩展
                                  return null;
                                })}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="flex-shrink-0 p-4 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800">
        <div className="max-w-3xl mx-auto">
          {/* 待上传文件预览 */}
          {pendingFiles.length > 0 && (
            <div className="mb-3">
              <div className="flex flex-wrap gap-2">
                {pendingFiles.map((pendingFile, index) => (
                  <div
                    key={index}
                    className="group relative flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-lg text-sm border border-blue-200 dark:border-blue-800"
                  >
                    <img
                      src={pendingFile.preview}
                      alt={pendingFile.file.name}
                      className="w-8 h-8 rounded object-cover"
                    />
                    <span className="max-w-[150px] truncate">{pendingFile.file.name}</span>
                    <button
                      onClick={() => handleRemovePendingFile(index)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2 items-end bg-white dark:bg-gray-800 rounded-3xl px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
            {/* 文件上传按钮 */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isStreaming}
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
            >
              {isUploading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Paperclip className="w-5 h-5" />
              )}
            </button>

            {/* 文本输入框 */}
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={isStreaming ? "AI 正在思考..." : "询问任何问题（Shift+Enter 换行）"}
              disabled={isStreaming}
              rows={1}
              className="flex-1 px-2 py-2 bg-transparent focus:outline-none text-gray-900 dark:text-gray-100 disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-gray-500 dark:placeholder:text-gray-400 resize-none overflow-hidden max-h-32"
              style={{ minHeight: '2.5rem' }}
            />

            {/* 发送按钮 */}
            <button
              onClick={handleSend}
              disabled={(!input.trim() && pendingFiles.length === 0) || isStreaming}
              className={`p-2 rounded-lg transition-all flex-shrink-0 ${
                (!input.trim() && pendingFiles.length === 0) || isStreaming
                  ? "text-gray-300 dark:text-gray-600 cursor-not-allowed"
                  : "text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
              }`}
            >
              {isStreaming ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
