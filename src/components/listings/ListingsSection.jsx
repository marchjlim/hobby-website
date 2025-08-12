import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { supabase } from "../../supabase-client";
import { useLocation } from "react-router-dom";
import { ListingsContainer } from "./ListingsContainer";


export const ListingsSection = ({ refreshFlag, triggerRefresh }) => {
    const [activeTag, setActiveTag] = useState("all");

    const [listings, setListings] = useState([]);
    const [tagMap, setTagMap] = useState({});
    const [tags, setTags] = useState([]);

    const location = useLocation();
    const isAdminPage = location.pathname === "/secret-admin-page";

    const fetchAllTags = async () => {
        const {error, data: tagData } = await supabase.from("ListingTag").select("name");

        if (error) {
            console.error("Error fetching all tags: ", error.message);
            return;
        }
        setTags(tagData.map(row => row.name));
    }

    const fetchListings = async () => {
        const { error, data: dataListings } = await supabase.from("Listings").select("*").order("created_at", { ascending : true });

        if (error) {
            console.error("Error fetching listings", error.message);
            return;
        }

        setListings(dataListings);

        // fetch tags
        const tagMapTemp = {};
        for (const listing of dataListings) {
            const { error, data } = await supabase.from("Tagged").select("TagName").eq("ListingId", listing.id);
            
            if (error) {
                console.error("Error fetching tags for listings: ", error.message);
                continue;
        }  
        tagMapTemp[listing.id] = data.map(row => row.TagName);
        }
        setTagMap(tagMapTemp);
    }

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
                    Note: Deals made on Telegram are cheaper. See <a href="#faq" className="text-primary">FAQ</a> for more info.
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
                               tagMap={tagMap} 
                               isModifiable={isAdminPage}
                               triggerRefresh={triggerRefresh}
            />
        </div>
    </section>
}