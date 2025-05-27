import { ThemeToggle } from "../components/ThemeToggle";
import { StarBackground } from "../components/StarBackground";
import { Navbar } from "../components/Navbar";
import { HeroSection } from "../components/HeroSection";
import { AboutSection } from "../components/AboutSection";
import { ContactSection } from "../components/ContactSection";
import { Footer } from "../components/Footer";
import { FaqSection } from "../components/FaqSection";
import { ListingsSection } from "../components/ListingsSection";
import { List } from "lucide-react";
import { ListingForm } from "../components/ListingForm";

export const Admin = () => {
    return (<div className="min-h-screen bg-background text-foreground overflow-x-hidden">
        
        {/* Theme Toggle */}
            <ThemeToggle />
        {/* Background Effects */}
            <StarBackground />

        {/* Navbar */}
            <Navbar />

        {/* Main Content */}
            <main>
                <ListingsSection />
                <ListingForm />
            </main>

        {/* Footer */}
        <Footer />
    </div>);
};