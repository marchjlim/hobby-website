import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useLocation } from "react-router-dom";
import { ListingsContainer } from "./ListingsContainer";


// const listings = [
//     {name: "MG Rezel type C defenser a + b unit", categories: ["MG", "Regular release", "1/100", "in-stock"], url: "", image: "/listings/rezel_type_c.jpg"},
//     {name: "MG Tallgeese III special coating", categories: ["MG", "Event-limited", "1/100", "in-stock", "special coating"], url: "", image: "/listings/mg_tallgeese_III_special_coating.png"},
//     {name: "RG Banshee Final battle special coating", categories: ["RG", "Premium Bandai", "1/144", "in-stock", "special coating"], url: "", image: "/listings/rg_banshee_special_coating.jpg"},
//     {name: "RG Unicorn Final battle special coating", categories: ["RG", "Gundam base limited", "1/144", "in-stock", "special coating"], url: "", image:"/listings/rg_unicorn_special_coating.jpg"},
// ]

export const ListingsSection = ({ refreshFlag, triggerRefresh }) => {
    const [activeTag, setActiveTag] = useState("all");
    const [searchQuery, setSearchQuery] = useState("");

    const [listings, setListings] = useState([]);
    const [tags, setTags] = useState([]);
    const [loadError, setLoadError] = useState("");

    const location = useLocation();
    const isAdminPage = location.pathname === "/secret-admin-page";

    const fetchAllTags = async () => {
        try {
            const response = await fetch("/api/listings/tags");

            if (!response.ok) {
                throw new Error(`Error while fetching all tags: ${response.status}`);
            }
            const payload = await response.json();
            const tagsData = payload.results ?? [];
            setTags(tagsData.map(tagRow => tagRow.name));
        } catch (error) {
            console.error("Error fetching tags", error.message);
        }
    }

    const fetchListings = async () => {
        try {
            const response = await fetch("/api/listings/withtags");

            if (!response.ok) {
                throw new Error(`Listings API returned ${response.status}`);
            }

            const payload = await response.json();
            const dataListingsWithTags = payload.results ?? [];
            setListings(dataListingsWithTags);
            setLoadError("");

        } catch (error) {
            console.error("Error fetching listings", error.message);
            setLoadError("Unable to load listings right now.");
            return;
        }
    }

    useEffect(() => {
        fetchAllTags();
        fetchListings();
    }, [refreshFlag]);

    const filteredListings = listings.filter((listing) => activeTag === "all" || listing.tags.includes(activeTag));
    

    return <section id="listings" className="py-24 px-4 relative bg-secondary/30">
        <div className="container mx-auto max-w-5xl">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center">
            My <span className="text-primary"> Listings</span>
            </h2>
            <p className="text-muted-foreground max-2-2xl mx-auto mb-12">
                See a kit that you want but isn't here? Feel free to <a href="#contact">contact me </a>
                and I will see if I can source it out for you.
            </p>

            {loadError && (
                <p className="mb-6 text-center text-sm text-red-500">{loadError}</p>
            )}

            <div className="max-w-2xl mx-auto mb-8">
                <input
                    type="search"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Try: in-stock RG kits under $100"
                    className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2
                    focus:ring-primary"
                />

                <p className="mt-2 text-sm text-muted-foreground">
                    Current query: {searchQuery || "No search entered"}
                </p>
            </div>
            

            <div className="flex flex-wrap justify-center gap-4 mb-12">
                {["all", ...tags].map((tag, key) => (
                    <button 
                        key={key} 
                        className={cn("tag",
                            activeTag === tag ? "bg-primary text-primary-foreground" 
                                                        : "bg-secondary rounded-full border-1 text-foreground hover:bd-secondary" 
                        )}
                        onClick={() => setActiveTag(tag)}
                    >
                        {tag}
                    </button>
                ))}
            </div>

            <ListingsContainer listingsToDisplay={filteredListings}
                               isModifiable={isAdminPage}
                               triggerRefresh={triggerRefresh}
            />
        </div>
    </section>
}
