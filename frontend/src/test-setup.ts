import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// JSDOM 没有布局/滚动实现；组件断言调用，浏览器再验证真实位置。
Element.prototype.scrollIntoView = vi.fn();
