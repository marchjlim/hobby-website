import { useEffect, useState } from "react"
import { supabase } from "../supabase-client";
import { WithContext as ReactTagInput } from 'react-tag-input';
import { useToast } from "@/hooks/use-toast";
import { Trash } from 'lucide-react';

export const ListingForm = ({ onListingCreated }) => {
    const [formData, setFormData] = useState({
        listingName: "",
        listingImg: "",
        listingTags: [],    
    });

    const [allTags, setAllTags] = useState([]);
    const [listingImage, setListingImage] = useState(null);

    const { toast } = useToast();

    const fetchAllTags = async () => {
        const {error, data: tagData } = await supabase.from("ListingTag").select("name");

        if (error) {
            console.error("Error fetching all tags: ", error.message);
            return;
        }
        setAllTags(tagData.map(row => ({ id: row.name, text: row.name })));
    }

    useEffect(() => {
        fetchAllTags();
    }, []);

    const addPredefinedTag = (tag) => {
        // add into tags
        addTag(tag);
    }
    

    const deleteListing = async (id) => {
        const {error} = await supabase.from("Listings").delete().eq("id", id);

        if (error) {
            console.error("Error deleting listing: ", error.message);
            return;
        }
    }

    const updateListing = async (id) => {
        const {error} = await supabase.from("Listings").update({ name: newName}).eq("id", id);

        if (error) {
            console.error("Error updating listing: ", error.message);
            return;
        }
    }

    const handleFileChange = (event) => {
        // store file into a state
        if (event.target.files && event.target.files.length > 0) {
            setListingImage(event.target.files[0]);
        }
    };

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

    const handleSubmit = async (event) => {
        event.preventDefault();

        let imageUrl = null;

        if (listingImage) {
            imageUrl = await uploadImage(listingImage);
        }
        
        // insert into listings
        const { error, data } = await supabase.from("Listings").insert(
                                                               {name: formData.listingName, 
                                                                image_url: imageUrl})
                                                        .select()
                                                        .single();
                                
        if (error) {
            console.error("Error adding listing", error.message);
            return;
        }

        for (const tag of tags) {
            const {error: tagError} = await supabase.from("ListingTag").upsert({ name: tag.text },
                                                             { onConflict: ['name'] }
                                                            )
            if (tagError) {
                console.error("Error adding listing tags", tagError.message);
                return;
            }
            
            const {error: relationError} = await supabase.from("Tagged").insert({ TagName: tag.text, ListingId: data.id });
            if (relationError) {
                console.error("Error adding listing and tag relation", relationError.message);
                return;
            }
        }



        setFormData({
            listingName:"",
            listingImg: "",
            listingTags: [],
        });

        await fetchAllTags();
        await onListingCreated();
    };

    const [tags, setTags] = useState([]);

    const addTag = (tag) => {
        // do not allow adding duplicate if tags already selected.
        if (!tags.some(t => t.text.toLowerCase() === tag.text.toLowerCase())) {
            setTags([...tags, tag]);
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
        setTags(tags.filter((tag, index) => idx !== index));
    }

    const deleteAllTags = () => {
        setTags([]);
    }

    

    return (
        <form onSubmit={handleSubmit} className="flex flex-col bg-card mx-auto px-100">
            <h3 className="text-3xl md:text-4xl font-bold text-center mb-4"> New Listing Details </h3>
            <div className="flex flex-col mb-4 gap-2">
                <span className="text-secondary text-2xl md:text-3xl font-semibold">Listing name</span>
                <input name="name" 
                       type="text" 
                       placeholder="Listing name" 
                       required
                       className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingName} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingName: event.target.value }));
                       }} />
                <span className="text-secondary text-2xl md:text-3xl font-semibold">
                    Choose some existing tags or add your own
                </span>
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Existing tags:
                </span>
                <div className="flex flex-row gap-2 w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    {allTags.map((tag) => (
                        <button className="tag rounded-full border-1" 
                                onClick={() => addPredefinedTag(tag)}>
                                    {tag.text}
                        </button>
                    ))}
                </div>
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Selected tags:
                </span>
                <div className="flex w-full px-2 py-2 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    <ReactTagInput
                        tags={tags}
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
                        {listingImage ? listingImage.name : "Upload Image"}
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="hidden"
                        />
                    </label>
                    <button className="flex flex-row px-3 py-2 font-medium rounded-full bg-primary"
                            onClick={deleteAllTags}> 
                        Delete all tags
                        <Trash />
                    </button>
                </span>
                
            </div>
            
            <button type="submit" className="cosmic-button">Create Listing</button>
        </form>
    )
}