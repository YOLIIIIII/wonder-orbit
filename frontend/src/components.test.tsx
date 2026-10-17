import { fireEvent, render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ListInput,
  ProposalEditor,
  StarEditor,
  ProposalFacts,
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
    fireEvent.change(screen.getByLabelText("分钟"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "确认修改并保存" }));
    expect(save).toHaveBeenCalledWith({ ...proposal, estimated_minutes: 3 });
  });
  it("未知预算不会被展示为免费", () => {
    render(<ProposalFacts proposal={proposal} />);
    expect(screen.getByText("预算未知")).toBeInTheDocument();
    expect(screen.queryByText("无需花费")).not.toBeInTheDocument();
  });
});
