import { useEffect, useState } from "react"
import { supabase } from "../supabase-client";
import { WithContext as ReactTagInput } from 'react-tag-input';

export const ListingForm = () => {
    const [formData, setFormData] = useState({
        listingName: "",
        listingImg: "",
        listingTags: [],
    });

    const [listingImage, setListingImage] = useState(null);

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
    };

    const [tags, setTags] = useState([]);

    const addTag = (tag) => {
        setTags([...tags, tag]);
    }

    const deleteTag = (idx) => {
        setTags(tags.filter((tag, index) => idx !== index));
    }

    

    return (
        <form onSubmit={handleSubmit} className="flex flex-col bg-card mx-auto px-100">
            <h3 className="text-3xl md:text-4xl font-bold text-center mb-4"> New Listing Details </h3>
            <div className="flex flex-col mb-4 gap-2">
                <span className="text-secondary text-2xl md:text-3xl">Listing name</span>
                <input name="name" 
                       type="text" 
                       placeholder="Listing name" 
                       className="border-1 bg-secondary rounded"
                       value={formData.listingName} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingName: event.target.value }));
                       }} />
                <ReactTagInput
                    tags={tags}
                    handleDelete={deleteTag}
                    handleAddition={addTag}
                    inputFieldPosition="bottom"
                    placeholder="Enter tags for listing"
                />
                <input type="file" accept="image/*" onChange={handleFileChange} className="cosmic-button"/>
            </div>
            
            <button type="submit" className="cosmic-button">Create Listing</button>
        </form>
    )
}