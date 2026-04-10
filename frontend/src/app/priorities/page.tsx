"use client";
import { useEffect, useState } from "react";
import { getPriorities, createPriority, updatePriority, Priority } from "@/lib/api";

export default function PrioritiesPage() {
  const [priorities, setPriorities] = useState<Priority[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newWeight, setNewWeight] = useState(0.3);

  const load = () => getPriorities().then(setPriorities);
  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!newName.trim()) return;
    await createPriority({ name: newName, description: newDesc, weight: newWeight });
    setNewName(""); setNewDesc(""); setNewWeight(0.3); setShowAdd(false);
    load();
  };

  const handleWeightChange = async (id: number, weight: number) => {
    await updatePriority(id, { weight });
    load();
  };

  return (
    <div className="p-6 max-w-[800px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[24px] font-semibold">Team Priorities</h1>
          <p className="text-[13px] mt-1" style={{ color: "var(--text-secondary)" }}>
            Define and weight your team&apos;s top priorities. Changes apply to all future analysis.
          </p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="px-4 py-2 rounded-md text-[13px] font-medium text-white"
          style={{ background: "var(--accent-blue)" }}
        >
          + Add Priority
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <div className="card p-5 space-y-3">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Priority name"
            className="w-full px-3 py-2 border rounded-md text-[13px]"
            style={{ borderColor: "var(--border)" }}
          />
          <textarea
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)"
            className="w-full px-3 py-2 border rounded-md text-[13px]"
            style={{ borderColor: "var(--border)" }}
            rows={2}
          />
          <div className="flex items-center gap-3">
            <label className="text-[12px]" style={{ color: "var(--text-secondary)" }}>Weight:</label>
            <input
              type="range" min="0" max="1" step="0.05"
              value={newWeight}
              onChange={(e) => setNewWeight(parseFloat(e.target.value))}
              className="flex-1"
            />
            <span className="text-[13px] font-medium w-12 text-right">{Math.round(newWeight * 100)}%</span>
          </div>
          <div className="flex gap-2">
            <button onClick={handleAdd} className="px-4 py-2 rounded-md text-[13px] font-medium text-white"
              style={{ background: "var(--accent-blue)" }}>Save</button>
            <button onClick={() => setShowAdd(false)} className="px-4 py-2 rounded-md text-[13px]"
              style={{ color: "var(--text-secondary)" }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Priority list */}
      <div className="space-y-3">
        {priorities.map((p) => (
          <div key={p.id} className="card p-5">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-[14px] font-semibold">{p.name}</h3>
                  {!p.active && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100" style={{ color: "var(--text-secondary)" }}>
                      Archived
                    </span>
                  )}
                </div>
                {p.description && (
                  <p className="text-[12px] mt-1" style={{ color: "var(--text-secondary)" }}>{p.description}</p>
                )}
              </div>
              <div className="text-[20px] font-semibold" style={{ color: "var(--accent-blue)" }}>
                {Math.round(p.weight * 100)}%
              </div>
            </div>
            <div className="mt-3 flex items-center gap-3">
              <input
                type="range" min="0" max="1" step="0.05"
                value={p.weight}
                onChange={(e) => handleWeightChange(p.id, parseFloat(e.target.value))}
                className="flex-1"
              />
              <div className="w-2 h-2 rounded-full" style={{
                background: p.weight >= 0.35 ? "var(--green)" : p.weight >= 0.2 ? "var(--warning)" : "var(--red)",
              }} />
            </div>
          </div>
        ))}
      </div>

      {/* Weight distribution visualization */}
      <div className="card p-5">
        <h3 className="text-[14px] font-semibold mb-3">Weight Distribution</h3>
        <div className="flex h-8 rounded-full overflow-hidden">
          {priorities.filter(p => p.active).map((p, i) => {
            const colors = ["var(--chart-navy)", "var(--chart-blue)", "var(--chart-teal)", "var(--chart-pink)"];
            const totalWeight = priorities.filter(q => q.active).reduce((s, q) => s + q.weight, 0);
            const pct = totalWeight > 0 ? (p.weight / totalWeight) * 100 : 0;
            return (
              <div key={p.id} style={{ width: `${pct}%`, background: colors[i % colors.length] }}
                className="flex items-center justify-center text-[10px] text-white font-medium"
                title={`${p.name}: ${Math.round(pct)}%`}>
                {pct > 15 ? `${p.name.split(" ")[0]}` : ""}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
