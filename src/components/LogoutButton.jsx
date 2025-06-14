import { supabase } from "../supabase-client";
import { useToast } from "@/hooks/use-toast";

export const LogoutButton = () => {
  const { toast } = useToast();

  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      toast({ title: "Logout failed", description: error.message, variant: "destructive" });
    } else {
      toast({ title: "Logged out", description: "You have been signed out." });
    }
  };

  return (
    <button onClick={handleLogout} className="cosmic-button">
      Log Out
    </button>
  );
};
