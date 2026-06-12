"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

const COLORS = ["#22c55e", "#ef4444", "#f59e0b"];

export function AnnotationChart() {
  const [data, setData] = useState<{ name: string; value: number; color: string }[]>([]);

  useEffect(() => {
    // In production, this would fetch from /api/feedback/stats
    // For now, using the known distribution from our bootstrapping
    setData([
      { name: "Valid", value: 11, color: "#22c55e" },
      { name: "False Positive", value: 8, color: "#ef4444" },
      { name: "Partial", value: 2, color: "#f59e0b" },
    ]);
  }, []);

  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No annotations yet.</p>;
  }

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="space-y-4">
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              dataKey="value"
              label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        {data.map((item) => (
          <div key={item.name}>
            <p className="text-xl font-bold" style={{ color: item.color }}>
              {item.value}
            </p>
            <p className="text-xs text-muted-foreground">{item.name}</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground text-center">
        Total: {total} annotations
      </p>
    </div>
  );
}
