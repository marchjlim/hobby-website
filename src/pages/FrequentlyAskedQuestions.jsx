import { ThemeToggle } from "../components/ThemeToggle";
import { StarBackground } from "../components/StarBackground";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { FaqSection } from "../components/FaqSection";

export const FrequentlyAskedQuestions = () => {
    return (<div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            
            {/* Theme Toggle */}
                <ThemeToggle />
            {/* Background Effects */}
                <StarBackground />
    
            {/* Navbar */}
                <Navbar />
    
            {/* Main Content */}
                <main>
                    <FaqSection />
                </main>
    
            {/* Footer */}
            <Footer />
        </div>);
}