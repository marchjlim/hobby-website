import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from '@/lib/utils';

export const ThemeToggle = () => {
    const [isDarkMode, setIsDarkMode] = useState(false);

    useEffect(() => {
        const storedTheme = localStorage.getItem("theme")
        if (storedTheme === "dark") {
            setIsDarkMode(true);
            document.documentElement.classList.add("dark"); // add dark theme to indicate dark
        } else {
            setIsDarkMode(false);
            localStorage.setItem("theme", "light"); // set "theme" object to "light" in case it was not "dark" before
            // no need to remove "dark" because by default is light theme.
        }
    }, [])

    const toggleTheme = () => {
        if (isDarkMode) {
            document.documentElement.classList.remove("dark");
            localStorage.setItem("theme", "light");
            setIsDarkMode(false);
        } else {
            document.documentElement.classList.add("dark");
            localStorage.setItem("theme", "dark");
            setIsDarkMode(true);
        }
    }

    return <button 
                onClick={toggleTheme}
                title={isDarkMode ? "Enable light mode" : "Enable dark mode"} 
                className={cn(
                            "fixed max-sm:hidden top-0 right-0 z-50 p-2 rounded-full transition-colors duration-300",
                            "focus:outlin-hidden"
                            )}
                        >
        {isDarkMode ? <Sun className="h-6 w-6 text-yellow-300"/> 
                    : <Moon className="h-6 w-6 text-blue-900"/>}
    </button>
}