import { useEffect, useId, useState } from "react";
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
  low: "低 · 轻轻一点",
  medium: "中 · 刚刚好",
  high: "高 · 充满能量",
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
  label,
  describedBy,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
  label?: string;
  describedBy?: string;
}) {
  const hintId = useId();
  const [raw, setRaw] = useState(value.join(", "));
  useEffect(() => {
    if (JSON.stringify(split(raw)) !== JSON.stringify(value))
      setRaw(value.join(", "));
  }, [raw, value]);
  return (
    <>
      <input
        aria-label={label}
        aria-describedby={[hintId, describedBy].filter(Boolean).join(" ")}
        value={raw}
        placeholder={placeholder}
        onChange={(e) => {
          setRaw(e.target.value);
          onChange(split(e.target.value));
        }}
      />
      <span className="field-hint" id={hintId}>
        支持中英文逗号或换行分隔；单行输入建议用逗号。
      </span>
    </>
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
  const hintId = useId();
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
      <p className="field-hint">
        标题、原始文字和兴趣类别必填；其余可选，状态与来源已有默认值。
      </p>
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
            maxLength={12000}
            value={value.original_text}
            onChange={(e) => set("original_text", e.target.value)}
          />
        </label>
        <label className="wide">
          整理后的描述
          <textarea
            maxLength={12000}
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
          标签（可选，最多 20 项，每项不超过 80 字）
          <ListInput
            label="标签（可选）"
            value={value.tags}
            onChange={(tags) => set("tags", tags)}
          />
        </label>
        <label className="wide">
          兴趣原因（可选）
          <input
            aria-label="兴趣原因（可选）"
            aria-describedby={hintId + "-reason"}
            maxLength={2000}
            value={value.interest_reason || ""}
            onChange={(e) => set("interest_reason", e.target.value || null)}
            placeholder="不知道也可以留空"
          />
          <span className="field-hint" id={hintId + "-reason"}>
            只写你明确知道的原因；未知可留空，无需猜测。
          </span>
        </label>
        <label>
          预计分钟（可选）
          <input
            aria-label="预计分钟（可选）"
            aria-describedby={hintId + "-minutes"}
            type="number"
            min={1}
            max={1440}
            value={value.estimated_minutes ?? ""}
            onChange={(e) => set("estimated_minutes", numeric(e.target.value))}
          />
          <span className="field-hint" id={hintId + "-minutes"}>
            预计体验所需时长，1–1440 分钟；未知留空。
          </span>
        </label>
        <label>
          预计预算（元，可选）
          <input
            aria-label="预计预算（元，可选）"
            aria-describedby={hintId + "-budget"}
            type="number"
            min={0}
            max={100000}
            step="0.01"
            value={value.estimated_budget ?? ""}
            onChange={(e) => set("estimated_budget", numeric(e.target.value))}
          />
          <span className="field-hint" id={hintId + "-budget"}>
            0–100000 元；未知留空，0 表示无需花费。
          </span>
        </label>
        <label>
          所需精力（可选）
          <select
            aria-label="所需精力（可选）"
            aria-describedby={hintId + "-energy"}
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
          <span className="field-hint" id={hintId + "-energy"}>
            预计体验所需的精力；未知表示尚不清楚，不代表低精力。
          </span>
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
          参考链接（可选）
          <input
            aria-label="参考链接（可选）"
            aria-describedby={hintId + "-reference"}
            readOnly={sourceLocked}
            type="url"
            pattern="[Hh][Tt][Tt][Pp][Ss]?://.+"
            maxLength={2000}
            placeholder="https://example.com/notes"
            value={value.source_reference || ""}
            onChange={(e) => set("source_reference", e.target.value || null)}
          />
          <span className="field-hint" id={hintId + "-reference"}>
            填写完整 http/https 地址。仅保存来源，不读取网页，仍需填写原始文字。
          </span>
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
  const hintId = useId();
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
      <p className="field-hint">
        标题、描述、预计分钟、所需精力、步骤和推荐理由必填；预算和不确定性可选。
      </p>
      <label>
        标题
        <input
          required
          maxLength={160}
          value={value.title}
          onChange={(e) => setValue({ ...value, title: e.target.value })}
        />
      </label>
      <label>
        描述
        <textarea
          required
          maxLength={4000}
          value={value.description}
          onChange={(e) => setValue({ ...value, description: e.target.value })}
        />
      </label>
      <div className="field-grid">
        <label>
          预计分钟（必填）
          <input
            aria-label="预计分钟（必填）"
            aria-describedby={hintId + "-minutes"}
            type="number"
            required
            min={1}
            max={1440}
            value={value.estimated_minutes}
            onChange={(e) =>
              setValue({ ...value, estimated_minutes: Number(e.target.value) })
            }
          />
          <span className="field-hint" id={hintId + "-minutes"}>
            预计所需时长，1–1440 分钟；保存时还需符合本次与偏好的时间范围。
          </span>
        </label>
        <label>
          预计预算（元，可选）
          <input
            aria-label="预计预算（元，可选）"
            aria-describedby={hintId + "-budget"}
            type="number"
            min={0}
            max={100000}
            step="0.01"
            value={value.estimated_budget ?? ""}
            onChange={(e) =>
              setValue({ ...value, estimated_budget: numeric(e.target.value) })
            }
          />
          <span className="field-hint" id={hintId + "-budget"}>
            0–100000 元；未知留空，0
            表示无需花费。有预算上限时，未知预算无法通过检查。
          </span>
        </label>
        <label>
          所需精力（必选）
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
        步骤（必填，一行一项）
        <textarea
          aria-label="步骤（必填，一行一项）"
          aria-describedby={hintId + "-steps"}
          required
          value={value.steps.join("\n")}
          onChange={(e) =>
            setValue({ ...value, steps: e.target.value.split("\n") })
          }
        />
        <span className="field-hint" id={hintId + "-steps"}>
          1–10 项，每项 1–1000 字；逗号不会拆分步骤。
        </span>
      </label>
      <label>
        推荐理由（必填）
        <textarea
          required
          maxLength={4000}
          value={value.rationale}
          onChange={(e) => setValue({ ...value, rationale: e.target.value })}
        />
      </label>
      <label>
        不确定性（可选，一行一项，最多 20 项）
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
