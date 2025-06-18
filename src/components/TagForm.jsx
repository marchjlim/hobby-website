import { useState, useEffect } from "react"
import { supabase } from "../supabase-client";
import { useToast } from "@/hooks/use-toast";
import { ListingsContainer } from "./ListingsContainer";
import { ExpandableButton } from "./ExpandableButton";
import { DropdownWithComponent } from "./DropdownWithComponent";

export const TagForm = ({ refreshFlag, onTagCreated }) => {
    const [formData, setFormData] = useState({
        tagName: "",
    });
    const [selectedListingIds, setSelectedListingIds] = useState([]);

    const handleListingSelect = (listing) => {
        setSelectedListingIds([...selectedListingIds, listing.id]);
    }

    const handleListingUnselect = (listing) => {
        setSelectedListingIds(selectedListingIds.filter(id => id !== listing.id));
    }

    
    const [listings, setListings] = useState([]);
    const [tagMap, setTagMap] = useState({});
    const [tags, setTags] = useState([]);

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

    const { toast } = useToast();

    const handleSubmit = async (event) => {
        event.preventDefault();
        
        const { error } = await supabase.from("ListingTag").upsert({ name: formData.tagName });
                                
        if (error) {
            console.error("Error adding tag", error.message);
            return;
        }

        for (const listingId of selectedListingIds) {
            const { error } = await supabase.from("Tagged")
                                            .upsert({ ListingId: listingId, TagName: formData.tagName });
            
            if (error) {
                console.error("Error adding tag relation", error.message);
                return;
            }
        }



        setFormData({
            tagName:"",
        });
        setSelectedListingIds([]);

        await onTagCreated();

        toast({
                    title: "Tag created",
                    description: "Your tag has been successfully created",
                });
    };

    return <>
    <div className="flex flex-col mx-auto">
        <form onSubmit={handleSubmit} className="px-100">
            <h3 className="text-3xl md:text-4xl font-bold text-center mb-4"> Create New Tag </h3>
            <div className="flex flex-col mb-4 gap-2">
                <input name="name" 
                    type="text" 
                    placeholder="Tag name" 
                    required
                    className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                    value={formData.tagName} 
                    onChange={(event) => {
                        setFormData((prev) => ({tagName: event.target.value }));
                    }} />
            </div>

            <DropdownWithComponent
                title="Select listings to tag"
                content={
                    <ListingsContainer listingsToDisplay={listings} 
                                    tagMap={tagMap} 
                                    isModifiable={false}
                                    triggerRefresh={onTagCreated}        
                                    hasSelectableListings={true}
                                    onListingSelect={handleListingSelect}
                                    onListingUnselect={handleListingUnselect}
                                    selectedListingIds={selectedListingIds}
                    />
                }
            />
            
            <button type="submit" className="cosmic-button mt-4">Create Tag</button>
        </form>
        
        


        
    </div>
            

            
            </>
}