import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast";
import { authenticatedFetch } from "@/lib/authenticated-fetch";
import { ListingsContainer } from "./ListingsContainer";
import { DropdownWithComponent } from "../DropdownWithComponent";

// Admin form to create a tag and also assign that tag to multiple listings
export const TagForm = ({ refreshFlag, onTagCreated }) => {
    const [formData, setFormData] = useState({
        tagName: "",
    });
    const [selectedListingIds, setSelectedListingIds] = useState([]);
    const [listings, setListings] = useState([]);

    const handleListingSelect = (listing) => {
        setSelectedListingIds([...selectedListingIds, listing.id]);
    }

    const handleListingUnselect = (listing) => {
        setSelectedListingIds(selectedListingIds.filter(id => id !== listing.id));
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
        } catch (error) {
            console.error("Error fetching listings", error.message);
        }
    }

    useEffect(() => {
        fetchListings();
    }, [refreshFlag]);

    const { toast } = useToast();

    const handleSubmit = async (event) => {
        event.preventDefault();

        try {
            const tagResponse = await authenticatedFetch("/api/listings/tag", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name: formData.tagName,
                }),
            });

            if (!tagResponse.ok) {
                throw new Error(`Listings/tag API returned ${tagResponse.status}`);
            }

            if (selectedListingIds.length > 0) {
                const relationshipResponse = await authenticatedFetch("/api/listings/tags/attach", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        tag_name: formData.tagName,
                        listing_ids: selectedListingIds,
                    }),
                });

                if (!relationshipResponse.ok) {
                    throw new Error(
                        `Unable to attach tag to listings: ${relationshipResponse.status}`
                    );
                }
            }

            setFormData({
                tagName: "",
            });
            setSelectedListingIds([]);

            await onTagCreated();

            toast({
                title: "Tag created",
                description: "Your tag has been successfully created",
            });
        } catch (error) {
            console.error("Error creating tag", error.message);
            toast({
                title: "Unable to create tag",
                description: error.message,
                variant: "destructive",
            });
        }
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
                        setFormData({tagName: event.target.value });
                    }} />
            </div>
            <DropdownWithComponent
                title="Select listings to tag"
                content={
                    <ListingsContainer listingsToDisplay={listings}
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