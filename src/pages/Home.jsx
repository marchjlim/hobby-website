import { ThemeToggle } from "../components/ThemeToggle";
import { StarBackground } from "../components/StarBackground";
import { Navbar } from "../components/Navbar";
import { HeroSection } from "../components/HeroSection";
import { AboutSection } from "../components/AboutSection";
import { ContactSection } from "../components/ContactSection";
import { Footer } from "../components/Footer";
import { FaqSection } from "../components/FaqSection";
import { ListingsSection } from "../components/listings/ListingsSection";
import { AuthForm } from "../components/AuthForm";
import { useEffect, useState } from 'react';
import { supabase } from "../supabase-client";
import { ChangelogSection } from "../components/ChangelogSection";
import { authenticatedFetch } from "@/lib/authenticated-fetch";


export const Home = () => {
    const [session, setSession] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const [apiMessage, setApiMessage] = useState("loading...");

    const fetchSession = async () => {
        const currentSession = await supabase.auth.getSession();
        setSession(currentSession.data.session);
    };

    const fetchApiMessage = async () => {
        const response = await fetch("/api/hello");
        const data = await response.json();
        console.log("data retrieved");
        console.log(data);
        setApiMessage(data.message);
    }

    useEffect(() => {
        fetchSession();
        fetchApiMessage();

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
        const user = session?.user;

        const fetchAdminStatus = async () => {
            const response = await authenticatedFetch("/api/users/me");
            if (!response.ok) {
                console.log("Error fetching admin status:", response.status);
                return;
            }
            const payload = await response.json();
            return payload.user?.is_admin ?? false;
        }

        const checkAdmin = async () => {
            if (user) {
                const adminStatus = await fetchAdminStatus();
                setIsAdmin(adminStatus);
            } else {
                setIsAdmin(false);
            }
        }

        checkAdmin();
    }, [session]);
    
    
    return (<div className="min-h-screen bg-background text-foreground overflow-x-hidden">
        
        {/* Theme Toggle */}
            <ThemeToggle />
        {/* Background Effects */}
            <StarBackground />

        {/* Navbar */}
            <Navbar isSignedIn={session} isAdmin={isAdmin} />

        {/* Main Content */}
            <main>
                <HeroSection />
                <span>{apiMessage}</span>
                <AboutSection />
                <ListingsSection />
                <ContactSection />
                <FaqSection />
                <div className="mt-20">{!session && <AuthForm className="py-20"/>}</div>
                <ChangelogSection />
            </main>

        {/* Footer */}
        <Footer />
    </div>);
};
