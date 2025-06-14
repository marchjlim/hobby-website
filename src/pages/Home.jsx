import { ThemeToggle } from "../components/ThemeToggle";
import { StarBackground } from "../components/StarBackground";
import { Navbar } from "../components/Navbar";
import { HeroSection } from "../components/HeroSection";
import { AboutSection } from "../components/AboutSection";
import { ContactSection } from "../components/ContactSection";
import { Footer } from "../components/Footer";
import { FaqSection } from "../components/FaqSection";
import { ListingsSection } from "../components/ListingsSection";
import { AuthForm } from "../components/AuthForm";
import { useEffect, useState } from 'react';
import { supabase } from "../supabase-client";


export const Home = () => {
    const [session, setSession] = useState(null);
    const fetchSession = async () => {
        const currentSession = await supabase.auth.getSession();
        setSession(currentSession.data.session);
    };

    useEffect(() => {
        fetchSession();

        const { data: authListener } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                setSession(session);
            }
        );

        return () => {
            authListener.subscription.unsubscribe();
        }
    }, []);

    useEffect(() => {
        console.log("Session updated:", session);
    }, [session]);
    
    
    return (<div className="min-h-screen bg-background text-foreground overflow-x-hidden">
        
        {/* Theme Toggle */}
            <ThemeToggle />
        {/* Background Effects */}
            <StarBackground />

        {/* Navbar */}
            <Navbar isSignedIn={session}/>

        {/* Main Content */}
            <main>
                <HeroSection />
                <AboutSection />
                <ListingsSection />
                <ContactSection />
                <FaqSection />
                {!session && <AuthForm />}
            </main>

        {/* Footer */}
        <Footer />
    </div>);
};