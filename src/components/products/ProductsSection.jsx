import { useEffect, useState } from "react";
import { authenticatedFetch } from "@/lib/authenticated-fetch";

export const ProductsSection = () => {
    const [page, setPage] = useState(1);
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [data, setData] = useState({ results: [], total: 0, total_pages: 0 });
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState("");

    useEffect(() => {
        const controller = new AbortController();
        setIsLoading(true);
        setLoadError("");
        authenticatedFetch(`/api/products?page=${page}&q=${encodeURIComponent(search)}`, { signal: controller.signal })
            .then(async (response) => {
                if (!response.ok) throw new Error(`Products API returned ${response.status}`);
                return response.json();
            })
            .then(setData)
            .catch((error) => {
                if (error.name !== "AbortError") setLoadError("Unable to load products right now.");
            })
            .finally(() => setIsLoading(false));
        return () => controller.abort();
    }, [page, search]);

    return (
        <section id="products" className="relative px-4 py-24">
            <div className="container mx-auto max-w-6xl">
                <h2 className="mb-4 text-center text-3xl font-bold md:text-4xl">
                    Product <span className="text-primary">Catalogue</span>
                </h2>
                <form
                    className="mx-auto mb-8 flex max-w-2xl gap-2"
                    onSubmit={(event) => {
                        event.preventDefault();
                        setPage(1);
                        setSearch(searchInput.trim());
                    }}
                >
                    <input
                        type="search"
                        value={searchInput}
                        onChange={(event) => setSearchInput(event.target.value)}
                        placeholder="Search by canonical name"
                        maxLength={100}
                        className="w-full rounded-md border border-input bg-background px-4 py-3 focus:outline-hidden focus:ring-2 focus:ring-primary"
                    />
                    <button type="submit" className="cosmic-button">Search</button>
                </form>                <div className="mb-8 flex justify-between text-foreground/70">
                    <p>{isLoading ? "Loading products..." : `${data.total.toLocaleString()}${search ? " matching" : ""} products`}</p>
                    <p>Page {page} of {data.total_pages || 1}</p>
                </div>

                {loadError ? <p className="text-sm text-red-500">{loadError}</p> : (
                    <div className="overflow-x-auto rounded-lg bg-card shadow-xs">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-primary/15">
                                <tr>
                                    <th className="p-3">Product</th>
                                    <th className="p-3">Grade</th>
                                    <th className="p-3">Scale</th>
                                    <th className="p-3">MSRP</th>
                                    <th className="p-3">Released</th>
                                    <th className="p-3">Last reproduction</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.results.map((product) => (
                                    <tr key={product.id} className="border-t border-border">
                                        <td className="p-3 font-medium">{product.canonical_name}</td>
                                        <td className="p-3">{product.grade || "—"}</td>
                                        <td className="p-3">{product.scale || "—"}</td>
                                        <td className="p-3">{product.msrp == null ? "—" : `${product.msrp_currency} ${Number(product.msrp).toLocaleString()}`}</td>
                                        <td className="p-3">{product.original_release_date || "—"}</td>
                                        <td className="p-3">{product.last_reproduction_date || "—"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                <div className="mt-8 flex justify-between">
                    <button className="cosmic-button disabled:opacity-40" disabled={page === 1 || isLoading} onClick={() => setPage((current) => current - 1)}>Previous</button>
                    <button className="cosmic-button disabled:opacity-40" disabled={page >= data.total_pages || isLoading} onClick={() => setPage((current) => current + 1)}>Next</button>
                </div>
            </div>
        </section>
    );
};
