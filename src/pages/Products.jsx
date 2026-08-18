import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ThemeToggle } from "../components/ThemeToggle";
import { ProductsSection } from "../components/products/ProductsSection";
import { authenticatedFetch } from "@/lib/authenticated-fetch";

export const Products = () => {
    const [isAdmin, setIsAdmin] = useState(null);

    useEffect(() => {
        authenticatedFetch("/api/users/me")
            .then(async (response) => response.ok ? response.json() : null)
            .then((payload) => setIsAdmin(payload?.user?.is_admin === true))
            .catch(() => setIsAdmin(false));
    }, []);

    if (isAdmin === null) {
        return <main className="min-h-screen bg-background p-16 text-foreground">Checking access...</main>;
    }
    if (!isAdmin) {
        return <main className="min-h-screen bg-background p-16 text-foreground">Admin access required. <Link to="/" className="text-primary hover:underline">Back to home</Link></main>;
    }

    return (
        <main className="min-h-screen bg-background text-foreground">
            <ThemeToggle />
            <div className="mx-auto max-w-6xl px-4 pt-16">
                <Link to="/secret-admin-page" className="text-primary hover:underline">Back to admin</Link>
            </div>
            <ProductsSection />
        </main>
    );
};
