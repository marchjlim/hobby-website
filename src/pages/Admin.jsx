import { ThemeToggle } from "../components/ThemeToggle";
import { StarBackground } from "../components/StarBackground";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { ListingsSection } from "../components/ListingsSection";
import { ListingForm } from "../components/ListingForm";
import { useState, useEffect } from "react";
import { supabase } from "../supabase-client";
import { useNavigate } from "react-router-dom";

export const Admin = () => {
    const [refreshFlag, setRefreshFlag] = useState(false);
    const triggerRefresh = async () => setRefreshFlag(prev => !prev);
    

    const [session, setSession] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);

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
        const user = session?.user;

        if (user) {
            const fetchAdminStatus = async (userUUID) => {
                const { data, error } = await supabase.from("Users")
                                                        .select("is_admin")
                                                        .eq("auth_user_id", userUUID)
                                                        .single();
                if (error) {
                    console.log("Error fetching admin status for user:", error.message);
                    return;
                }

                return data.is_admin;
            }
            
            fetchAdminStatus(user.id).then((adminStatus) => {
                setIsAdmin(adminStatus);
            });
        } else {
            setIsAdmin(false);
        }
    }, [session]);

    const navigate = useNavigate();
    const redirectHome = () => {
        navigate("/");
    }

    return <>
                { !isAdmin ? <div>
                                <h3 className="font-bold text-3xl mb-10"> Invalid Access </h3>
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
                                        <ListingsSection refreshFlag={refreshFlag} />
                                        <ListingForm onListingCreated={triggerRefresh} />
                                    </main>

                                {/* Footer */}
                                <Footer />
                            </div>
                }
            </>
};