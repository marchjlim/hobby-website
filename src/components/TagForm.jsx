import { useState } from "react"
import { supabase } from "../supabase-client";
import { useToast } from "@/hooks/use-toast";

export const TagForm = ({ onTagCreated }) => {
    // listings to add the tag to?
    const [formData, setFormData] = useState({
        tagName: "",
    });

    const { toast } = useToast();

    const handleSubmit = async (event) => {
        event.preventDefault();
        
        const { error } = await supabase.from("ListingTag").upsert({ name: formData.tagName });
                                
        if (error) {
            console.error("Error adding tag", error.message);
            return;
        }



        setFormData({
            tagName:"",
        });

        await onTagCreated();

        toast({
                    title: "Tag created",
                    description: "Your tag has been successfully created",
                });
    };

    return (
        <form onSubmit={handleSubmit} className="flex flex-col bg-card mx-auto px-100">
            <h3 className="text-3xl md:text-4xl font-bold text-center mb-4"> Create New Tag </h3>
            <div className="flex flex-col mb-4 gap-2">
                <span className="text-secondary text-2xl md:text-3xl font-semibold">Tag name</span>
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
            
            <button type="submit" className="cosmic-button">Create Tag</button>
        </form>
    )
}