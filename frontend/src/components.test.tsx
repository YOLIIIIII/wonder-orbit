import { fireEvent, render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ListInput,
  ProposalEditor,
  StarEditor,
  StarDetails,
  ProposalFacts,
  split,
} from "./components";
import type { Proposal, StarInput } from "./types";
afterEach(cleanup);
const star: StarInput = {
  title: "海洋",
  original_text: "我想看海",
  description: "海洋",
  category: "自然",
  tags: ["海洋"],
  interest_reason: null,
  source_type: "paste",
  source_reference: null,
  estimated_minutes: null,
  estimated_budget: null,
  energy_level: null,
  status: "collected",
};
describe("星星只读详情的真实字段与安全文本", () => {
  const saved = {
    ...star,
    id: "star",
    created_at: "2026-10-18T00:00:00Z",
    updated_at: "2026-10-18T01:00:00Z",
  };
  it("分别呈现原文和描述；未知值不变成零，空原因不补写", () => {
    render(<StarDetails star={{ ...saved, description: "整理后的内容" }} />);
    expect(screen.getByText("我想看海")).toBeVisible();
    expect(screen.getByText("整理后的内容")).toBeVisible();
    expect(screen.getAllByText("尚未记录")).toHaveLength(3);
    expect(screen.queryByText("0 元")).not.toBeInTheDocument();
    expect(screen.queryByText("兴趣原因")).not.toBeInTheDocument();
    expect(document.querySelector("input,textarea,select")).toBeNull();
  });
  it("只显示真实已填值，预算 0 和来源含义准确", () => {
    render(
      <StarDetails
        star={{
          ...saved,
          estimated_minutes: 12,
          estimated_budget: 0,
          energy_level: "low",
          interest_reason: "想看真实的海",
          source_reference: "https://example.com/notes",
        }}
      />,
    );
    expect(screen.getByText("12 分钟")).toBeVisible();
    expect(screen.getByText("0 元")).toBeVisible();
    expect(screen.getByText("想看真实的海")).toBeVisible();
    expect(screen.getByText("低 · 轻轻一点")).toBeVisible();
    expect(screen.getByRole("link")).toHaveAttribute(
      "href",
      "https://example.com/notes",
    );
    expect(screen.getByRole("link")).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
  });
  it("用户内容是安全文本，非 http/https 来源不可点击，无内部字段名", () => {
    const { container } = render(
      <StarDetails
        star={{
          ...saved,
          original_text: '<img src=x onerror="alert(1)">',
          source_reference: "javascript:alert(1)",
        }}
      />,
    );
    expect(screen.getByText('<img src=x onerror="alert(1)">')).toBeVisible();
    expect(container.querySelector("img,script")).toBeNull();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(container.textContent).not.toMatch(
      /original_text|estimated_budget|energy_level|source_reference/,
    );
  });
});
const proposal: Proposal = {
  title: "写问题",
  description: "记录好奇",
  estimated_minutes: 5,
  estimated_budget: null,
  energy_level: "low",
  steps: ["写三个问题"],
  based_on_star_ids: ["real-id"],
  rationale: "真实记录",
  uncertainties: ["时间是估计"],
};
describe("可确认的编辑流程", () => {
  it("保留未知值，并提交用户修改的字段", () => {
    const save = vi.fn();
    render(
      <StarEditor initial={star} disabled={false} onSave={save} sourceLocked />,
    );
    fireEvent.change(screen.getByLabelText("标题"), {
      target: { value: "深海微光" },
    });
    expect(screen.getByLabelText("原始文字")).toHaveAttribute("readonly");
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "深海微光",
        original_text: star.original_text,
        estimated_budget: null,
        interest_reason: null,
      }),
    );
  });
  it("可以连续输入逗号分隔标签", () => {
    const change = vi.fn();
    render(<ListInput value={["海洋"]} onChange={change} />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "海洋," },
    });
    expect(screen.getByRole("textbox")).toHaveValue("海洋,");
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "海洋,星空" },
    });
    expect(change).toHaveBeenLastCalledWith(["海洋", "星空"]);
  });
  it("编辑正式体验时只提交方案字段，避免将数据库元信息传给严格 API", () => {
    const save = vi.fn();
    render(
      <ProposalEditor
        initial={
          { ...proposal, id: "quest-id", status: "accepted" } as Proposal
        }
        onSave={save}
        disabled={false}
      />,
    );
    fireEvent.change(screen.getByLabelText("预计分钟（必填）"), {
      target: { value: "3" },
    });
    fireEvent.click(screen.getByRole("button", { name: "确认修改并保存" }));
    expect(save).toHaveBeenCalledWith({ ...proposal, estimated_minutes: 3 });
  });
  it("未知预算不会被展示为免费", () => {
    render(<ProposalFacts proposal={proposal} />);
    expect(screen.getByText("预算未知")).toBeInTheDocument();
    expect(screen.queryByText("无需花费")).not.toBeInTheDocument();
  });
  it("标签说明关联输入，保留中英文逗号及换行解析", () => {
    const save = vi.fn();
    render(<StarEditor initial={star} disabled={false} onSave={save} />);
    const tags = screen.getByLabelText("标签（可选）");
    expect(tags).toHaveAccessibleDescription(/中英文逗号或换行分隔/);
    fireEvent.change(tags, { target: { value: "海洋，微光, 观察" } });
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({ tags: ["海洋", "微光", "观察"] }),
    );
    // 单行 HTML input 会移除换行；解析器本身仍支持它，不新增多行控件。
    expect(split("海洋，微光, 观察\n记录\n")).toEqual([
      "海洋",
      "微光",
      "观察",
      "记录",
    ]);
  });
  it("清空已知字段提交 null，零预算保持 0，保留必填与 Schema 范围", () => {
    const save = vi.fn();
    render(
      <StarEditor
        initial={{
          ...star,
          interest_reason: "喜欢微光",
          estimated_minutes: 5,
          estimated_budget: 5,
          energy_level: "medium",
        }}
        disabled={false}
        onSave={save}
      />,
    );
    const reason = screen.getByLabelText("兴趣原因（可选）");
    const minutes = screen.getByLabelText("预计分钟（可选）");
    const budget = screen.getByLabelText("预计预算（元，可选）");
    const energy = screen.getByLabelText("所需精力（可选）");
    expect(reason).toHaveAccessibleDescription(/未知可留空，无需猜测/);
    expect(budget).toHaveAccessibleDescription(/未知留空，0 表示无需花费/);
    expect(energy).toHaveAccessibleDescription(/不代表低精力/);
    expect(screen.getByLabelText("标题")).toBeRequired();
    expect(screen.getByLabelText("标题")).toHaveAttribute("maxlength", "160");
    expect(screen.getByLabelText("原始文字")).toBeRequired();
    expect(screen.getByLabelText("原始文字")).toHaveAttribute(
      "maxlength",
      "12000",
    );
    expect(screen.getByLabelText("兴趣类别")).toBeRequired();
    expect(minutes).not.toBeRequired();
    expect(minutes).toHaveAttribute("min", "1");
    expect(minutes).toHaveAttribute("max", "1440");
    expect(budget).not.toBeRequired();
    expect(budget).toHaveAttribute("min", "0");
    expect(budget).toHaveAttribute("max", "100000");
    const link = screen.getByLabelText("参考链接（可选）");
    expect(link).toHaveAccessibleDescription(
      /仅保存来源，不读取网页，仍需填写原始文字/,
    );
    fireEvent.change(link, { target: { value: "ftp://example.com/notes" } });
    expect(link).toBeInvalid();
    fireEvent.change(link, { target: { value: "http://example.com/notes" } });
    expect(link).toBeValid();
    for (const field of [reason, minutes, budget, energy])
      fireEvent.change(field, { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    expect(save).toHaveBeenLastCalledWith(
      expect.objectContaining({
        interest_reason: null,
        estimated_minutes: null,
        estimated_budget: null,
        energy_level: null,
      }),
    );
    fireEvent.change(budget, { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "确认保存星星" }));
    expect(save).toHaveBeenLastCalledWith(
      expect.objectContaining({ estimated_budget: 0 }),
    );
  });
  it("步骤和不确定性一行一项，逗号留在同项，预算可空", () => {
    const save = vi.fn();
    render(
      <ProposalEditor initial={proposal} disabled={false} onSave={save} />,
    );
    const steps = screen.getByLabelText("步骤（必填，一行一项）");
    expect(steps).toBeRequired();
    expect(steps).toHaveAccessibleDescription(/1–10 项，每项 1–1000 字/);
    expect(screen.getByLabelText("预计分钟（必填）")).toBeRequired();
    expect(screen.getByLabelText("预计分钟（必填）")).toHaveAttribute(
      "max",
      "1440",
    );
    const budget = screen.getByLabelText("预计预算（元，可选）");
    expect(budget).not.toBeRequired();
    expect(budget).toHaveAccessibleDescription(
      /有预算上限时，未知预算无法通过检查/,
    );
    fireEvent.change(steps, { target: { value: "读原文，记问题\n记录感受" } });
    const uncertainties = screen.getByLabelText(
      "不确定性（可选，一行一项，最多 20 项）",
    );
    expect(uncertainties).not.toBeRequired();
    fireEvent.change(uncertainties, {
      target: { value: "时间是估计\n感受未知" },
    });
    fireEvent.click(screen.getByRole("button", { name: "确认修改并保存" }));
    expect(save).toHaveBeenCalledWith(
      expect.objectContaining({
        steps: ["读原文，记问题", "记录感受"],
        uncertainties: ["时间是估计", "感受未知"],
        estimated_budget: null,
      }),
    );
    fireEvent.change(budget, { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "确认修改并保存" }));
    expect(save).toHaveBeenLastCalledWith(
      expect.objectContaining({ estimated_budget: 0 }),
    );
  });
});
