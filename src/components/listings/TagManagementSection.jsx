import { useState, useEffect } from "react";
import { supabase } from "../../supabase-client";
import { TagManagementCard } from "./TagManagementCard";

export const TagManagementSection = ({ refreshFlag, onTagUpdate }) => {
    const [tags, setTags] = useState([]);

    const fetchAllTags = async () => {
        const { error, data: tagData } = await supabase.from("ListingTag").select("name");

        if (error) {
            console.error("Error fetching all tags: ", error.message);
            return;
        }
        setTags(tagData.map(row => row.name));
    }

    useEffect(() => {
        fetchAllTags();
    }, [refreshFlag]);

    return <section id="tags" className="py-24 px-4 relative bg-secondary/30">
        <div className="container mx-auto max-w-5xl">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center">
            Listing <span className="text-primary"> Tags</span>
            </h2>

            <h1 className="text-1xl md:text-2xl font-semibold mb-4 text-center">
                Edit or remove existing tags
            </h1>
            <div className="flex flex-wrap justify-center gap-2 mb-12">
                {tags.map((tag, key) => (
                    <TagManagementCard key={key} tag={tag} onTagUpdate={onTagUpdate} />
                ))}
            </div>
        </div>
    </section>
}