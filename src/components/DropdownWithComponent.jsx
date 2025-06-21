import { useState, useRef } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export const DropdownWithComponent = ({ title, content }) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef();


  return (
    <div ref={ref} className="relative inline-block text-left w-full">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="cosmic-button flex items-center justify-between w-full"
      >
        <span>{isOpen ? "Collapse" : title}</span>
        <ChevronDown className={cn("transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div
          className={cn(
            "mt-4 w-full w-[800px] relative left-1/2 transform -translate-x-1/2 max-h-[600px] overflow-auto bg-card border border-border rounded-lg shadow-lg p-4"
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
};
