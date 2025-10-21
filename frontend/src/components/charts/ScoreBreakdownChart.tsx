"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface ScoreBreakdownChartProps {
  codeLines: number;
  documentLines: number;
}

const COLORS = ['#3b82f6', '#10b981']; // Blue for code, Green for documents

export function ScoreBreakdownChart({ codeLines, documentLines }: ScoreBreakdownChartProps) {
  const total = codeLines + documentLines;

  // If no data, show placeholder
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-[250px] text-muted-foreground">
        <p>No data to display. Submit your weekly work to see breakdown.</p>
      </div>
    );
  }

  const data = [
    { name: 'Code', value: codeLines },
    { name: 'Documents', value: documentLines },
  ].filter(item => item.value > 0); // Only show non-zero values

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }: any) => `${name}: ${((percent as number) * 100).toFixed(0)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => `${value} lines`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
