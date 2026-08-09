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
    const [sessionLoaded, setSessionLoaded] = useState(false);
    const [isCheckingAdmin, setIsCheckingAdmin] = useState(true);
    const [apiMessage, setApiMessage] = useState("loading...");

    const fetchSession = async () => {
        const currentSession = await supabase.auth.getSession();
        setSession(currentSession.data.session);
        setSessionLoaded(true);
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
                setSessionLoaded(true);
            }
        );

        return () => {
            authListener.subscription.unsubscribe();
        }
    }, []);

    useEffect(() => {
        if (!sessionLoaded) {
            return;
        }

        console.log("Session updated:", session);
        const user = session?.user;
        let cancelled = false;

        const checkAdmin = async () => {
            if (user) {
                setIsCheckingAdmin(true);
                try {
                    const response = await authenticatedFetch("/api/users/me");
                    if (!response.ok) {
                        console.log("Error fetching admin status:", response.status);
                        if (!cancelled) {
                            setIsAdmin(false);
                        }
                        return;
                    }
                    const payload = await response.json();
                    if (!cancelled) {
                        setIsAdmin(payload.user?.is_admin ?? false);
                    }
                } catch (error) {
                    console.log("Error fetching admin status:", error.message);
                    if (!cancelled) {
                        setIsAdmin(false);
                    }
                } finally {
                    if (!cancelled) {
                        setIsCheckingAdmin(false);
                    }
                }
            } else {
                setIsAdmin(false);
                setIsCheckingAdmin(false);
            }
        }

        checkAdmin();
        return () => {
            cancelled = true;
        };
    }, [session, sessionLoaded]);

    const isLoadingHome = !sessionLoaded || (Boolean(session) && isCheckingAdmin);

    if (isLoadingHome) {
        return (
            <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
                <p className="text-muted-foreground">Loading...</p>
            </div>
        );
    }


    return (<div className="min-h-screen bg-background text-foreground overflow-x-hidden">
        
        {/* Theme Toggle */}
            <ThemeToggle />
        {/* Background Effects */}
            <StarBackground />

        {/* Navbar */}
            <Navbar
                isSignedIn={session}
                isAdmin={isAdmin}
                isSessionLoaded={sessionLoaded}
                isCheckingAdmin={isCheckingAdmin}
            />

        {/* Main Content */}
            <main>
                <HeroSection />
                <span>{apiMessage}</span>
                <AboutSection />
                <ListingsSection />
                <ContactSection />
                <FaqSection />
                <div className="mt-20">
                    {sessionLoaded && !session && <AuthForm className="py-20"/>}
                </div>
                <ChangelogSection />
            </main>

        {/* Footer */}
        <Footer />
    </div>);
};
