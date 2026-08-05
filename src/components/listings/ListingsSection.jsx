import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useLocation } from "react-router-dom";
import { ListingsContainer } from "./ListingsContainer";


export const ListingsSection = ({ refreshFlag, triggerRefresh }) => {
    const [activeTag, setActiveTag] = useState("all");
    const [loadError, setLoadError] = useState("");

    const [listings, setListings] = useState([]);
    const [tagMap, setTagMap] = useState({});
    const [tags, setTags] = useState([]);

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
            setTags(tagsData.map((row) => row.name));
        } catch (error) {
            console.error("Error fetching all tags:", error.message);
        }
    };

    const fetchListings = async () => {
        try {
            const response = await fetch("/api/listings/withtags");

            if (!response.ok) {
                throw new Error(`Listings API returned ${response.status}`);
            }

            const payload = await response.json();
            const dataListings = payload.results ?? [];
            const nextTagMap = {};

            for (const listing of dataListings) {
                nextTagMap[listing.id] = listing.tags ?? [];
            }

            setListings(dataListings);
            setTagMap(nextTagMap);
            setLoadError("");
        } catch (error) {
            console.error("Error fetching listings", error.message);
            setLoadError("Unable to load listings right now.");
        }
    };

    useEffect(() => {
        fetchAllTags();
        fetchListings();
    }, [refreshFlag]);

    const filteredListings = listings.filter((listing) => activeTag === "all" || (tagMap[listing.id] || []).includes(activeTag));
    

    return <section id="listings" className="py-24 px-4 relative bg-secondary/30">
        <div className="container mx-auto max-w-5xl">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center">
            My <span className="text-primary"> Listings</span>
            </h2>
            <div className="text-muted-foreground max-2-2xl mx-auto mb-12">
                <p>
                See a kit that you want but isn't here? Feel free to <a href="#contact" className="text-primary">contact me </a>
                and I will see if I can source it out for you.
                </p>
                <p>
                    Browse through my collection of Gundam kits and accessories. 
                    Click on the tags to filter the listings.
                </p>
                <p>
                    Meetups are available near Lorong Chuan MRT station.
                </p>
                <p>
                    Note: Deals made on Telegram are cheaper. See <a href="#faq" className="text-primary">FAQ</a> for more info.
                </p>
            </div>

            {loadError && (
                <p className="mb-6 text-center text-sm text-red-500">{loadError}</p>
            )}
            
            

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
                               tagMap={tagMap} 
                               isModifiable={isAdminPage}
                               triggerRefresh={triggerRefresh}
            />
        </div>
    </section>
}
