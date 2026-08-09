import { useState } from "react"
import { authenticatedFetch } from "@/lib/authenticated-fetch";
import { Pencil, X } from "lucide-react";

export const EditTagForm = ({ tagName, onTagEdited, onCancel }) => {
    const [formData, setFormData] = useState({
        tagName: tagName,
    });

    const handleUpdate = async (event) => {
        event.preventDefault();
        
        const response = await authenticatedFetch(
            `/api/listings/tags/${encodeURIComponent(tagName)}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: formData.tagName }),
            },
        );
        if (!response.ok) {
            console.error("Error updating tag name", response.status);
            return;
        }

        onTagEdited();
    };

    

    return (
        <form onSubmit={handleUpdate} className="flex items-center gap-1 px-2 rounded-full bg-primary text-primary-foreground">
                <input name="name" 
                       type="text" 
                       placeholder="Tag name" 
                       required
                       style={{ minWidth: `${formData.tagName.length || 1}ch`,
                                maxWidth: '15ch' }}
                       className="tag bg-primary-foreground/15 py-1 text-primary-foreground items-center overflow-x-auto"
                       value={formData.tagName} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, tagName: event.target.value }));
                       }} />
            
            <button className="relative group" type="submit" >
                <Pencil/>
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                                    Confirm edit
                </span>
            </button>
            <button className="relative group" onClick={onCancel}>
                <X className="text-red-400"/>
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                                    Cancel edit
                </span>
            </button>
        </form>
    )
}
