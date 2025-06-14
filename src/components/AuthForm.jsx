import { useState } from "react";
import { supabase } from "../supabase-client"; 
import { useToast } from "@/hooks/use-toast"; 

export const AuthForm = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    const { email, password } = formData;

    try {
        let authData = null;

        if (isSignUp) {
            const { error: signUpError, data } = await supabase.auth.signUp({ email, password });
            if (signUpError) {
                toast({
                    title: "Sign in error",
                    description: signUpError.message,
                    variant: "destructive",
                });
                setIsSubmitting(false);
                return;
            }

            if (data.user) {
                await supabase.from("Users").upsert([
                    { email: email, is_admin: false, auth_user_id: data.user.id }
                ]);
            }
            authData = data;

        } else {
            const { error: signInError, data } = await supabase.auth.signInWithPassword({ email, password });
            if (signInError) {
                toast({
                    title: "Sign in error",
                    description: signInError.message,
                    variant: "destructive",
                });
                setIsSubmitting(false);
                return;
            }

            if (data.user) {
                await supabase.from("Users").upsert([
                    { email: email, is_admin: false, auth_user_id: data.user.id }
                ]);
            }
            authData = data;
        }

        if (authData.session) {
            // logged in
            toast({ title: "Signed in!", description: "Enjoy viewing!" });
        } else {
            toast({
                title: "Check your inbox",
                description: "You may need to confirm your email before logging in.",
            });
        }

    } catch (err) {
        toast({ title: "Error", description: err.message });
        setIsSubmitting(false);
    }

    
    setIsSubmitting(false);
    setFormData({
        email: "",
        password: "",
    });
  };

  return (
    <div id="login" className="w-full max-w-md bg-card p-6 rounded-lg shadow-md mx-auto">
      <h2 className="text-2xl font-bold text-center">
        {isSignUp ? "Create Account" : "Sign In"}
      </h2>
      <div className="text-sm font-semibold text-center mb-4">
        Note: Accounts are currently only relevant for developers.
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input
          type="email"
          placeholder="Email"
          required
          className="px-4 py-2 border border-input rounded-md"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />
        <input
          type="password"
          placeholder="Password"
          required
          className="px-4 py-2 border border-input rounded-md"
          value={formData.password}
          onChange={(e) =>
            setFormData({ ...formData, password: e.target.value })
          }
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="cosmic-button disabled:opacity-50"
        >
          {isSignUp ? "Sign Up" : "Sign In"}
        </button>
      </form>
      <p className="text-center mt-4 text-sm text-muted-foreground">
        {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
        <button
          onClick={() => setIsSignUp(!isSignUp)}
          className="underline font-medium"
        >
          {isSignUp ? "Sign in" : "Sign up"}
        </button>
      </p>
    </div>
  );
};
