"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface LeaderboardChartProps {
  data: Array<{
    name: string;
    score: number;
    rank: number;
  }>;
}

const MEDAL_COLORS = {
  1: '#FFD700', // Gold
  2: '#C0C0C0', // Silver
  3: '#CD7F32', // Bronze
  default: '#8884d8', // Default blue
};

export function LeaderboardChart({ data }: LeaderboardChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="name" className="text-sm" />
        <YAxis className="text-sm" />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '0.5rem',
          }}
        />
        <Legend />
        <Bar dataKey="score" name="Total Score" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={MEDAL_COLORS[entry.rank as keyof typeof MEDAL_COLORS] || MEDAL_COLORS.default}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
