import { ThemeToggle } from "../components/ThemeToggle";
import { StarBackground } from "../components/StarBackground";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { ListingsSection } from "../components/listings/ListingsSection";
import { ListingForm } from "../components/listings/ListingForm";
import { useState, useEffect } from "react";
import { supabase } from "../supabase-client";
import { useNavigate } from "react-router-dom";
import { TagManagementSection } from "../components/listings/TagManagementSection";
import { TagForm } from "../components/listings/TagForm";
import { authenticatedFetch } from "@/lib/authenticated-fetch";
import { LogoutButton } from "../components/LogoutButton";
import { ProductsSection } from "../components/products/ProductsSection";

export const Admin = () => {
    const [refreshFlag, setRefreshFlag] = useState(false);
    const triggerRefresh = async () => setRefreshFlag(prev => !prev);
    

    const [session, setSession] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const [sessionLoaded, setSessionLoaded] = useState(false);
    const [isCheckingAdmin, setIsCheckingAdmin] = useState(true);

    const fetchSession = async () => {
        const currentSession = await supabase.auth.getSession();
        setSession(currentSession.data.session);
        setSessionLoaded(true);
    };

    useEffect(() => {
        fetchSession();

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

        if (user) {
            setIsCheckingAdmin(true);
            const fetchAdminStatus = async () => {
                try {
                    const response = await authenticatedFetch("/api/users/me");
                    if (!response.ok) {
                        console.log("Error fetching admin status:", response.status);
                        setIsAdmin(false);
                        return;
                    }
                    const payload = await response.json();
                    setIsAdmin(payload.user?.is_admin ?? false);
                } catch (error) {
                    console.log("Error fetching admin status:", error.message);
                    setIsAdmin(false);
                } finally {
                    setIsCheckingAdmin(false);
                }
            }

            fetchAdminStatus();
        } else {
            setIsAdmin(false);
            setIsCheckingAdmin(false);
        }
    }, [session, sessionLoaded]);

    const navigate = useNavigate();
    const redirectHome = () => {
        navigate("/");
    }

    return <>
                { isCheckingAdmin
                    ? <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
                        <p className="text-muted-foreground">Checking access...</p>
                      </div>
                    : !isAdmin ? <div className="flex flex-col items-start gap-4">
                                <h3 className="font-bold text-3xl mb-10"> Invalid Access </h3>
                                {session && <LogoutButton />}
                                <button onClick={redirectHome} className="cosmic-button"> Back to Home </button>
                             </div>
                             
                           : 
                           <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
                                {/* Theme Toggle */}
                                    <ThemeToggle />
                                {/* Background Effects */}
                                    <StarBackground />

                                {/* Navbar */}
                                    <Navbar isSignedIn={session} isAdmin={isAdmin} />

                                {/* Main Content */}
                                    <main>
                                        <ProductsSection />
                                        <ListingsSection refreshFlag={refreshFlag} triggerRefresh={triggerRefresh} />
                                        <ListingForm onListingCreated={triggerRefresh} />
                                        <TagManagementSection refreshFlag={refreshFlag} onTagUpdate={triggerRefresh} />
                                        <TagForm refreshFlag={refreshFlag} onTagCreated={triggerRefresh} />
                                    </main>

                                {/* Footer */}
                                <Footer />
                            </div>
                }
            </>
};
