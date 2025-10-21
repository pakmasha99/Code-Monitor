"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface ScoreBreakdownChartProps {
  productivity: number;
  quality: number;
  consistency: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28'];

export function ScoreBreakdownChart({ productivity, quality, consistency }: ScoreBreakdownChartProps) {
  const data = [
    { name: 'Productivity', value: productivity },
    { name: 'Quality', value: quality },
    { name: 'Consistency', value: consistency },
  ].filter(item => item.value > 0); // Only show non-zero values

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
