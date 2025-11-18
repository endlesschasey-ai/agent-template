"use client";

import { DataFrameData } from "@/types";

interface DataFrameViewerProps {
  data: DataFrameData;
}

/**
 * DataFrame 表格展示组件
 * 用于展示结构化数据
 */
export default function DataFrameViewer({ data }: DataFrameViewerProps) {
  const { dataframe_name, columns, data: rows } = data;

  return (
    <div className="my-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-800">
      {/* 表格标题 */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          {dataframe_name}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {rows.length} 行 × {columns.length} 列
        </p>
      </div>

      {/* 表格内容 */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700/50">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider border-b border-gray-200 dark:border-gray-700"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {rows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                {row.map((cell, cellIdx) => (
                  <td
                    key={cellIdx}
                    className="px-4 py-3 text-gray-900 dark:text-gray-100 whitespace-nowrap"
                  >
                    {cell !== null && cell !== undefined ? String(cell) : "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
