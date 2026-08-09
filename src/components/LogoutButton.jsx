import { useNavigate } from "react-router-dom";
import { supabase } from "../supabase-client";
import { useToast } from "@/hooks/use-toast";

export const LogoutButton = () => {
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      // An expired/revoked server session should not trap the user in the UI.
      const { error: localError } = await supabase.auth.signOut({ scope: "local" });
      if (localError) {
        toast({ title: "Logout failed", description: error.message, variant: "destructive" });
        return;
      }
    }
    toast({ title: "Logged out", description: "You have been signed out." });
    navigate("/");
  };

  return (
    <button onClick={handleLogout} className="cosmic-button">
      Log Out
    </button>
  );
};
