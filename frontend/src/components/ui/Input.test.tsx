import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { Input } from "./Input";

describe("Input", () => {
  it("renders correctly", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("accepts user input", async () => {
    const user = userEvent.setup();
    render(<Input placeholder="Type here" />);

    const input = screen.getByPlaceholderText("Type here");
    await user.type(input, "Hello World");

    expect(input).toHaveValue("Hello World");
  });

  it("calls onChange handler when typing", async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<Input onChange={handleChange} />);
    await user.type(screen.getByRole("textbox"), "test");

    expect(handleChange).toHaveBeenCalled();
  });

  it("displays error message when error prop is provided", () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("applies error styling when error prop is provided", () => {
    render(<Input error="Error" data-testid="input" />);
    const input = screen.getByTestId("input");
    expect(input).toHaveClass("border-destructive");
  });

  it("is disabled when disabled prop is true", () => {
    render(<Input disabled placeholder="Disabled" />);
    expect(screen.getByPlaceholderText("Disabled")).toBeDisabled();
  });

  it("supports different input types", () => {
    const { rerender } = render(<Input type="email" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveAttribute("type", "email");

    rerender(<Input type="password" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveAttribute("type", "password");

    rerender(<Input type="number" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveAttribute("type", "number");
  });

  it("forwards ref correctly", () => {
    const ref = vi.fn();
    render(<Input ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });

  it("merges custom className with default classes", () => {
    render(<Input className="custom-class" data-testid="input" />);
    const input = screen.getByTestId("input");
    expect(input).toHaveClass("custom-class");
    expect(input).toHaveClass("flex"); // Default class
  });

  it("supports name attribute for form handling", () => {
    render(<Input name="email" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveAttribute("name", "email");
  });

  it("supports value prop for controlled inputs", () => {
    render(<Input value="Controlled value" readOnly data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveValue("Controlled value");
  });
});
