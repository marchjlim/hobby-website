import { useState } from "react"
import { supabase } from "../supabase-client";
import { WithContext as ReactTagInput } from 'react-tag-input';
import { useToast } from "@/hooks/use-toast";
import { Trash, X } from 'lucide-react';

export const EditListingForm = ({ listing, initialListingTags, onListingEdited, onCancel }) => {
    // convert each tag to the structure of ReactTagInput
    let formattedInitialListingTags = initialListingTags.map(tag => ({ id: tag, text: tag }));
    const [formData, setFormData] = useState({
        listingName: listing.name,
        listingImg: listing.image_url,
        listingTags: formattedInitialListingTags,
    });

    // formData should maintain list of all tags that the user wants to have in the updated listing
    // backend should maintain list of tags that user wants to remove, and tags that user wants to add

    const [allTags, setAllTags] = useState(formattedInitialListingTags);
    const [updatedListingImage, setUpdatedListingImage] = useState(null);

    const { toast } = useToast();

    const handleFileChange = (event) => {
        // store file into a state
        if (event.target.files && event.target.files.length > 0) {
            setUpdatedListingImage(event.target.files[0]);
        }
    };

    // update image?
    const uploadImage = async (file) => {
        const filePath = `${file.name}-${Date.now()}`; 
        const {error} = await supabase.storage.from("listing-images").upload(filePath, file);

        if (error) {
            console.error("Error uploading image: ", error.message);
            return null;
        }

        const {data} = await supabase.storage.from("listing-images").getPublicUrl(filePath);

        return data.publicUrl;
    }

    const handleUpdate = async (event) => {
        event.preventDefault();

        let updatedImageUrl = null;

        if (updatedListingImage) {
            updatedImageUrl = await uploadImage(updatedListingImage);
        }
        
        // update listing table
        const { error } = await supabase.from("Listings")
                                        .update({ name: formData.listingName, 
                                                  image_url: updatedImageUrl ? updatedImageUrl
                                                                             : formData.listingImg })
                                        .eq("id", listing.id);

                                
        if (error) {
            console.error("Error updating listing", error.message);
            return;
        }

        for (const tag of allTags) {
            // insert new listing tag, if any
            const {error: tagError} = await supabase.from("ListingTag").upsert({ name: tag.text },
                                                             { onConflict: ['name'] }
                                                            )
            if (tagError) {
                console.error("Error adding listing tags", tagError.message);
                return;
            }
            
            const {error: relationError} = await supabase.from("Tagged").upsert({ TagName: tag.text, ListingId: listing.id });
            if (relationError) {
                console.error("Error adding listing and tag relation", relationError.message);
                return;
            }
        }

        // delete relations for tags that have been removed
        let lowerCaseTags = allTags.map(tag => tag.text.toLowerCase());
        // removed tags are ones that contained in initialListingTags but not in allTags
        let removedTags = initialListingTags.filter(tag => !lowerCaseTags.includes(tag.toLowerCase()));
        for (const removedTag of removedTags) {
            const {error: removeRelationError} = await supabase.from("Tagged").delete()
                                                                              .eq("ListingId", listing.id)
                                                                              .eq("TagName", removedTag);
            
            if (removeRelationError) {
                console.error("Error removing listing and tag relation", removeRelationError.message);
            }
        }

        onListingEdited();
    };

    const addTag = (tag) => {
        // do not allow adding duplicate if tags already selected.
        if (!allTags.some(t => t.text.toLowerCase() === tag.text.toLowerCase())) {
            setAllTags([...allTags, tag]);
        } else {
            // duplicate tag
            setTimeout(() => {
                toast({
                    title: "Duplicate tag detected",
                    description: "Please ensure all tags for a listing are unique",
                })
            }, 1000);
        }
    }

    const deleteTag = (idx) => {
        setAllTags(allTags.filter((tag, index) => idx !== index));
    }

    const deleteAllTags = () => {
        setAllTags([]);
    }

    

    return (
        <form onSubmit={handleUpdate} className="flex flex-col w-full space-y-4">
            <div className="flex flex-col mb-4 gap-2">
                <div className="relative w-full text-center">
                    <div className="text-secondary text-xl font-semibold">Listing name</div>
                    <button className="absolute top-0 right-0 group" onClick={onCancel}>
                        <X className="text-red-400"/>
                        <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                        bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                                            Cancel edit
                        </span>
                    </button>
                </div>
                
                <input name="name" 
                       type="text" 
                       placeholder="Listing name" 
                       required
                       className="w-full px-3 py-1 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingName} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingName: event.target.value }));
                       }} />
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Listing tags:
                </span>
                <div className="flex flex-row gap-2 w-full px-4 py-3 overflow-x-auto rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    {allTags.map((tag) => (
                        <span className="tag rounded-full border-1">
                            {tag.text}
                        </span>
                    ))}
                </div>
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Add new tag:
                </span>
                <div className="flex w-full px-2 py-2 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    <ReactTagInput
                        tags={allTags}
                        handleDelete={deleteTag}
                        handleAddition={addTag}
                        inputFieldPosition="bottom"
                        placeholder="Create new tag"
                        classNames={{
                            tag: 'border-1 rounded-full px-1 mr-2',
                            tagInputField: 'w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary',
                            tagInput: 'py-2',
                            remove: 'px-1'
                        }}
                    />
                </div>
                
                <span className="flex justify-between gap-2">
                    <label className="cosmic-button">
                        {updatedListingImage ? updatedListingImage.name : "Upload New Image"}
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="hidden"
                        />
                    </label>
                    <button type="button" className="flex flex-row px-3 py-2 font-medium rounded-full bg-primary"
                            onClick={deleteAllTags}> 
                        Delete all tags
                        <Trash />
                    </button>
                </span>
                
            </div>
            
            <button type="submit" className="cosmic-button">Update Listing</button>
        </form>
    )
}