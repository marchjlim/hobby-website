import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from '@/lib/utils';

export const ExpandableButton = ({
  title,
  content,
  defaultOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="cosmic-button">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn("w-full flex items-center justify-between px-4 py-2 bg-primary text-primary-foreground",
                      "rounded-md transition-all duration-300")}
      >
        <span className="text-glow text-lg">{title}</span>
        <ChevronDown className={cn("transition-transform duration-300", isOpen ? "rotate-180" : "")} />
      </button>

      <div
        className={cn(
            "transition-all duration-300 overflow-hidden px-4",
            isOpen ? "max-h-96 opacity-100 overflow-y-auto" : "max-h-0 opacity-0"
        )}
      >
        <div className="text-muted-foreground text-left text-sm">{content}</div>
      </div>
    </div>
  );
};
