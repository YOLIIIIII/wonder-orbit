import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Sparkles,
  Star as StarIcon,
  Clock3,
  Coins,
  Zap,
} from "lucide-react";
import type { Energy, Proposal, Star, StarInput } from "./types";

export const split = (text: string) =>
  text
    .split(/[,，\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
export const numeric = (text: string) => (text === "" ? null : Number(text));
export const energyNames = {
  low: "轻轻一点",
  medium: "刚刚好",
  high: "充满能量",
};
export const statusNames: Record<string, string> = {
  collected: "已收藏",
  exploring: "探索中",
  archived: "已归档",
  accepted: "已接受",
  completed: "已完成",
  skipped: "已跳过",
  awaiting_decision: "等待确认",
  decided: "已决定",
  failed: "失败",
  running: "运行中",
  succeeded: "成功",
};
export function ListInput({
  value,
  onChange,
  placeholder,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [raw, setRaw] = useState(value.join(", "));
  useEffect(() => {
    if (JSON.stringify(split(raw)) !== JSON.stringify(value))
      setRaw(value.join(", "));
  }, [raw, value]);
  return (
    <input
      value={raw}
      placeholder={placeholder}
      onChange={(e) => {
        setRaw(e.target.value);
        onChange(split(e.target.value));
      }}
    />
  );
}
export function OrbitArt() {
  return (
    <div className="orbit-art" aria-hidden="true">
      <svg viewBox="0 0 430 310" fill="none">
        <ellipse
          cx="214"
          cy="160"
          rx="170"
          ry="77"
          stroke="#b4a4d7"
          strokeDasharray="5 8"
          transform="rotate(-25 214 160)"
        />
        <ellipse
          cx="214"
          cy="160"
          rx="127"
          ry="110"
          stroke="#d5cbed"
          transform="rotate(30 214 160)"
        />
        <circle cx="214" cy="160" r="68" fill="#8a72c2" />
        <path
          d="M170 174c25-50 65-13 86-49M192 212c17-39 51-24 66-39"
          stroke="#b8a3de"
          strokeWidth="17"
          strokeLinecap="round"
        />
        <ellipse
          cx="214"
          cy="164"
          rx="104"
          ry="25"
          stroke="#e9d391"
          strokeWidth="7"
          transform="rotate(-25 214 164)"
        />
        <path
          d="m329 49 6 17 18 1-14 11 4 18-15-10-15 10 4-18-14-11 18-1Z"
          fill="#edbf51"
        />
        <path
          d="m98 224 4 11 12 1-9 7 2 12-10-6-10 6 3-12-9-7 12-1Z"
          fill="#edbf51"
        />
        <circle cx="98" cy="107" r="11" fill="#f3dca0" />
        <circle cx="328" cy="217" r="7" fill="#9e85c7" />
        <circle cx="260" cy="31" r="3" fill="#bda8dc" />
        <circle cx="56" cy="187" r="3" fill="#bda8dc" />
        <path
          d="M365 153v12m-6-6h12M144 47v10m-5-5h10"
          stroke="#b39acb"
          strokeWidth="2"
        />
      </svg>
      <span className="art-note">每一份好奇，都有自己的轨道。</span>
    </div>
  );
}
export function Empty({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Sparkles size={26} />
      </span>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}
export function StarCard({ star, onOpen }: { star: Star; onOpen: () => void }) {
  return (
    <button className="star-card" onClick={onOpen}>
      <div className="card-top">
        <span className="star-tile">
          <StarIcon size={21} />
        </span>
        <span className="chip">{star.category}</span>
        <ArrowUpRight size={18} />
      </div>
      <h3>{star.title}</h3>
      <p>{star.description || star.original_text}</p>
      <div className="tags">
        {star.tags.map((tag) => (
          <span key={tag}>#{tag}</span>
        ))}
      </div>
      <footer>
        <span>{statusNames[star.status]}</span>
        <time>{new Date(star.created_at).toLocaleDateString("zh-CN")}</time>
      </footer>
    </button>
  );
}
export function StarEditor({
  initial,
  disabled,
  onSave,
  label = "确认保存星星",
  sourceLocked = false,
}: {
  initial: StarInput;
  disabled: boolean;
  onSave: (star: StarInput) => void;
  label?: string;
  sourceLocked?: boolean;
}) {
  const [value, setValue] = useState(initial);
  const set = <K extends keyof StarInput>(key: K, v: StarInput[K]) =>
    setValue((old) => ({ ...old, [key]: v }));
  return (
    <form
      className="editor"
      onSubmit={(e) => {
        e.preventDefault();
        onSave(value);
      }}
    >
      <div className="field-grid">
        <label className="wide">
          标题
          <input
            required
            maxLength={160}
            value={value.title}
            onChange={(e) => set("title", e.target.value)}
          />
        </label>
        <label className="wide">
          原始文字
          <textarea
            required
            readOnly={sourceLocked}
            value={value.original_text}
            onChange={(e) => set("original_text", e.target.value)}
          />
        </label>
        <label className="wide">
          整理后的描述
          <textarea
            value={value.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </label>
        <label>
          兴趣类别
          <input
            required
            maxLength={80}
            value={value.category}
            onChange={(e) => set("category", e.target.value)}
          />
        </label>
        <label>
          标签（逗号分隔）
          <ListInput
            value={value.tags}
            onChange={(tags) => set("tags", tags)}
          />
        </label>
        <label className="wide">
          兴趣原因（只写你明确的想法）
          <input
            value={value.interest_reason || ""}
            onChange={(e) => set("interest_reason", e.target.value || null)}
            placeholder="不知道也可以留空"
          />
        </label>
        <label>
          预计分钟
          <input
            type="number"
            min={1}
            max={1440}
            value={value.estimated_minutes ?? ""}
            onChange={(e) => set("estimated_minutes", numeric(e.target.value))}
          />
        </label>
        <label>
          预计预算（元）
          <input
            type="number"
            min={0}
            step="0.01"
            value={value.estimated_budget ?? ""}
            onChange={(e) => set("estimated_budget", numeric(e.target.value))}
          />
        </label>
        <label>
          精力
          <select
            value={value.energy_level || ""}
            onChange={(e) =>
              set("energy_level", (e.target.value as Energy) || null)
            }
          >
            <option value="">未知</option>
            {Object.entries(energyNames).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label>
          状态
          <select
            value={value.status}
            onChange={(e) =>
              set("status", e.target.value as StarInput["status"])
            }
          >
            <option value="collected">已收藏</option>
            <option value="exploring">探索中</option>
            <option value="archived">已归档</option>
          </select>
        </label>
        <label>
          来源
          <select
            disabled={sourceLocked}
            value={value.source_type}
            onChange={(e) =>
              set("source_type", e.target.value as StarInput["source_type"])
            }
          >
            <option value="manual">手动输入</option>
            <option value="paste">粘贴文字</option>
            <option value="link">链接引用</option>
          </select>
        </label>
        <label>
          参考链接
          <input
            readOnly={sourceLocked}
            type="url"
            value={value.source_reference || ""}
            onChange={(e) => set("source_reference", e.target.value || null)}
          />
        </label>
      </div>
      <button className="primary" disabled={disabled} type="submit">
        <StarIcon size={16} />
        {label}
      </button>
    </form>
  );
}
export function ProposalEditor({
  initial,
  onSave,
  disabled,
}: {
  initial: Proposal;
  onSave: (v: Proposal) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState<Proposal>({
    title: initial.title,
    description: initial.description,
    estimated_minutes: initial.estimated_minutes,
    estimated_budget: initial.estimated_budget,
    energy_level: initial.energy_level,
    steps: initial.steps,
    based_on_star_ids: initial.based_on_star_ids,
    rationale: initial.rationale,
    uncertainties: initial.uncertainties,
  });
  return (
    <form
      className="editor"
      onSubmit={(e) => {
        e.preventDefault();
        onSave(value);
      }}
    >
      <label>
        标题
        <input
          required
          value={value.title}
          onChange={(e) => setValue({ ...value, title: e.target.value })}
        />
      </label>
      <label>
        描述
        <textarea
          required
          value={value.description}
          onChange={(e) => setValue({ ...value, description: e.target.value })}
        />
      </label>
      <div className="field-grid">
        <label>
          分钟
          <input
            type="number"
            required
            min={1}
            max={1440}
            value={value.estimated_minutes}
            onChange={(e) =>
              setValue({ ...value, estimated_minutes: Number(e.target.value) })
            }
          />
        </label>
        <label>
          预算（元）
          <input
            type="number"
            min={0}
            step="0.01"
            value={value.estimated_budget ?? ""}
            onChange={(e) =>
              setValue({ ...value, estimated_budget: numeric(e.target.value) })
            }
          />
        </label>
        <label>
          精力
          <select
            value={value.energy_level}
            onChange={(e) =>
              setValue({ ...value, energy_level: e.target.value as Energy })
            }
          >
            {Object.entries(energyNames).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        步骤（每行一项）
        <textarea
          required
          value={value.steps.join("\n")}
          onChange={(e) =>
            setValue({ ...value, steps: e.target.value.split("\n") })
          }
        />
      </label>
      <label>
        推荐理由
        <textarea
          required
          value={value.rationale}
          onChange={(e) => setValue({ ...value, rationale: e.target.value })}
        />
      </label>
      <label>
        不确定性（每行一项）
        <textarea
          value={value.uncertainties.join("\n")}
          onChange={(e) =>
            setValue({
              ...value,
              uncertainties: e.target.value.split("\n").filter(Boolean),
            })
          }
        />
      </label>
      <p className="muted">保存时后端会再次检查当前约束和依据。</p>
      <button className="primary" disabled={disabled}>
        确认修改并保存
      </button>
    </form>
  );
}
export function ProposalFacts({ proposal }: { proposal: Proposal }) {
  return (
    <div className="facts">
      <span>
        <Clock3 size={15} />
        {proposal.estimated_minutes} 分钟
      </span>
      <span>
        <Coins size={15} />
        {proposal.estimated_budget === null
          ? "预算未知"
          : proposal.estimated_budget === 0
            ? "无需花费"
            : "¥" + proposal.estimated_budget}
      </span>
      <span>
        <Zap size={15} />
        {energyNames[proposal.energy_level]}
      </span>
    </div>
  );
}
