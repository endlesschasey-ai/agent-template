"use client";

import { useState } from "react";
import ChatInterface from "@/components/ChatInterface";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  // 创建新会话
  const handleCreateSession = async (): Promise<string> => {
    try {
      const response = await fetch(`${API_URL}/api/session/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "新对话",
        }),
      });

      if (!response.ok) {
        throw new Error("创建会话失败");
      }

      const data = await response.json();
      setSessionId(data.session_id);
      return data.session_id;
    } catch (error) {
      console.error("创建会话失败:", error);
      throw error;
    }
  };

  return (
    <main className="h-screen flex flex-col">
      {/* 头部 */}
      <header className="flex-shrink-0 h-16 border-b border-gray-200 dark:border-gray-800 flex items-center px-6 bg-white dark:bg-gray-900">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          AI Agent 模板
        </h1>
      </header>

      {/* 主内容区域 */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface
          sessionId={sessionId}
          onCreateSession={handleCreateSession}
        />
      </div>
    </main>
  );
}
